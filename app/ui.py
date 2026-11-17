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

    # Apply the warmer, more vibrant theme only to protected (signed-in)
    # pages. Login and registration retain their established appearance.
    if protected:
        st.markdown(
            """
            <style>
            :root {
                --skin-navy: #103F53;
                --skin-teal: #087F79;
                --skin-coral: #F07868;
                --skin-amber: #F2B84B;
                --skin-mint: #DDF3ED;
                --skin-white: #F5F8FA;
            }
            .stApp {
                background:
                    radial-gradient(circle at 95% 1%, rgba(240,120,104,.10), transparent 27%),
                    radial-gradient(circle at 5% 12%, rgba(8,127,121,.09), transparent 25%),
                    var(--skin-white);
                color: var(--skin-navy);
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(175deg, #ecf8f4 0%, var(--skin-mint) 100%);
                border-right: 1px solid #c4ddd6;
            }
            [data-testid="stSidebar"] .sidebar-brand {
                color: var(--skin-navy);
                padding: .8rem .85rem;
                background: #ffffffcc;
                border-radius: 12px;
                border-left: 4px solid var(--skin-coral);
                box-shadow: 0 3px 12px #103f5309;
            }
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"],
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span,
            [data-testid="stSidebar"] a {
                border-radius: 10px;
                transition: background-color .18s ease, color .18s ease;
            }
            [data-testid="stSidebar"] a:hover {
                background: #ffffffb8;
            }
            [data-testid="stSidebar"] a[aria-current="page"],
            [data-testid="stSidebar"] a[aria-current="page"]:hover,
            [data-testid="stSidebar"] a[aria-selected="true"] {
                color: var(--skin-navy);
                background: #ffffff;
                box-shadow: inset 4px 0 var(--skin-coral), 0 2px 10px #103f530f;
                font-weight: 650;
            }
            [data-testid="stMain"] .block-container {
                padding-top: 5.5rem;
                padding-bottom: 3.5rem;
            }
            [data-testid="stMain"] h1,
            [data-testid="stMain"] h2,
            [data-testid="stMain"] h3 {
                color: var(--skin-navy) !important;
                letter-spacing: -.025em;
            }
            [data-testid="stMain"] h1 {
                line-height: 1.18;
                margin-bottom: .35rem;
            }
            [data-testid="stMain"] h1::after {
                content: "";
                display: block;
                width: 4.2rem;
                height: .27rem;
                margin-top: .7rem;
                border-radius: 99px;
                background: linear-gradient(90deg, var(--skin-coral) 0 55%, var(--skin-amber) 55% 100%);
            }
            [data-testid="stMain"] h2 {
                border-bottom: 1px solid #dbe9e7;
                padding-bottom: .38rem;
            }
            [data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid #d4e7e1;
                border-top: 4px solid var(--skin-teal);
                border-radius: 16px;
                padding: 1.15rem 1.2rem;
                box-shadow: 0 5px 22px #103f530b;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3n+2) [data-testid="stMetric"] {
                border-top-color: var(--skin-coral);
            }
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3n) [data-testid="stMetric"] {
                border-top-color: #c58b19;
            }
            [data-testid="stMetricValue"] {
                color: var(--skin-navy);
                font-weight: 750;
            }
            [data-testid="stMetricLabel"] {
                color: #395969;
                font-weight: 600;
            }
            [data-testid="stForm"],
            [data-testid="stExpander"],
            [data-testid="stVerticalBlockBorderWrapper"] > div {
                border-color: #d4e6e3;
                border-radius: 15px;
            }
            [data-testid="stForm"], [data-testid="stExpander"] {
                background: #ffffffed;
                box-shadow: 0 3px 16px #103f5308;
            }
            [data-testid="stMain"] [data-testid="stButton"] button[kind="primary"],
            [data-testid="stMain"] [data-testid="stFormSubmitButton"] button[kind="primary"] {
                background: var(--skin-teal);
                color: #ffffff;
                border: 1px solid var(--skin-teal);
                border-radius: 11px;
                box-shadow: 0 4px 10px #087f7926;
                font-weight: 650;
            }
            [data-testid="stMain"] [data-testid="stButton"] button[kind="primary"]:hover,
            [data-testid="stMain"] [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
                background: var(--skin-navy);
                border-color: var(--skin-navy);
            }
            [data-testid="stMain"] [data-testid="stButton"] button[kind="secondary"],
            [data-testid="stMain"] [data-testid="stFormSubmitButton"] button[kind="secondary"],
            [data-testid="stMain"] [data-testid="stDownloadButton"] button {
                background: #ffffff;
                color: var(--skin-navy);
                border: 1px solid #a4cec6;
                border-radius: 11px;
                font-weight: 600;
            }
            [data-testid="stMain"] [data-testid="stButton"] button[kind="secondary"]:hover,
            [data-testid="stMain"] [data-testid="stDownloadButton"] button:hover {
                background: var(--skin-mint);
                color: var(--skin-navy);
                border-color: var(--skin-teal);
            }
            [data-testid="stMain"] button:focus-visible,
            [data-testid="stSidebar"] a:focus-visible,
            [data-testid="stMain"] a:focus-visible {
                outline: 3px solid #b07a13;
                outline-offset: 3px;
            }
            [data-testid="stMain"] input:focus,
            [data-testid="stMain"] textarea:focus,
            [data-testid="stMain"] [role="combobox"]:focus {
                border-color: var(--skin-teal);
                box-shadow: 0 0 0 2px #087f7928;
            }
            [data-testid="stMain"] [data-testid="stTable"],
            [data-testid="stMain"] [data-testid="stDataFrame"] {
                border: 1px solid #d8e7e6;
                background: #ffffff;
                border-radius: 13px;
                overflow: hidden;
            }
            [data-testid="stMain"] [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
                color: var(--skin-navy);
                font-weight: 700;
            }
            [data-testid="stMain"] [data-testid="stTabs"] [role="tab"]:hover {
                color: var(--skin-teal);
            }
            [data-testid="stMain"] [data-testid="stAlert"] {
                border-radius: 12px;
                border-color: #ccdfda;
            }
            [data-testid="stMain"] hr {
                border-color: #d6e7e1;
            }
            @media (max-width: 640px) {
                [data-testid="stMain"] .block-container {
                    padding: 5rem 1rem 2.5rem;
                }
                [data-testid="stMetric"] {
                    padding: .85rem 1rem;
                }
            }
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