from datetime import datetime, timezone

import streamlit as st
import db

from translations import t, language_selector
from branding import SHORT_NAME
from html import escape


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
    "Reviews",
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
        .stApp {background:linear-gradient(145deg,#f7fafc,#eef5f5);color:#19334a}
        [data-testid="stSidebar"] {background:#e9f2f3;border-right:1px solid #d1e2e5}
        [data-testid="stSidebarNav"],.stDeployButton,[data-testid="stAppDeployButton"] {display:none!important}
        [data-testid="stMain"] {overflow-y:auto}
        .block-container {padding-top:6rem;padding-bottom:3rem;max-width:1320px}
        h1,h2,h3 {color:#153e53!important;letter-spacing:-.025em}
        [data-testid="stMetric"] {background:#fff;border:1px solid #d5e5e9;border-top:4px solid #087f79;border-radius:16px;padding:20px;box-shadow:0 5px 20px #19334a08}
        [data-testid="stForm"],[data-testid="stExpander"] {background:#fff;border:1px solid #d5e5e9;border-radius:16px}
        [data-testid="stForm"] {padding:24px}
        .project-hero {padding:32px;border-radius:22px;background:linear-gradient(120deg,#103f53,#086e69);margin-bottom:26px;color:#fff}
        .project-hero h1 {color:#fff!important;font-size:clamp(1.65rem,2.6vw,2.55rem);line-height:1.22;max-width:1050px;margin:10px 0 18px}
        .project-hero p {color:#e1f1f2;font-size:1.05rem;max-width:850px;margin:0}
        .project-eyebrow {font-size:.85rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#b6e4df}
        .feature-card {background:#fff;border:1px solid #d5e5e9;border-radius:16px;padding:19px 22px;margin-bottom:14px}
        .feature-card h3 {font-size:1.1rem;margin:0 0 7px}
        .feature-card p {margin:0;color:#506879;line-height:1.6}
        .sidebar-brand {font-size:1.05rem;font-weight:700;color:#125d61;margin:0 0 16px}
        @media(max-width:640px) {.project-hero {padding:22px}.block-container {padding-left:1rem;padding-right:1rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown('<div class="sidebar-brand">' + escape(t(SHORT_NAME)) + '</div>', unsafe_allow_html=True)
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
                    label=t("Reviews"),
                    icon="📋",
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

            st.page_link("pages/10_Analytics.py", label=t("Analytics"), icon="📈")

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