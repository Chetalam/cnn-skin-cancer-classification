from datetime import datetime, timezone

import streamlit as st
import db

from translations import t, language_selector


DISCLAIMER = (
    "Research decision-support prototype. It does not provide a "
    "medical diagnosis. Suspected skin cancer requires assessment "
    "by a qualified healthcare professional."
)

ADMIN_ONLY_PAGES = {
    "User Management",
    "Dataset Status",
    "Database Guide",
}

WORKER_ONLY_PAGES = {
    "Analyse Image",
    "History",
    "Review Records",
}


def clear_session():
    for key in list(st.session_state):
        if key not in {"app_language", "_language_choice"}:
            del st.session_state[key]


def setup(title, protected=True):
    st.set_page_config(
        page_title=t(title),
        page_icon="🔬",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .stApp {
            background: #ffffff;
            color: #18324d;
        }

        [data-testid="stSidebar"] {
            background: #eff6ff;
            border-right: 1px solid #dbeafe;
        }

        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        .stDeployButton,
        [data-testid="stAppDeployButton"] {
            display: none !important;
        }

        .block-container {
            padding-top: 2rem;
            max-width: 1200px;
        }

        h1, h2, h3 {
            color: #124c8c !important;
        }

        [data-testid="stMetric"] {
            background: #f0f7ff;
            border: 1px solid #dbeafe;
            border-radius: 12px;
            padding: 16px;
        }

        [data-testid="stForm"] {
            border: 1px solid #dbeafe;
            border-radius: 12px;
            background: #fcfdff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    language_selector()
    db.initialize()

    token = st.session_state.get("auth_token")
    user = db.session_user(token)

    if user is None and (protected or token):
        clear_session()

        if token:
            st.session_state["flash"] = (
                "Your session has ended or your account is inactive. "
                "Please sign in again."
            )

        st.switch_page("streamlit_app.py")
        st.stop()

    administrator = bool(
        user
        and user["role"] == "system_administrator"
        and user.get("account_status") == "active"
    )

    worker = bool(
        user
        and user["role"] == "healthcare_worker"
        and user.get("account_status") == "active"
    )

    if user and not (administrator or worker):
        st.error(t("This account role is not supported."))
        st.stop()

    if (
        protected
        and user
        and title != "Account"
        and not db.profile_complete(user)
    ):
        st.switch_page("pages/4_Account.py")
        st.stop()

    with st.sidebar:
        if not user:
            st.page_link(
                "streamlit_app.py",
                label=t("Welcome / Sign in"),
                icon="🔐",
            )
        else:
            st.page_link(
                "pages/1_Dashboard.py",
                label=t("Dashboard"),
                icon="🏠",
            )

            if worker:
                st.page_link(
                    "pages/2_Analyse_Image.py",
                    label=t("Analyse Image"),
                    icon="🔬",
                )

                st.page_link(
                    "pages/3_History.py",
                    label=t("History"),
                    icon="📋",
                )

                st.page_link(
                    "pages/8_Review_Records.py",
                    label=t("Review Records"),
                    icon="📝",
                )

            if administrator:
                st.page_link(
                    "pages/7_User_Management.py",
                    label=t("User Management"),
                    icon="👥",
                )

                st.page_link(
                    "pages/5_Dataset_Status.py",
                    label=t("Dataset Status"),
                    icon="📊",
                )

                st.page_link(
                    "pages/9_Database_Guide.py",
                    label=t("Database Guide"),
                    icon="🗄️",
                )

            st.page_link(
                "pages/4_Account.py",
                label=t("Account"),
                icon="👤",
            )

            st.page_link(
                "pages/6_Help.py",
                label=t("Help"),
                icon="❓",
            )

            st.divider()
            st.write(user["full_name"])

            if st.button(
                t("Log out"),
                use_container_width=True,
                key="sidebar_logout",
            ):
                db.sign_out(token)
                clear_session()
                st.switch_page("streamlit_app.py")
                st.stop()

    denied = (
        title in ADMIN_ONLY_PAGES and not administrator
    ) or (
        title in WORKER_ONLY_PAGES and not worker
    )

    if denied:
        message = (
            "Use your separate Healthcare Worker account "
            "for image reviews."
            if title in WORKER_ONLY_PAGES
            else (
                "This page is available only to active "
                "System Administrators."
            )
        )

        st.error(t(message))

        st.page_link(
            "pages/1_Dashboard.py"
            if user
            else "streamlit_app.py",
            label=t(
                "Return to dashboard"
                if user
                else "Sign in"
            ),
        )

        st.stop()

    if user:
        st.caption(t(title))

    return user


def disclaimer():
    st.warning(t(DISCLAIMER))


def timestamp(value):
    return datetime.fromtimestamp(
        value,
        timezone.utc,
    ).strftime("%d %b %Y, %H:%M UTC")


def flash():
    message = st.session_state.pop("flash", None)

    if message:
        st.success(t(message))