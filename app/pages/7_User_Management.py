from translations import t, display_data, translated_format, language_selector
import streamlit as st
import db
from ui import setup, flash, timestamp
user = setup('User Management')
if user['role'] != 'system_administrator' or user.get('account_status') != 'active':
    st.error(t('Only active System Administrators can manage accounts.'))
    st.stop()
st.title(t('User Management'))
st.write(t('Healthcare centre:'), user['healthcare_center'])
st.caption(t('Manage access within your centre. Suspending or deactivating an account retains its saved records.'))
flash()
try:
    accounts = db.list_accounts_for_review(user['id'])
except ValueError as exc:
    st.error(t(str(exc)))
    st.stop()
roles = {'system_administrator': 'System Administrator', 'healthcare_worker': 'Healthcare Worker'}
columns = st.columns(3)
for column, status in zip(columns, ['active', 'suspended', 'deactivated']):
    column.metric(t(status.title() + ' accounts'), sum((a['account_status'] == status for a in accounts)))
st.dataframe(display_data([{'Name': a['full_name'], 'Email': a['email'], 'Role': roles.get(a['role'], a['role']), 'Status': a['account_status'].title(), 'Registered': timestamp(a['created_at']), 'Deactivated': timestamp(a['deactivated_at']) if a.get('deactivated_at') else '—'} for a in accounts]), hide_index=True, use_container_width=True)
st.caption(t('Password hashes and session tokens are not displayed. Centre names remain self-declared.'))
manageable = {a['id']: a for a in accounts if a['id'] != user['id']}
if not manageable:
    st.info(t('No other accounts to manage.'))
else:
    selected = st.selectbox(t('Select an account'), list(manageable), format_func=translated_format(lambda key: manageable[key]['full_name'] + ' — ' + manageable[key]['email']), key='pages/7_User_Management.py:34:selectbox')
    target = manageable[selected]
    active = target['account_status'] == 'active'
    st.write(t('Current status:'), t(target['account_status'].title()))
    st.info(t('Suspend prevents access. Restore/reactivate permits sign-in again. Saved reviews are retained.'))
    with st.form(f'manage_{selected}'):
        confirmed = st.checkbox(t('I confirm this account action is authorised.'), key='pages/7_User_Management.py:40:checkbox')
        submit = st.form_submit_button(t('Suspend account' if active else 'Restore / reactivate account'), type='primary')
    if submit:
        try:
            if not confirmed:
                raise ValueError('Confirm the account action first.')
            db.review_account(user['id'], selected, 'suspended' if active else 'active')
            st.session_state['flash'] = 'Account suspended.' if active else 'Account restored. The user can sign in again.'
            st.rerun()
        except ValueError as exc:
            st.error(t(str(exc)))
