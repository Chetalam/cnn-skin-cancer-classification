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
                        "Sign-in could not be completed."
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
        role_label = st.selectbox(
            "Which account are you creating?",
            options=list(ROLE_OPTIONS),
            key="registration_role",
        )

        requested_role = ROLE_OPTIONS[role_label]

        st.info(
            "Both account roles are active immediately after "
            "registration. No invitation or approval is required."
        )

        # Healthcare Worker signup never requires an existing account.
        link_existing = False

        if requested_role == "system_administrator":
            link_existing = st.checkbox(
                "I already have a Healthcare Worker account "
                "and am creating my separate System Administrator account.",
                key="link_existing_system_administrator",
            )

        with st.form(
            f"register_{requested_role}",
            clear_on_submit=True,
        ):
            name = st.text_input(
                "Full name",
                max_chars=100,
                key=f"name_{requested_role}",
            )

            healthcare_center = st.text_input(
                "Healthcare centre name",
                max_chars=150,
                key=f"center_{requested_role}",
            )

            new_email = st.text_input(
                "Email address",
                max_chars=254,
                key=f"email_{requested_role}",
            )

            new_password = st.text_input(
                "Password",
                type="password",
                max_chars=128,
                key=f"password_{requested_role}",
            )

            confirm = st.text_input(
                "Confirm password",
                type="password",
                max_chars=128,
                key=f"confirm_{requested_role}",
            )

            st.caption(
                "Use a password or passphrase with 12–128 characters."
            )

            linked_email = None
            linked_password = None

            if link_existing:
                st.markdown(
                    "**Verify your existing Healthcare Worker account**"
                )

                st.caption(
                    "Your new account must use a different "
                    "email address and password."
                )

                linked_email = st.text_input(
                    "Existing account email address",
                    max_chars=254,
                    key="linked_email_system_administrator",
                )

                linked_password = st.text_input(
                    "Existing account password",
                    type="password",
                    max_chars=128,
                    key="linked_password_system_administrator",
                )

            agree = st.checkbox(
                "I understand this is a research prototype "
                "and will use de-identified images.",
                key=f"agree_{requested_role}",
            )

            registered = st.form_submit_button(
                "Create account",
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
                    raise ValueError(
                        "The passwords do not match."
                    )

                if link_existing and (
                    not (linked_email or "").strip()
                    or not linked_password
                ):
                    raise ValueError(
                        "Enter your existing account email "
                        "and password."
                    )

                db.register(
                    name=name,
                    email=new_email,
                    password=new_password,
                    healthcare_center=healthcare_center,
                    requested_role=requested_role,
                    linked_account_email=(
                        linked_email if link_existing else None
                    ),
                    linked_account_password=(
                        linked_password if link_existing else None
                    ),
                )

                st.success(
                    f"{role_label} account created. "
                    "Use the Sign in tab to continue."
                )

            except ValueError as exc:
                st.error(str(exc))

        st.caption(
            "Healthcare centre names are self-declared."
        )

with right:
    st.subheader("Your research workspace")

    st.markdown(
        """
        **Dashboard** — account role, healthcare centre and activity

        **Analyse Image** — upload, preview and save a review

        **History** — saved records and CSV export

        **Account** — profile and password settings

        **User Management** — administrator account controls

        **Help** — instructions and project scope
        """
    )

    st.warning(
        "No clinical diagnosis is provided at this milestone."
    )