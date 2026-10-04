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
 full_name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('maintainer','system_administrator','healthcare_worker')),
 password_hash TEXT NOT NULL, created_at INTEGER NOT NULL,
 healthcare_center TEXT NOT NULL DEFAULT '',
 account_group_id INTEGER REFERENCES users(id),
 account_status TEXT NOT NULL DEFAULT 'pending' CHECK(account_status IN ('pending','active','rejected','suspended')),
 center_key TEXT NOT NULL DEFAULT '',
 approved_by INTEGER REFERENCES users(id), approved_at INTEGER
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
CREATE TABLE IF NOT EXISTS administrator_invitations (
 id INTEGER PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE,
 email TEXT NOT NULL COLLATE NOCASE, healthcare_center TEXT NOT NULL, center_key TEXT NOT NULL,
 issued_by INTEGER NOT NULL REFERENCES users(id), created_at INTEGER NOT NULL,
 expires_at INTEGER NOT NULL, used_by INTEGER REFERENCES users(id), used_at INTEGER,
 revoked_at INTEGER
);
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
        columns = {row['name'] for row in conn.execute('PRAGMA table_info(users)')}
        additions = {'healthcare_center','account_group_id','account_status','center_key','approved_by','approved_at'} - columns
        if additions or (not conn.execute('SELECT 1 FROM schema_version WHERE version=4').fetchone() and conn.execute('SELECT 1 FROM users LIMIT 1').fetchone()):
            # SQLite backup includes committed records even when journal files exist.
            backup_path = DB_PATH.with_name(
                DB_PATH.stem + f'.before_approval_update_{time.time_ns()}.db'
            )
            with sqlite3.connect(backup_path) as backup:
                conn.backup(backup)
        conn.execute('BEGIN IMMEDIATE')
        # Recheck inside the write transaction in case another session migrated first.
        columns = {row['name'] for row in conn.execute('PRAGMA table_info(users)')}
        if 'healthcare_center' not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN healthcare_center TEXT NOT NULL DEFAULT ''")
        if 'account_group_id' not in columns:
            conn.execute('ALTER TABLE users ADD COLUMN account_group_id INTEGER REFERENCES users(id)')
        adding_status = 'account_status' not in columns
        if adding_status:
            conn.execute("ALTER TABLE users ADD COLUMN account_status TEXT NOT NULL DEFAULT 'pending' CHECK(account_status IN ('pending','active','rejected','suspended'))")
        if 'center_key' not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN center_key TEXT NOT NULL DEFAULT ''")
        if 'approved_by' not in columns:
            conn.execute('ALTER TABLE users ADD COLUMN approved_by INTEGER REFERENCES users(id)')
        if 'approved_at' not in columns:
            conn.execute('ALTER TABLE users ADD COLUMN approved_at INTEGER')
        if adding_status:
            # Preserve existing active accounts.
            conn.execute("UPDATE users SET account_status='active',approved_at=? WHERE role IN ('maintainer','system_administrator','healthcare_worker')", (int(time.time()),))
            conn.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE account_status<>'active')")
        if not conn.execute('SELECT 1 FROM schema_version WHERE version=4').fetchone():
            # Correct the previous worker-approval policy; retain explicit suspensions/rejections.
            conn.execute("UPDATE users SET account_status='active',approved_by=NULL,approved_at=NULL WHERE role='healthcare_worker' AND account_status='pending'")
        for row in conn.execute("SELECT id,healthcare_center FROM users WHERE center_key=''").fetchall():
            conn.execute('UPDATE users SET center_key=? WHERE id=?', (center_key(row['healthcare_center']),row['id']))
        # Do not guess identity from a person's name or workplace.
        conn.execute('UPDATE users SET account_group_id=id WHERE account_group_id IS NULL')
        conn.execute('INSERT OR IGNORE INTO schema_version VALUES (1,?)', (int(time.time()),))
        conn.execute('INSERT OR IGNORE INTO schema_version VALUES (2,?)', (int(time.time()),))
        conn.execute('INSERT OR IGNORE INTO schema_version VALUES (3,?)', (int(time.time()),))
        conn.execute('INSERT OR IGNORE INTO schema_version VALUES (4,?)', (int(time.time()),))
        conn.executemany('INSERT OR IGNORE INTO cancer_classes VALUES (?,?)', [
            ('Melanoma','Melanoma'), ('BCC','Basal Cell Carcinoma'), ('SCC','Squamous Cell Carcinoma')])

    migrate_administrator_role()


def migrate_administrator_role():
    # Rebuild the users table because its old CHECK constraint forbids the new value.
    with connect() as conn:
        if conn.execute('SELECT 1 FROM schema_version WHERE version=5').fetchone():
            return
        backup_path = DB_PATH.with_name(DB_PATH.stem + f'.before_role_rename_{time.time_ns()}.db')
        with sqlite3.connect(backup_path) as backup:
            conn.backup(backup)
        conn.execute('PRAGMA foreign_keys=OFF')
        try:
            conn.execute('BEGIN IMMEDIATE')
            if conn.execute('SELECT 1 FROM schema_version WHERE version=5').fetchone():
                conn.rollback()
                return
            table_sql = SCHEMA.split('CREATE TABLE IF NOT EXISTS users (',1)[1].split(');',1)[0]
            conn.execute('CREATE TABLE users_role_migration (' + table_sql + ')')
            conn.execute(
                "INSERT INTO users_role_migration "
                "(id,email,full_name,role,password_hash,created_at,healthcare_center,"
                "account_group_id,account_status,center_key,approved_by,approved_at) "
                "SELECT id,email,full_name,CASE WHEN role='maintainer' "
                "THEN 'system_administrator' ELSE role END,password_hash,created_at,"
                "healthcare_center,account_group_id,account_status,center_key,"
                "approved_by,approved_at FROM users"
            )
            conn.execute('DROP TABLE users')
            conn.execute('ALTER TABLE users_role_migration RENAME TO users')
            if conn.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Role migration failed its relationship checks.')
            conn.execute('INSERT INTO schema_version VALUES (5,?)',(int(time.time()),))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.execute('PRAGMA foreign_keys=ON')


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
        raise ValueError('This account is not approved for access.')
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
             requested_role='healthcare_worker', invitation_code=None,
             linked_account_email=None, linked_account_password=None):
    email = normalize_email(email)
    name, healthcare_center = validate_profile(name, healthcare_center)
    validate_password(password)
    if requested_role not in {'system_administrator','healthcare_worker'}:
        raise ValueError('Choose System Administrator or Healthcare Worker.')
    if requested_role == 'system_administrator' and not invitation_code:
        raise ValueError('System Administrator registration requires a valid invitation.')
    if requested_role == 'healthcare_worker' and invitation_code:
        raise ValueError('Administrator invitations are only for administrator registration.')
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
            # Workers are active immediately; invited administrators await approval.
            role = requested_role
            invitation = None
            if role == 'system_administrator':
                code = (invitation_code or '').strip()
                if not code or len(code)>200:
                    raise ValueError('The administrator invitation is invalid or expired.')
                invitation = conn.execute('SELECT * FROM administrator_invitations WHERE token_hash=?',
                    (hashlib.sha256(code.encode()).hexdigest(),)).fetchone()
                if (not invitation or invitation['used_by'] is not None
                    or invitation['revoked_at'] is not None or invitation['expires_at']<=int(time.time())
                    or invitation['email'] != email or invitation['center_key'] != center_key(healthcare_center)):
                    raise ValueError('The administrator invitation is invalid, expired, or does not match your email and centre.')
                issuer = require_system_administrator(conn, invitation['issued_by'])
                if issuer['center_key'] != invitation['center_key']:
                    raise ValueError('The administrator invitation is no longer valid for this centre.')
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
                                  (email, name, role, encoded, int(time.time()), healthcare_center, group_id, 'active' if role == 'healthcare_worker' else 'pending', center_key(healthcare_center)))
            if group_id is None:
                conn.execute('UPDATE users SET account_group_id=? WHERE id=?',
                             (cursor.lastrowid, cursor.lastrowid))
            if invitation:
                consumed = conn.execute('UPDATE administrator_invitations SET used_by=?,used_at=? WHERE id=? AND used_by IS NULL AND revoked_at IS NULL AND expires_at>?',
                    (cursor.lastrowid,int(time.time()),invitation['id'],int(time.time())))
                if consumed.rowcount != 1:
                    raise ValueError('The invitation has already been used or expired.')
            audit(conn, cursor.lastrowid, 'registered_active' if role == 'healthcare_worker' else 'registered_pending')
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
                    'pending':'Your account is awaiting administrator approval.',
                    'rejected':'Your account application was not approved. Contact your centre administrator.',
                    'suspended':'Your account is suspended. Contact your centre administrator.'
                }.get(user['account_status'],'This account is not approved for access.')
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
            raise ValueError('An administrator centre change requires host-level authorisation. Your approved centre cannot be changed here.')
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
        require_active_user(conn,user_id)
        existing = conn.execute('SELECT id,user_id FROM skin_lesion_images WHERE request_key=?', (request_key,)).fetchone()
        if existing:
            if existing['user_id'] != user_id:
                raise ValueError('Record unavailable.')
            return existing['id']
        cursor = conn.execute('INSERT INTO skin_lesion_images(user_id,request_key,case_reference,file_name,image_sha256,width,height,thumbnail,uploaded_at) VALUES (?,?,?,?,?,?,?,?,?)',
            (user_id,request_key,case_reference.strip()[:80],file_name.replace('\\','/').split('/')[-1][:200],raw_digest,image.width,image.height,out.getvalue(),now))
        image_id = cursor.lastrowid
        conn.execute("INSERT INTO prediction_results(image_id,status,created_at) VALUES (?,'awaiting_model',?)", (image_id,now))
        audit(conn,user_id,'image_review_saved')
        return image_id

def history(user_id):
    with connect() as conn:
        require_active_user(conn,user_id)
        return [dict(r) for r in conn.execute('SELECT i.id,i.case_reference,i.file_name,i.width,i.height,i.uploaded_at,p.status,p.cancer_class,p.confidence FROM skin_lesion_images i JOIN prediction_results p ON p.image_id=i.id WHERE i.user_id=? ORDER BY i.uploaded_at DESC,i.id DESC', (user_id,))]

def get_thumbnail(user_id, image_id):
    with connect() as conn:
        require_active_user(conn,user_id)
        row = conn.execute('SELECT thumbnail FROM skin_lesion_images WHERE user_id=? AND id=?', (user_id,image_id)).fetchone()
        return row['thumbnail'] if row else None

def delete_review(user_id, image_id):
    with connect() as conn:
        require_active_user(conn,user_id)
        cursor = conn.execute('DELETE FROM skin_lesion_images WHERE id=? AND user_id=?', (image_id,user_id))
        if cursor.rowcount:
            audit(conn,user_id,'image_review_deleted')
        return cursor.rowcount

def require_system_administrator(conn, user_id):
    row = require_active_user(conn,user_id)
    if not row or row['role'] != 'system_administrator':
        raise ValueError('Only approved System Administrators can perform this action.')
    if not row['center_key']:
        raise ValueError('Complete your healthcare centre profile first.')
    return row

def create_initial_administrator(name, email, password, healthcare_center):
    """Host-only bootstrap helper. Never call from the public registration form."""
    name, healthcare_center = validate_profile(name, healthcare_center)
    email = normalize_email(email)
    validate_password(password)
    encoded = password_hash(password)
    try:
        with connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            if conn.execute("SELECT 1 FROM users WHERE role='system_administrator' AND account_status='active' AND center_key=?", (center_key(healthcare_center),)).fetchone():
                raise ValueError('An active administrator already exists for this centre. Use an administrator invitation instead.')
            now = int(time.time())
            cursor = conn.execute("INSERT INTO users(email,full_name,role,password_hash,created_at,healthcare_center,account_status,center_key,approved_at) VALUES (?,?,'system_administrator',?,?,?,'active',?,?)",
                (email,name,encoded,now,healthcare_center,center_key(healthcare_center),now))
            conn.execute('UPDATE users SET account_group_id=? WHERE id=?',(cursor.lastrowid,cursor.lastrowid))
            audit(conn,cursor.lastrowid,'host_bootstrap_administrator')
            return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError('That email is already registered. Existing accounts were not changed.') from exc

def issue_administrator_invitation(administrator_id, email, healthcare_center, expires_hours=24):
    email = normalize_email(email)
    _, healthcare_center = validate_profile('Invitation',healthcare_center)
    if isinstance(expires_hours,bool) or not isinstance(expires_hours,int) or not 1 <= expires_hours <= 168:
        raise ValueError('Invitation expiry must be between 1 and 168 hours.')
    with connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        actor = require_system_administrator(conn,administrator_id)
        if actor['center_key'] != center_key(healthcare_center):
            raise ValueError('You can invite administrators only for your approved healthcare centre.')
        if conn.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone():
            raise ValueError('Use a new email address for a separate administrator account.')
        now = int(time.time())
        conn.execute('UPDATE administrator_invitations SET revoked_at=? WHERE email=? AND used_by IS NULL AND revoked_at IS NULL',(now,email))
        code = secrets.token_urlsafe(32)
        cursor = conn.execute('INSERT INTO administrator_invitations(token_hash,email,healthcare_center,center_key,issued_by,created_at,expires_at) VALUES (?,?,?,?,?,?,?)',
            (hashlib.sha256(code.encode()).hexdigest(),email,healthcare_center,center_key(healthcare_center),administrator_id,now,now+expires_hours*3600))
        audit(conn,administrator_id,f'administrator_invitation_issued:{cursor.lastrowid}')
        return code

def list_administrator_invitations(administrator_id):
    with connect() as conn:
        actor = require_system_administrator(conn,administrator_id)
        return [dict(row) for row in conn.execute('SELECT id,email,healthcare_center,created_at,expires_at,used_at,revoked_at FROM administrator_invitations WHERE issued_by=? AND center_key=? ORDER BY id DESC',
            (administrator_id,actor['center_key']))]

def revoke_administrator_invitation(administrator_id, invitation_id):
    with connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        actor = require_system_administrator(conn,administrator_id)
        result = conn.execute('UPDATE administrator_invitations SET revoked_at=? WHERE id=? AND issued_by=? AND center_key=? AND used_by IS NULL AND revoked_at IS NULL',
            (int(time.time()),invitation_id,administrator_id,actor['center_key']))
        if not result.rowcount:
            raise ValueError('No unused invitation was available to revoke.')
        audit(conn,administrator_id,f'administrator_invitation_revoked:{invitation_id}')

def list_accounts_for_review(administrator_id):
    with connect() as conn:
        actor = require_system_administrator(conn,administrator_id)
        return [dict(row) for row in conn.execute('SELECT id,email,full_name,role,healthcare_center,account_status,created_at,approved_at FROM users WHERE center_key=? ORDER BY created_at DESC,id DESC',
            (actor['center_key'],))]

def review_account(administrator_id, target_user_id, decision):
    if decision not in {'active','rejected','suspended'}:
        raise ValueError('Choose approve, reject or suspend.')
    with connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        actor = require_system_administrator(conn,administrator_id)
        target = conn.execute('SELECT * FROM users WHERE id=?',(target_user_id,)).fetchone()
        if not target or target['center_key'] != actor['center_key']:
            raise ValueError('You can review accounts only for your approved healthcare centre.')
        if target_user_id == administrator_id:
            raise ValueError('You cannot approve or suspend your own account.')
        if decision == 'rejected' and target['account_status'] != 'pending':
            raise ValueError('Only pending applications can be rejected. Suspend an active account instead.')
        if decision == 'suspended' and target['account_status'] != 'active':
            raise ValueError('Only active accounts can be suspended.')
        if decision == 'active' and target['account_status']=='active':
            raise ValueError('This account is already active.')
        now = int(time.time())
        conn.execute('UPDATE users SET account_status=?,approved_by=?,approved_at=? WHERE id=?',
            (decision,administrator_id,now if decision=='active' else None,target_user_id))
        conn.execute('DELETE FROM sessions WHERE user_id=?',(target_user_id,))
        audit(conn,administrator_id,f'account_{decision}:{target_user_id}')

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
