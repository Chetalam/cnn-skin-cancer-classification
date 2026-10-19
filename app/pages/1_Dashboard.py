from translations import t, display_data, translated_format, language_selector
import streamlit as st
import db
from ui import setup, flash, timestamp
user = setup('Dashboard')
administrator = user['role'] == 'system_administrator'
role_labels = {'system_administrator': 'System Administrator', 'healthcare_worker': 'Healthcare Worker'}
st.title(t('Administrator dashboard' if administrator else 'Healthcare Worker dashboard'))
st.write(t('Welcome back, ' + user['full_name'] + '.'))
role_column, centre_column = st.columns(2)
role_column.write(t('**Account role:** ' + role_labels.get(user['role'], 'Unknown')))
centre_column.write(t('**Healthcare centre:** ' + (user.get('healthcare_center') or 'Not provided')))
flash()
if administrator:
    st.subheader(t('Users at your healthcare centre'))
    accounts = db.list_accounts_for_review(user['id'])
    managed_accounts = [account for account in accounts if account['id'] != user['id']]
    if managed_accounts:
        st.dataframe(display_data([{'Name': account['full_name'], 'Email': account['email'], 'Role': role_labels.get(account['role'], account['role']), 'Status': account['account_status'].title(), 'Registered': timestamp(account['created_at'])} for account in managed_accounts]), hide_index=True, use_container_width=True)
    else:
        st.info(t('No other users are registered at your healthcare centre.'))
    st.caption(t('Use User Management in the sidebar to suspend or reactivate accounts.'))
else:
    rows = db.history(user['id'])
    col1, col2, col3 = st.columns(3)
    col1.metric(t('Your saved reviews'), len(rows))
    col2.metric(t('Your completed predictions'), sum((row['status'] == 'predicted' for row in rows)))
    col3.metric(t('Your reviews awaiting model'), sum((row['status'] == 'awaiting_model' for row in rows)))
    st.subheader(t('Start a review'))
    st.write(t('Upload a de-identified lesion image, check the preview and save a review.'))
    st.page_link('pages/2_Analyse_Image.py', label=t('Open Analyse Image'), icon='🔬')
    st.info(t('The CNN is not integrated. Newly saved reviews await the model and have no predicted class or confidence.'))
    st.subheader(t('Your recent reviews'))
    if rows:
        recent_reviews = [{'Case reference': row['case_reference'] or '—', 'File': row['file_name'], 'Status': 'Awaiting model' if row['status'] == 'awaiting_model' else 'Predicted', 'Saved': timestamp(row['uploaded_at'])} for row in rows[:5]]
        st.dataframe(display_data(recent_reviews), hide_index=True, use_container_width=True)
    else:
        st.info(t('No reviews yet. Your first saved review will appear here.'))
