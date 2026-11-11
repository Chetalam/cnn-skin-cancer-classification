from translations import t, display_data, translated_format, language_selector
import streamlit as st
from ui import setup, disclaimer
user = setup('Help')
st.title(t('Help'))
with st.expander(t('Account and sign-in'), expanded=True):
    st.write(t('Use Account to edit your name and centre or change your password. Changing your password ends all sessions for that account. Email verification and password-reset emails are not enabled.'))
with st.expander(t('Deactivation and reactivation')):
    st.write(t('Open Account → Deactivate profile. Enter your current password and confirm. Your profile and reviews remain saved. An active administrator at your centre can reactivate your account. The last active administrator at a centre cannot self-deactivate.'))
if user['role'] == 'healthcare_worker':
    with st.expander(t('Create and view reviews')):
        st.write(t('Open Analyse Image to upload and save a de-identified image. Reviews contains your saved records, predictions, referral downloads and CSV export. Save without prediction retains an awaiting-model record. Model scores are not a diagnosis.'))
    with st.expander(t('Update, archive or restore a review')):
        st.write(t('Open Reviews to edit a case reference, archive a review or restore it. Archiving hides it from the active list and retains its preview and predictions. Choose Archived reviews to restore it.'))
else:
    with st.expander(t('Administrator tasks')):
        st.write(t('User Management controls account access within your centre. Dataset Status manages imported dataset metadata. Database Guide explains the tables and CRUD actions and shows database health.'))
    with st.expander(t('Image reviews')):
        st.write(t("Sign out and use your separate Healthcare Worker account to upload images or access review history. Administrator access does not expose other users' private reviews. Previously saved administrator reviews remain retained in the database."))
disclaimer()

with st.expander(t('Analytics')):
    st.write(t('Analytics shows activity and prediction counts. Workers see their own records; administrators see centre aggregates. It does not measure live diagnostic accuracy.'))
