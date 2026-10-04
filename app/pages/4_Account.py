import streamlit as st
import db
from ui import setup, clear_session, flash, timestamp


user = setup("Account")

st.title("Account settings")
flash()

role_labels = {
    "system_administrator": "System Administrator",
    "healthcare_worker": "Healthcare Worker",
}

st.write("**Email:** " + user["email"])
st.write(
    "**Account role:** "
    + role_labels.get(user["role"], "Unknown")
)
st.caption("Registered " + timestamp(user["created_at"]))

needs_completion = not db.profile_complete(user)

if needs_completion:
    st.warning(
        "Please enter your healthcare centre name and save "
        "your profile before accessing the other pages."
    )

profile_tab, password_tab = st.tabs(
    ["Profile", "Change password"]
)

with profile_tab:
    with st.form("profile"):
        name = st.text_input(
            "Full name",
            value=user["full_name"],
            max_chars=100,
        )

        healthcare_center = st.text_input(
            "Healthcare centre name",
            value=user.get("healthcare_center") or "",
            max_chars=150,
            help="Enter the name of the healthcare centre where you work.",
        )

        st.caption(
            "Both your full name and healthcare centre name are required."
        )

        save = st.form_submit_button(
            "Save profile",
            type="primary",
            use_container_width=True,
        )

    if save:
        try:
            db.update_profile(
                user_id=user["id"],
                name=name,
                healthcare_center=healthcare_center,
            )

            if needs_completion:
                st.session_state["flash"] = (
                    "Profile completed. Welcome to your dashboard."
                )
                st.switch_page("pages/1_Dashboard.py")
            else:
                st.session_state["flash"] = "Profile updated."
                st.rerun()

        except ValueError as exc:
            st.error(str(exc))

    st.caption(
        "Your centre name identifies your workplace. "
        "It does not grant access to other users’ records."
    )

with password_tab:
    with st.form("password_change", clear_on_submit=True):
        current = st.text_input(
            "Current password",
            type="password",
            max_chars=128,
        )

        new = st.text_input(
            "New password",
            type="password",
            max_chars=128,
        )

        confirm = st.text_input(
            "Confirm new password",
            type="password",
            max_chars=128,
        )

        st.caption(
            "Use 12–128 characters. Changing your password signs "
            "out all sessions for this account."
        )

        st.caption(
            "If your administrator and healthcare-worker accounts "
            "are linked, they must use different passwords."
        )

        change = st.form_submit_button(
            "Change password",
            type="primary",
            use_container_width=True,
        )

    if change:
        try:
            if new != confirm:
                raise ValueError("The new passwords do not match.")

            db.change_password(
                user_id=user["id"],
                current=current,
                new=new,
            )

            clear_session()
            st.session_state["flash"] = (
                "Password changed. Sign in with your new password."
            )
            st.switch_page("streamlit_app.py")

        except ValueError as exc:
            st.error(str(exc))