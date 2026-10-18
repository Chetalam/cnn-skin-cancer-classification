import streamlit as st
import db
from ui import setup, clear_session, flash, timestamp

user = setup("Account")
st.title("Account settings")
flash()
roles = {"system_administrator": "System Administrator", "healthcare_worker": "Healthcare Worker"}
st.write("Email:", user["email"])
st.write("Account role:", roles.get(user["role"], user["role"]))
st.caption("Registered " + timestamp(user["created_at"]))
needs_completion = not db.profile_complete(user)
if needs_completion:
    st.warning("Enter your healthcare centre name and save your profile to continue.")

profile_tab, password_tab, deactivate_tab = st.tabs(["Profile", "Change password", "Deactivate profile"])
with profile_tab:
    with st.form("profile"):
        name = st.text_input("Full name", value=user["full_name"], max_chars=100)
        centre = st.text_input("Healthcare centre name", value=user.get("healthcare_center") or "", max_chars=150)
        save = st.form_submit_button("Save profile", type="primary")
    if save:
        try:
            db.update_profile(user["id"], name, centre)
            st.session_state["flash"] = "Profile updated."
            if needs_completion:
                st.switch_page("pages/1_Dashboard.py")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    st.caption("Your centre name does not grant access to other users' saved reviews.")

with password_tab:
    with st.form("password_change", clear_on_submit=True):
        current = st.text_input("Current password", type="password", max_chars=128)
        new = st.text_input("New password", type="password", max_chars=128)
        confirm = st.text_input("Confirm new password", type="password", max_chars=128)
        st.caption("Use 12–128 characters. Linked accounts for different roles must use different passwords.")
        change = st.form_submit_button("Change password", type="primary")
    if change:
        try:
            if new != confirm:
                raise ValueError("The new passwords do not match.")
            db.change_password(user["id"], current, new)
            clear_session()
            st.session_state["flash"] = "Password changed. Sign in again."
            st.switch_page("streamlit_app.py")
        except ValueError as exc:
            st.error(str(exc))

with deactivate_tab:
    st.write("Deactivation prevents sign-in and ends all sessions for this account. Your profile and saved reviews stay in the database.")
    st.info("To reactivate your profile, contact an active administrator at your healthcare centre. Deactivation does not affect a separate account you hold for another role.")
    if user["role"] == "system_administrator":
        st.caption("Another active administrator at your centre must remain available.")
    with st.form("deactivate_profile", clear_on_submit=True):
        deactivate_password = st.text_input("Enter your current password", type="password", max_chars=128)
        acknowledged = st.checkbox("I understand that my data will be retained and an administrator is needed to reactivate my account.")
        deactivate = st.form_submit_button("Deactivate my profile")
    if deactivate:
        try:
            if not acknowledged:
                raise ValueError("Confirm that you understand deactivation before continuing.")
            db.deactivate_profile(st.session_state.get("auth_token"), deactivate_password)
            clear_session()
            st.session_state["flash"] = "Your profile is deactivated. Your saved data has been retained."
            st.switch_page("streamlit_app.py")
        except ValueError as exc:
            st.error(str(exc))