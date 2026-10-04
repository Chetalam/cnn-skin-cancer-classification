from datetime import datetime, timezone

import streamlit as st
import db


DISCLAIMER = (
    "Research decision-support prototype. It does not provide a "
    "medical diagnosis. Suspected skin cancer requires assessment "
    "by a qualified healthcare professional."
)

ADMIN_ONLY_PAGES = {
    "User Management",
    "Dataset Status",
}


def clear_session():
    for key in list(st.session_state):
        del st.session_state[key]


def setup(title, protected=True):
    st.set_page_config(
        page_title=title + " | SkinCare Research",
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

        /* Replace automatic navigation with our account-aware links. */
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

    db.initialize()

    token = st.session_state.get("auth_token")
    user = db.session_user(token)

    if user is None and (protected or token):
        clear_session()

        if token:
            st.session_state["flash"] = (
                "Your session has ended. Please sign in again."
            )

        st.switch_page("streamlit_app.py")
        st.stop()

    with st.sidebar:
        if user is None:
            st.page_link(
                "streamlit_app.py",
                label="Welcome / Sign in",
                icon="🔐",
            )
        else:
            st.page_link(
                "pages/1_Dashboard.py",
                label="Dashboard",
                icon="🏠",
            )
            st.page_link(
                "pages/2_Analyse_Image.py",
                label="Analyse Image",
                icon="🔬",
            )
            st.page_link(
                "pages/3_History.py",
                label="History",
                icon="📋",
            )
            st.page_link(
                "pages/4_Account.py",
                label="Account",
                icon="👤",
            )

            if (
                user["role"] == "system_administrator"
                and user.get("account_status") == "active"
            ):
                st.page_link(
                    "pages/5_Dataset_Status.py",
                    label="Dataset Status",
                    icon="📊",
                )
                st.page_link(
                    "pages/7_User_Management.py",
                    label="User Management",
                    icon="👥",
                )

            st.page_link(
                "pages/6_Help.py",
                label="Help",
                icon="❓",
            )

            st.divider()
            st.write(user["full_name"])

            if st.button("Log out", use_container_width=True):
                db.sign_out(st.session_state["auth_token"])
                clear_session()
                st.switch_page("streamlit_app.py")
                st.stop()

    if (
        protected
        and user is not None
        and title != "Account"
        and not db.profile_complete(user)
    ):
        st.switch_page("pages/4_Account.py")
        st.stop()

    if title in ADMIN_ONLY_PAGES:
        if (
            user is None
            or user["role"] != "system_administrator"
            or user.get("account_status") != "active"
        ):
            st.error(
                "This page is available only to active "
                "System Administrators."
            )
            st.page_link(
                "pages/1_Dashboard.py",
                label="Return to your dashboard",
                icon="🏠",
            )
            st.stop()

    if user:
        st.caption("SKINCARE RESEARCH  /  " + title.upper())

    return user


def disclaimer():
    st.warning(DISCLAIMER)


def timestamp(value):
    return datetime.fromtimestamp(
        value, timezone.utc
    ).strftime("%d %b %Y, %H:%M UTC")


def flash():
    message = st.session_state.pop("flash", None)
    if message:
        st.success(message)