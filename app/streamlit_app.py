from translations import t, display_data, translated_format, language_selector
import streamlit as st
import db
from ui import setup, clear_session, flash
ROLE_OPTIONS = {'Healthcare Worker': 'healthcare_worker', 'System Administrator': 'system_administrator'}

def open_account_page(user):
    if db.profile_complete(user):
        st.switch_page('pages/1_Dashboard.py')
    else:
        st.switch_page('pages/4_Account.py')
user = setup('Welcome', protected=False)
if user:
    open_account_page(user)
st.title(t('Welcome to SkinCare Research'))
st.write(t('A workspace for skin lesion image review and CNN classification research.'))
st.info(t('Register or sign in to access your dashboard. Predictions will become available after model integration.'))
flash()
left, right = st.columns([1.15, 1], gap='large')
with left:
    login_tab, register_tab = st.tabs(display_data(['Sign in', 'Create account']))
    with login_tab:
        with st.form('login', clear_on_submit=True):
            email = st.text_input(t('Email address'), key='login_email', max_chars=254)
            password = st.text_input(t('Password'), type='password', key='login_password', max_chars=128)
            submitted = st.form_submit_button(t('Sign in'), type='primary', use_container_width=True)
        if submitted:
            try:
                token = db.sign_in(email, password)
                signed_in_user = db.session_user(token)
                if signed_in_user is None:
                    db.sign_out(token)
                    raise ValueError('Sign-in could not be completed.')
                clear_session()
                st.session_state['auth_token'] = token
                open_account_page(signed_in_user)
            except ValueError as exc:
                st.error(t(str(exc)))
        st.caption(t('Email verification and password-reset emails are not enabled in this prototype.'))
    with register_tab:
        role_label = st.selectbox(t('Which account are you creating?'), options=list(ROLE_OPTIONS), key='registration_role', format_func=t)
        requested_role = ROLE_OPTIONS[role_label]
        st.info(t('Both account roles are active immediately after registration. No invitation or approval is required.'))
        link_existing = False
        if requested_role == 'system_administrator':
            link_existing = st.checkbox(t('I already have a Healthcare Worker account and am creating my separate System Administrator account.'), key='link_existing_system_administrator')
        with st.form(f'register_{requested_role}', clear_on_submit=True):
            name = st.text_input(t('Full name'), max_chars=100, key=f'name_{requested_role}')
            healthcare_center = st.text_input(t('Healthcare centre name'), max_chars=150, key=f'center_{requested_role}')
            new_email = st.text_input(t('Email address'), max_chars=254, key=f'email_{requested_role}')
            new_password = st.text_input(t('Password'), type='password', max_chars=128, key=f'password_{requested_role}')
            confirm = st.text_input(t('Confirm password'), type='password', max_chars=128, key=f'confirm_{requested_role}')
            st.caption(t('Use a password or passphrase with 12–128 characters.'))
            linked_email = None
            linked_password = None
            if link_existing:
                st.markdown(t('**Verify your existing Healthcare Worker account**'))
                st.caption(t('Your new account must use a different email address and password.'))
                linked_email = st.text_input(t('Existing account email address'), max_chars=254, key='linked_email_system_administrator')
                linked_password = st.text_input(t('Existing account password'), type='password', max_chars=128, key='linked_password_system_administrator')
            agree = st.checkbox(t('I understand this is a research prototype and will use de-identified images.'), key=f'agree_{requested_role}')
            registered = st.form_submit_button(t('Create account'), type='primary', use_container_width=True)
        if registered:
            try:
                if not agree:
                    raise ValueError('Please acknowledge the research-use notice.')
                if new_password != confirm:
                    raise ValueError('The passwords do not match.')
                if link_existing and (not (linked_email or '').strip() or not linked_password):
                    raise ValueError('Enter your existing account email and password.')
                db.register(name=name, email=new_email, password=new_password, healthcare_center=healthcare_center, requested_role=requested_role, linked_account_email=linked_email if link_existing else None, linked_account_password=linked_password if link_existing else None)
                st.success(t(f'{role_label} account created. Use the Sign in tab to continue.'))
            except ValueError as exc:
                st.error(t(str(exc)))
        st.caption(t('Healthcare centre names are self-declared.'))
with right:
    st.subheader(t('Your research workspace'))
    st.markdown(t('\n        **Dashboard** — account role, healthcare centre and activity\n\n        **Analyse Image** — upload, preview and save a review\n\n        **History** — saved records and CSV export\n\n        **Account** — profile and password settings\n\n        **User Management** — administrator account controls\n\n        **Help** — instructions for using the app\n        '))
    st.warning(t('No clinical diagnosis is provided at this milestone.'))
