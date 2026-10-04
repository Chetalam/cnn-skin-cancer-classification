import streamlit as st
import db
from ui import setup, clear_session, flash


ROLE_OPTIONS = {
    "Healthcare Worker": "healthcare_worker",
    "System Administrator": "system_administrator",
}


def open_account_page(user):
    if db.profile_complete(user):
        st.switch_page("pages/1_Dashboard.py")
    else:
        st.switch_page("pages/4_Account.py")


user = setup("Welcome", protected=False)

if user:
    open_account_page(user)


st.title("Welcome to SkinCare Research")
st.write(
    "A workspace for skin lesion image review "
    "and CNN classification research."
)
st.info(
    "Register or sign in to access your dashboard. "
    "Predictions will become available after model integration."
)

flash()

left, right = st.columns([1.15, 1], gap="large")

with left:
    login_tab, register_tab = st.tabs(
        ["Sign in", "Create account"]
    )

    with login_tab:
        with st.form("login", clear_on_submit=True):
            email = st.text_input(
                "Email address",
                key="login_email",
                max_chars=254,
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
                max_chars=128,
            )

            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            try:
                token = db.sign_in(email, password)
                signed_in_user = db.session_user(token)

                if signed_in_user is None:
                    db.sign_out(token)
                    raise ValueError(
                        "Sign-in could not be completed. Please try again."
                    )

                clear_session()
                st.session_state["auth_token"] = token
                open_account_page(signed_in_user)

            except ValueError as exc:
                st.error(str(exc))

        st.caption(
            "Email verification and password-reset emails "
            "are not enabled in this prototype."
        )

    with register_tab:
        # Outside the form so changing the role updates its fields.
        role_label = st.selectbox(
            "Which account are you creating?",
            options=list(ROLE_OPTIONS),
            key="registration_role",
        )
        requested_role = ROLE_OPTIONS[role_label]
        is_administrator = requested_role == "system_administrator"

        if is_administrator:
            st.info(
                "System Administrator registration requires an "
                "invitation for your email address and healthcare "
                "centre. After registration, your application "
                "must be approved before you can sign in."
            )
            other_role_label = "Healthcare Worker"
        else:
            st.info(
                "Healthcare Worker accounts are active immediately "
                "after registration. No invitation or administrator "
                "approval is required."
            )
            other_role_label = "System Administrator"

        st.caption(
            "Full name, healthcare centre, email and password "
            "are required for both roles."
        )

        # A separate checkbox state is kept for each signup role.
        link_existing = st.checkbox(
            f"I already have a {other_role_label} account "
            "and am creating my separate account for this role.",
            key=f"link_existing_{requested_role}",
        )

        if link_existing:
            st.info(
                "Verify your existing account below. Your new "
                "account must use a different email address "
                "and password."
            )

        with st.form(
            f"register_{requested_role}",
            clear_on_submit=True,
        ):
            name = st.text_input(
                "Full name",
                max_chars=100,
                key=f"register_name_{requested_role}",
            )

            healthcare_center = st.text_input(
                "Healthcare centre name",
                max_chars=150,
                key=f"register_center_{requested_role}",
                help=(
                    "Enter the healthcare centre where you work. "
                    "Administrator applications must match the "
                    "centre named in their invitation."
                ),
            )

            new_email = st.text_input(
                "Email address",
                max_chars=254,
                key=f"register_email_{requested_role}",
            )

            new_password = st.text_input(
                "Password",
                type="password",
                max_chars=128,
                key=f"register_password_{requested_role}",
            )

            confirm = st.text_input(
                "Confirm password",
                type="password",
                max_chars=128,
                key=f"register_confirm_{requested_role}",
            )

            st.caption(
                "Use a password or passphrase with 12–128 characters."
            )

            invitation_code = None

            if is_administrator:
                invitation_code = st.text_input(
                    "Administrator invitation code",
                    type="password",
                    max_chars=200,
                    key="register_administrator_invitation",
                    help=(
                        "Use the code issued for your email address "
                        "by an administrator at your healthcare centre."
                    ),
                )

            linked_email = None
            linked_password = None

            if link_existing:
                st.markdown(
                    f"**Verify your existing {other_role_label} account**"
                )

                linked_email = st.text_input(
                    "Existing account email address",
                    max_chars=254,
                    key=f"linked_email_{requested_role}",
                )

                linked_password = st.text_input(
                    "Existing account password",
                    type="password",
                    max_chars=128,
                    key=f"linked_password_{requested_role}",
                )

            agree = st.checkbox(
                "I understand this is a research prototype "
                "and will use de-identified images.",
                key=f"register_agree_{requested_role}",
            )

            registered = st.form_submit_button(
                (
                    "Submit administrator application"
                    if is_administrator
                    else "Create account"
                ),
                type="primary",
                use_container_width=True,
            )

        if registered:
            try:
                if not agree:
                    raise ValueError(
                        "Please acknowledge the research-use notice."
                    )

                if new_password != confirm:
                    raise ValueError("The passwords do not match.")

                if is_administrator and not (
                    invitation_code or ""
                ).strip():
                    raise ValueError(
                        "Enter your administrator invitation code."
                    )

                if link_existing and (
                    not (linked_email or "").strip()
                    or not linked_password
                ):
                    raise ValueError(
                        "Enter your existing account email and "
                        "password to link your two accounts."
                    )

                db.register(
                    name=name,
                    email=new_email,
                    password=new_password,
                    healthcare_center=healthcare_center,
                    requested_role=requested_role,
                    invitation_code=(
                        invitation_code.strip()
                        if is_administrator
                        else None
                    ),
                    linked_account_email=(
                        linked_email if link_existing else None
                    ),
                    linked_account_password=(
                        linked_password if link_existing else None
                    ),
                )

                if is_administrator:
                    st.success(
                        "Administrator application submitted. "
                        "You can sign in once an administrator "
                        "at your healthcare centre approves it."
                    )
                else:
                    st.success(
                        "Healthcare Worker account created. "
                        "You can sign in now using the Sign in tab."
                    )

            except ValueError as exc:
                st.error(str(exc))

        st.caption(
            "Entering a healthcare centre name does not verify "
            "employment at that centre."
        )

with right:
    st.subheader("Your research workspace")

    st.markdown(
        """
        **Dashboard** — account role, healthcare centre and activity

        **Analyse Image** — upload, preview and save a review

        **History** — your saved records and CSV export

        **Account** — profile, healthcare centre and password settings

        **Dataset Status** — cleaned dataset and database checks

        **Help** — instructions and project scope
        """
    )

    st.warning(
        "No clinical diagnosis is provided at this milestone."
    )