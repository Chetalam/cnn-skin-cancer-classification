"""SQLite persistence. No plaintext passwords, uploaded originals or synthetic predictions."""
import csv
import hashlib
import hmac
import io
import json
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
import unicodedata
from contextlib import contextmanager
ITERATIONS = 600_000
SESSION_SECONDS = 8 * 60 * 60
DB_PATH = Path(os.environ.get('SKIN_APP_DB', str(Path(__file__).parent / 'storage' / 'application.db')))
SCHEMA = '''
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, email TEXT NOT NULL COLLATE NOCASE UNIQUE,
 full_name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('system_administrator','healthcare_worker')),
 password_hash TEXT NOT NULL, created_at INTEGER NOT NULL,
 healthcare_center TEXT NOT NULL DEFAULT '',
 account_group_id INTEGER REFERENCES users(id),
 account_status TEXT NOT NULL DEFAULT 'active' CHECK(account_status IN ('pending','active','rejected','suspended','deactivated')),
 center_key TEXT NOT NULL DEFAULT '',
 deactivated_at INTEGER, updated_at INTEGER
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS login_attempts (
 email TEXT PRIMARY KEY COLLATE NOCASE, failures INTEGER NOT NULL DEFAULT 0,
 blocked_until INTEGER NOT NULL DEFAULT 0, last_attempt INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS cancer_classes (code TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS model_versions (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, artifact_path TEXT NOT NULL,
 class_order TEXT NOT NULL, preprocessing TEXT NOT NULL, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS skin_lesion_images (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 request_key TEXT NOT NULL UNIQUE, case_reference TEXT NOT NULL,
 file_name TEXT NOT NULL, image_sha256 TEXT NOT NULL,
 width INTEGER NOT NULL CHECK(width>0), height INTEGER NOT NULL CHECK(height>0),
 thumbnail BLOB NOT NULL, uploaded_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS prediction_results (
 id INTEGER PRIMARY KEY, image_id INTEGER NOT NULL UNIQUE REFERENCES skin_lesion_images(id) ON DELETE CASCADE,
 status TEXT NOT NULL CHECK(status IN ('awaiting_model','predicted')),
 cancer_class TEXT REFERENCES cancer_classes(code), confidence REAL,
 model_id INTEGER REFERENCES model_versions(id), created_at INTEGER NOT NULL,
 CHECK((status='awaiting_model' AND cancer_class IS NULL AND confidence IS NULL AND model_id IS NULL)
 OR (status='predicted' AND cancer_class IS NOT NULL AND model_id IS NOT NULL
 AND confidence IS NOT NULL AND confidence>=0 AND confidence<=1))
);
CREATE TABLE IF NOT EXISTS prediction_scores (
 prediction_id INTEGER NOT NULL REFERENCES prediction_results(id) ON DELETE CASCADE,
 cancer_class TEXT NOT NULL REFERENCES cancer_classes(code),
 score REAL NOT NULL CHECK(score>=0 AND score<=1), PRIMARY KEY(prediction_id,cancer_class)
);
CREATE TABLE IF NOT EXISTS audit_events (
 id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
 action TEXT NOT NULL, occurred_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS dataset_imports (
 id INTEGER PRIMARY KEY, imported_by INTEGER NOT NULL REFERENCES users(id),
 file_sha256 TEXT NOT NULL, imported_at INTEGER NOT NULL, record_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS dataset_images (
 id INTEGER PRIMARY KEY, import_id INTEGER NOT NULL REFERENCES dataset_imports(id),
 dataset TEXT NOT NULL CHECK(dataset IN ('HAM10000','PAD-UFES-20')),
 image_id TEXT NOT NULL, lesion_id TEXT, patient_id TEXT,
 class_label TEXT NOT NULL REFERENCES cancer_classes(code), age REAL CHECK(age IS NULL OR age>=0),
 sex TEXT CHECK(sex IS NULL OR sex IN ('female','male')),
 localization TEXT, image_path TEXT NOT NULL, image_hash TEXT NOT NULL UNIQUE,
 fitzpatrick REAL CHECK(fitzpatrick IS NULL OR (fitzpatrick>=1 AND fitzpatrick<=6)),
 biopsy_confirmed INTEGER CHECK(biopsy_confirmed IS NULL OR biopsy_confirmed IN (0,1)),
 diagnosis_method TEXT,
 UNIQUE(dataset,image_id)
);
CREATE INDEX IF NOT EXISTS idx_upload_owner ON skin_lesion_images(user_id,uploaded_at);
CREATE INDEX IF NOT EXISTS idx_dataset_class ON dataset_images(class_label);
CREATE INDEX IF NOT EXISTS idx_session_user ON sessions(user_id);
'''
@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA busy_timeout=20000')
    try:
        with conn:
            yield conn
    finally:
        conn.close()
def initialize():
    with connect() as conn:
        conn.executescript(SCHEMA)
    with connect() as conn:
        if not conn.execute('SELECT 1 FROM schema_version WHERE version=6').fetchone():
            backup_path = DB_PATH.with_name(DB_PATH.stem + f'.before_profile_update_{time.time_ns()}.db')
            with sqlite3.connect(backup_path) as backup:
                conn.backup(backup)
            conn.execute('PRAGMA foreign_keys=OFF')
            try:
                conn.execute('BEGIN IMMEDIATE')
                if not conn.execute('SELECT 1 FROM schema_version WHERE version=6').fetchone():
                    columns = {row['name'] for row in conn.execute('PRAGMA table_info(users)')}
                    supported = {'id','email','full_name','role','password_hash','created_at',
                                 'healthcare_center','account_group_id','account_status','center_key',
                                 'approved_at','approved_by','deactivated_at','updated_at'}
                    if columns - supported:
                        raise ValueError('Unexpected user columns; migration stopped to protect data.')
                    custom = conn.execute("SELECT type,name,sql FROM sqlite_master WHERE tbl_name='users' AND type IN ('index','trigger') AND sql IS NOT NULL").fetchall()
                    if any('approved_at' in row['sql'].lower() or 'approved_by' in row['sql'].lower() for row in custom):
                        raise ValueError('A custom index/trigger uses approval fields; inspect it before migrating.')
                    table_sql = SCHEMA.split('CREATE TABLE IF NOT EXISTS users (',1)[1].split(');',1)[0]
                    conn.execute('CREATE TABLE users_profile_migration (' + table_sql + ')')
                    for original in conn.execute('SELECT * FROM users').fetchall():
                        row = dict(original)
                        role = 'system_administrator' if row['role']=='maintainer' else row['role']
                        status = row.get('account_status','active')
                        conn.execute('INSERT INTO users_profile_migration(id,email,full_name,role,password_hash,created_at,healthcare_center,account_group_id,account_status,center_key,deactivated_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                            (row['id'],row['email'],row['full_name'],role,row['password_hash'],row['created_at'],
                             row.get('healthcare_center',''),row.get('account_group_id') or row['id'],status,
                             center_key(row.get('healthcare_center','')),row.get('deactivated_at'),row.get('updated_at')))
                    conn.execute('DROP TABLE users')
                    conn.execute('ALTER TABLE users_profile_migration RENAME TO users')
                    for item in custom:
                        conn.execute(item['sql'])
                    conn.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE account_status<>'active')")
                    if conn.execute('PRAGMA foreign_key_check').fetchall():
                        raise ValueError('Migration relationship checks failed; changes rolled back.')
                    conn.execute('INSERT INTO schema_version VALUES (6,?)',(int(time.time()),))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.execute('PRAGMA foreign_keys=ON')
        conn.executemany('INSERT OR IGNORE INTO cancer_classes VALUES (?,?)', [
            ('Melanoma','Melanoma'),('BCC','Basal Cell Carcinoma'),('SCC','Squamous Cell Carcinoma')])


def normalize_email(email):
    value = email.strip().lower()
    if len(value)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
        raise ValueError('Enter a valid email address.')
    return value
def validate_password(password):
    if not 12 <= len(password) <= 128:
        raise ValueError('Use a password or passphrase with 12–128 characters.')
def validate_profile(name, healthcare_center):
    name = (name or '').strip()
    healthcare_center = (healthcare_center or '').strip()
    if not 2 <= len(name) <= 100:
        raise ValueError('Enter a name with 2–100 characters.')
    if not 2 <= len(healthcare_center) <= 150:
        raise ValueError('Enter a healthcare centre name with 2–150 characters.')
    return name, healthcare_center
def center_key(value):
    return ' '.join(unicodedata.normalize('NFKC', value or '').casefold().split())
def require_active_user(conn, user_id):
    user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    if not user or user['account_status'] != 'active':
        raise ValueError('This account is not active. Contact your healthcare centre administrator.')
    return user
def check_separate_role_password(conn, group_id, role, password, excluded_user_id=None):
    if group_id is None:
        return
    accounts = conn.execute(
        'SELECT id,password_hash FROM users WHERE account_group_id=? AND role<>?',
        (group_id, role)
    ).fetchall()
    for account in accounts:
        if account['id'] != excluded_user_id and verify_password(password, account['password_hash']):
            raise ValueError('Your administrator and healthcare-worker accounts must use different passwords.')
def password_hash(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'
def verify_password(password, encoded):
    try:
        algorithm, iterations, salt, expected = encoded.split('$')
        if algorithm != 'pbkdf2_sha256':
            return False
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False
def audit(conn, user_id, action):
    conn.execute('INSERT INTO audit_events(user_id,action,occurred_at) VALUES (?,?,?)',
                 (user_id, action, int(time.time())))
def register(name, email, password, healthcare_center=None,
             linked_administrator_email=None, linked_administrator_password=None,
             requested_role='healthcare_worker',
             linked_account_email=None, linked_account_password=None):
    email = normalize_email(email)
    name, healthcare_center = validate_profile(name, healthcare_center)
    validate_password(password)
    if requested_role not in {'system_administrator','healthcare_worker'}:
        raise ValueError('Choose System Administrator or Healthcare Worker.')
    linked_user = None
    if linked_account_email or linked_account_password:
        if linked_administrator_email or linked_administrator_password:
            raise ValueError('Use only one set of linked-account credentials.')
        if not linked_account_email or not linked_account_password:
            raise ValueError('Enter both the existing account email and its current password.')
        token = sign_in(linked_account_email, linked_account_password)
        try:
            linked_user = session_user(token)
            if not linked_user or linked_user['role'] == requested_role:
                raise ValueError('Link your existing account for the other role.')
        finally:
            sign_out(token)
    if linked_administrator_email or linked_administrator_password:
        if requested_role != 'healthcare_worker':
            raise ValueError('Administrator credentials can link a new healthcare-worker account only.')
        if not linked_administrator_email or not linked_administrator_password:
            raise ValueError('Enter both the administrator email and its current password to link your accounts.')
        # Reuse sign-in throttling rather than create an unthrottled password-check route.
        token = sign_in(linked_administrator_email, linked_administrator_password)
        try:
            linked_user = session_user(token)
            if not linked_user or linked_user['role'] != 'system_administrator':
                raise ValueError('The linked account must be your system-administrator account.')
        finally:
            sign_out(token)
    encoded = password_hash(password)
    try:
        with connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            role = requested_role
            group_id = None
            if linked_user:
                existing = require_active_user(conn, linked_user['id'])
                if existing['role'] == role:
                    raise ValueError('Use an existing account for the other role.')
                if email == existing['email']:
                    raise ValueError('Use a different email for your second-role account.')
                group_id = existing['account_group_id'] or existing['id']
                check_separate_role_password(conn, group_id, role, password)
            cursor = conn.execute('INSERT INTO users(email,full_name,role,password_hash,created_at,healthcare_center,account_group_id,account_status,center_key) VALUES (?,?,?,?,?,?,?,?,?)',
                                  (email, name, role, encoded, int(time.time()), healthcare_center, group_id, 'active', center_key(healthcare_center)))
            if group_id is None:
                conn.execute('UPDATE users SET account_group_id=? WHERE id=?',
                             (cursor.lastrowid, cursor.lastrowid))
            audit(conn, cursor.lastrowid, 'registered_active')
            return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError('Registration could not be completed. Try signing in or use another email.') from exc

def sign_in(email, password):
    email = normalize_email(email)
    if len(password)>128:
        raise ValueError('Email or password is incorrect.')
    now = int(time.time())
    token = None
    status_error = None
    with connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        attempt = conn.execute('SELECT * FROM login_attempts WHERE email=?', (email,)).fetchone()
        if attempt and attempt['blocked_until'] > now:
            raise ValueError('Too many failed attempts. Try again in 15 minutes.')
        user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        # Apply the same work factor for unknown accounts.
        encoded = user['password_hash'] if user else f'pbkdf2_sha256${ITERATIONS}$' + '00'*16 + '$' + '00'*32
        valid = verify_password(password, encoded)
        if user and valid:
            conn.execute('DELETE FROM login_attempts WHERE email=?', (email,))
            if user['account_status'] != 'active':
                status_error = {
                    'pending':'This legacy account is inactive. Contact your healthcare centre administrator.',
                    'rejected':'This legacy account is inactive. Contact your healthcare centre administrator.',
                    'suspended':'Your account is suspended. Contact your centre administrator.',
                    'deactivated':'Your profile is deactivated. Contact your centre administrator to reactivate it.'
                }.get(user['account_status'],'This account is not active. Contact your healthcare centre administrator.')
            else:
                conn.execute('DELETE FROM sessions WHERE expires_at<=?', (now,))
                token = secrets.token_urlsafe(32)
                conn.execute('INSERT INTO sessions VALUES (?,?,?)',
                             (hashlib.sha256(token.encode()).hexdigest(), user['id'], now+SESSION_SECONDS))
                audit(conn, user['id'], 'signed_in')
        else:
            failures = (attempt['failures'] if attempt and now-attempt['last_attempt']<900 else 0) + 1
            conn.execute('INSERT INTO login_attempts VALUES (?,?,?,?) ON CONFLICT(email) DO UPDATE SET failures=excluded.failures,blocked_until=excluded.blocked_until,last_attempt=excluded.last_attempt',
                         (email, failures, now+900 if failures>=5 else 0, now))
    if status_error:
        raise ValueError(status_error)
    if token is None:
        raise ValueError('Email or password is incorrect.')
    return token
def session_user(token):
    if not token:
        return None
    with connect() as conn:
        row = conn.execute("SELECT u.id,u.email,u.full_name,u.role,u.created_at,u.healthcare_center,u.account_group_id,u.account_status FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>? AND u.account_status='active'",
                           (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
        return dict(row) if row else None
def sign_out(token):
    with connect() as conn:
        row = conn.execute('SELECT user_id FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        conn.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
        if row:
            audit(conn, row['user_id'], 'signed_out')
def change_password(user_id, current, new):
    validate_password(new)
    with connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        require_active_user(conn,user_id)
        user = conn.execute('SELECT password_hash,role,account_group_id FROM users WHERE id=?', (user_id,)).fetchone()
        if not user or not verify_password(current, user['password_hash']):
            raise ValueError('The current password is incorrect.')
        if verify_password(new, user['password_hash']):
            raise ValueError('Choose a password different from the current password.')
        check_separate_role_password(conn, user['account_group_id'], user['role'], new, user_id)
        conn.execute('UPDATE users SET password_hash=? WHERE id=?', (password_hash(new), user_id))
        conn.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))
        audit(conn, user_id, 'password_changed')
def update_name(user_id, name):
    name = name.strip()
    if not 2 <= len(name) <= 100:
        raise ValueError('Enter a name with 2–100 characters.')
    with connect() as conn:
        require_active_user(conn,user_id)
        conn.execute('UPDATE users SET full_name=? WHERE id=?', (name, user_id))
        audit(conn, user_id, 'profile_updated')
def update_profile(user_id, name, healthcare_center):
    name, healthcare_center = validate_profile(name, healthcare_center)
    with connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        current = require_active_user(conn,user_id)
        changed_centre = bool(current['center_key']) and current['center_key'] != center_key(healthcare_center)
        if changed_centre and current['role']=='system_administrator':
            raise ValueError('An administrator centre change requires host-level authorisation. Your centre cannot be changed here.')
        cursor = conn.execute(
            'UPDATE users SET full_name=?,healthcare_center=?,center_key=? WHERE id=?',
            (name, healthcare_center, center_key(healthcare_center), user_id)
        )
        if not cursor.rowcount:
            raise ValueError('Account unavailable.')
        audit(conn, user_id, 'profile_updated')
        if changed_centre:
            audit(conn,user_id,'centre_changed_self_declared')
def profile_complete(user):
    return bool(user and (user.get('healthcare_center') or '').strip())
def save_review(user_id, request_key, case_reference, file_name, image, raw_digest):
    thumb = image.copy()
    thumb.thumbnail((320,320))
    out = io.BytesIO()
    thumb.save(out, format='PNG')
    now = int(time.time())
    with connect() as conn:
        require_healthcare_worker(conn,user_id)
        existing = conn.execute('SELECT id,user_id FROM skin_lesion_images WHERE request_key=?', (request_key,)).fetchone()
        if existing:
            if existing['user_id'] != user_id:
                raise ValueError('Record unavailable.')
            return existing['id']
        cursor = conn.execute('INSERT INTO skin_lesion_images(user_id,request_key,case_reference,file_name,image_sha256,width,height,thumbnail,uploaded_at) VALUES (?,?,?,?,?,?,?,?,?)',
            (user_id,request_key,case_reference.strip()[:80],file_name.replace('\\\\','/').split('/')[-1][:200],raw_digest,image.width,image.height,out.getvalue(),now))
        image_id = cursor.lastrowid
        conn.execute("INSERT INTO prediction_results(image_id,status,created_at) VALUES (?,'awaiting_model',?)", (image_id,now))
        audit(conn,user_id,'image_review_saved')
        return image_id
def history(user_id):
    with connect() as conn:
        require_healthcare_worker(conn,user_id)
        return [dict(r) for r in conn.execute('SELECT i.id,i.case_reference,i.file_name,i.width,i.height,i.uploaded_at,p.status,p.cancer_class,p.confidence FROM skin_lesion_images i JOIN prediction_results p ON p.image_id=i.id WHERE i.user_id=? ORDER BY i.uploaded_at DESC,i.id DESC', (user_id,))]
def get_thumbnail(user_id, image_id):
    with connect() as conn:
        require_healthcare_worker(conn,user_id)
        row = conn.execute('SELECT thumbnail FROM skin_lesion_images WHERE user_id=? AND id=?', (user_id,image_id)).fetchone()
        return row['thumbnail'] if row else None
def delete_review(user_id, image_id):
    with connect() as conn:
        require_healthcare_worker(conn,user_id)
        cursor = conn.execute('DELETE FROM skin_lesion_images WHERE id=? AND user_id=?', (image_id,user_id))
        if cursor.rowcount:
            audit(conn,user_id,'image_review_deleted')
        return cursor.rowcount
def require_system_administrator(conn, user_id):
    row = require_active_user(conn,user_id)
    if not row or row['role'] != 'system_administrator':
        raise ValueError('Only active System Administrators can perform this action.')
    if not row['center_key']:
        raise ValueError('Complete your healthcare centre profile first.')
    return row




def list_accounts_for_review(administrator_id):
    with connect() as conn:
        actor = require_system_administrator(conn,administrator_id)
        return [dict(row) for row in conn.execute('SELECT id,email,full_name,role,healthcare_center,account_status,created_at,deactivated_at FROM users WHERE center_key=? ORDER BY created_at DESC,id DESC',
            (actor['center_key'],))]
def review_account(administrator_id, target_user_id, decision):
    if decision not in {'active','suspended'}:
        raise ValueError('Choose restore or suspend.')
    with connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        actor = require_system_administrator(conn, administrator_id)
        target = conn.execute('SELECT * FROM users WHERE id=?',(target_user_id,)).fetchone()
        if not target or target['center_key'] != actor['center_key']:
            raise ValueError('Manage accounts only within your healthcare centre.')
        if target_user_id == administrator_id:
            raise ValueError('Use Account settings to deactivate your own profile.')
        if target['account_status'] == decision:
            raise ValueError('This account already has that status.')
        if decision=='suspended' and target['account_status']!='active':
            raise ValueError('Only an active account can be suspended.')
        conn.execute('UPDATE users SET account_status=?,deactivated_at=NULL,updated_at=? WHERE id=?',
                     (decision,int(time.time()),target_user_id))
        conn.execute('DELETE FROM sessions WHERE user_id=?',(target_user_id,))
        audit(conn,administrator_id,f'account_{decision}:{target_user_id}')

def deactivate_profile(token, password):
    if not token:
        raise ValueError('Sign in again before deactivating your profile.')
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        session = conn.execute('SELECT user_id FROM sessions WHERE token_hash=? AND expires_at>?',
                               (token_hash,int(time.time()))).fetchone()
        if not session:
            raise ValueError('Your session has ended. Sign in again.')
        user = require_active_user(conn,session['user_id'])
        if len(password)>128 or not verify_password(password,user['password_hash']):
            raise ValueError('The current password is incorrect.')
        if user['role']=='system_administrator':
            others = conn.execute("SELECT COUNT(*) FROM users WHERE role='system_administrator' AND account_status='active' AND center_key=? AND id<>?",(user['center_key'],user['id'])).fetchone()[0]
            if not others:
                raise ValueError('Another active administrator at your healthcare centre is required before you can deactivate your profile.')
        now = int(time.time())
        conn.execute("UPDATE users SET account_status='deactivated',deactivated_at=?,updated_at=? WHERE id=?",(now,now,user['id']))
        conn.execute('DELETE FROM sessions WHERE user_id=?',(user['id'],))
        audit(conn,user['id'],'profile_deactivated')

def update_review(user_id, image_id, case_reference):
    value = (case_reference or '').strip()
    if len(value)>80:
        raise ValueError('Case reference must be at most 80 characters.')
    with connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        require_healthcare_worker(conn,user_id)
        result = conn.execute('UPDATE skin_lesion_images SET case_reference=? WHERE id=? AND user_id=?',
                              (value,image_id,user_id))
        if not result.rowcount:
            raise ValueError('Review unavailable.')
        audit(conn,user_id,'image_review_updated')

def import_manifest(user_id, data):
    if len(data)>20*1024*1024:
        raise ValueError('Manifest must be smaller than 20 MB.')
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
    required = {'dataset','image_id','class_label','image_path','image_hash'}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError('Use the clean_metadata.csv exported by notebook 3. Required columns: ' + ', '.join(sorted(required)))
    rows = []
    keys, hashes = set(), set()
    for number,row in enumerate(reader, start=2):
        row = {k:(v or '').strip() for k,v in row.items() if k is not None}
        source, image_id, label, path, digest = (row.get(k,'') for k in ['dataset','image_id','class_label','image_path','image_hash'])
        if source not in {'HAM10000','PAD-UFES-20'} or label not in {'Melanoma','BCC','SCC'} or not image_id or not path or not re.fullmatch('[a-f0-9]{64}',digest):
            raise ValueError(f'Invalid required metadata in CSV row {number}.')
        if (source,image_id) in keys or digest in hashes:
            raise ValueError(f'Duplicate identifier or image hash in CSV row {number}.')
        keys.add((source,image_id)); hashes.add(digest)
        age = float(row['age']) if row.get('age') else None
        if age is not None and (not math.isfinite(age) or age<0):
            raise ValueError(f'Invalid age in CSV row {number}.')
        sex = row.get('sex','').lower() or None
        if sex not in {None,'female','male'}:
            raise ValueError(f'Invalid sex label in CSV row {number}.')
        fitzpatrick = float(row['fitzpatrick']) if row.get('fitzpatrick') else None
        if fitzpatrick is not None and (not math.isfinite(fitzpatrick) or fitzpatrick not in {1,2,3,4,5,6}):
            raise ValueError(f'Invalid Fitzpatrick category in CSV row {number}.')
        biopsy = row.get('biopsy_confirmed','').lower()
        if biopsy not in {'','0','1','0.0','1.0','true','false'}:
            raise ValueError(f'Invalid biopsy flag in CSV row {number}.')
        biopsy = None if not biopsy else int(biopsy in {'1','1.0','true'})
        rows.append((source,image_id,row.get('lesion_id') or None,row.get('patient_id') or None,label,age,sex,row.get('localization') or None,path,digest,fitzpatrick,biopsy,row.get('diagnosis_method') or None))
    if not rows:
        raise ValueError('The manifest contains no records.')
    with connect() as conn:
        require_system_administrator(conn,user_id)
        cursor = conn.execute('INSERT INTO dataset_imports(imported_by,file_sha256,imported_at,record_count) VALUES (?,?,?,?)',
            (user_id,hashlib.sha256(data).hexdigest(),int(time.time()),len(rows)))
        # Replacement is deliberate and atomic; original training SQLite is untouched.
        conn.execute('DELETE FROM dataset_images')
        conn.executemany('INSERT INTO dataset_images(import_id,dataset,image_id,lesion_id,patient_id,class_label,age,sex,localization,image_path,image_hash,fitzpatrick,biopsy_confirmed,diagnosis_method) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            [(cursor.lastrowid,)+row for row in rows])
        audit(conn,user_id,'clean_manifest_imported')
    return len(rows)
def dataset_summary():
    with connect() as conn:
        return [dict(r) for r in conn.execute('SELECT dataset,class_label,COUNT(*) AS image_count FROM dataset_images GROUP BY dataset,class_label ORDER BY dataset,class_label')]
def database_health(user_id):
    with connect() as conn:
        require_system_administrator(conn,user_id)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {'integrity':conn.execute('PRAGMA integrity_check').fetchone()[0],
                'foreign_key_errors':[tuple(r) for r in conn.execute('PRAGMA foreign_key_check')],
                'foreign_keys_enabled':bool(conn.execute('PRAGMA foreign_keys').fetchone()[0]),
                'schema_version':conn.execute('SELECT MAX(version) FROM schema_version').fetchone()[0],
                'counts':{t:conn.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in tables}}


def require_healthcare_worker(conn, user_id):
    user = require_active_user(conn, user_id)
    if user['role'] != 'healthcare_worker':
        raise ValueError('Image reviews are available only through a Healthcare Worker account. Sign in with your separate Healthcare Worker credentials.')
    return user