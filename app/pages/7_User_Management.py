import time

import streamlit as st
import db
from ui import setup, flash, timestamp


ROLE_LABELS = {
    "system_administrator": "System Administrator",
    "healthcare_worker": "Healthcare Worker",
}


def invitation_status(invitation):
    if invitation["used_at"] is not None:
        return "Used"
    if invitation["revoked_at"] is not None:
        return "Revoked"
    if invitation["expires_at"] <= int(time.time()):
        return "Expired"
    return "Available"


user = setup("User Management")

if (
    user["role"] != "system_administrator"
    or user.get("account_status") != "active"
):
    st.error(
        "User Management is available only to active "
        "System Administrators."
    )
    st.stop()

st.title("User Management")
st.write("**Healthcare centre:** " + user["healthcare_center"])
st.caption(
    "Manage accounts within your healthcare centre. "
    "Healthcare workers can register and sign in immediately."
)

flash()

try:
    accounts = db.list_accounts_for_review(user["id"])
    invitations = db.list_administrator_invitations(user["id"])
except ValueError as exc:
    st.error(str(exc))
    st.stop()

pending_admins = [
    account
    for account in accounts
    if account["role"] == "system_administrator"
    and account["account_status"] == "pending"
]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Active healthcare workers",
    sum(
        account["role"] == "healthcare_worker"
        and account["account_status"] == "active"
        for account in accounts
    ),
)

col2.metric(
    "Active administrators",
    sum(
        account["role"] == "system_administrator"
        and account["account_status"] == "active"
        for account in accounts
    ),
)

col3.metric(
    "Administrator applications",
    len(pending_admins),
)

applications_tab, invitations_tab, accounts_tab = st.tabs(
    [
        "Administrator applications",
        "Administrator invitations",
        "Manage accounts",
    ]
)

with applications_tab:
    st.subheader("Review administrator applications")
    st.write(
        "Confirm the applicant is authorised to administer "
        "your healthcare centre before approving their account."
    )

    if not pending_admins:
        st.info("No administrator applications are awaiting approval.")
    else:
        candidates = {
            account["id"]: account
            for account in pending_admins
        }

        selected_id = st.selectbox(
            "Select an application",
            options=list(candidates),
            format_func=lambda account_id: (
                candidates[account_id]["full_name"]
                + " — "
                + candidates[account_id]["email"]
            ),
            key="application_account",
        )

        applicant = candidates[selected_id]

        st.write("**Name:** " + applicant["full_name"])
        st.write("**Email:** " + applicant["email"])
        st.write(
            "**Healthcare centre:** "
            + applicant["healthcare_center"]
        )
        st.caption(
            "Application submitted "
            + timestamp(applicant["created_at"])
        )

        with st.form(f"review_application_{selected_id}"):
            decision_label = st.radio(
                "Decision",
                ["Approve", "Reject"],
            )

            confirmed = st.checkbox(
                "I have checked this application and "
                "confirm the selected decision."
            )

            submitted = st.form_submit_button(
                "Save decision",
                type="primary",
            )

        if submitted:
            try:
                if not confirmed:
                    raise ValueError(
                        "Confirm your decision before saving."
                    )

                decision = (
                    "active"
                    if decision_label == "Approve"
                    else "rejected"
                )

                db.review_account(
                    user["id"],
                    selected_id,
                    decision,
                )

                st.session_state["flash"] = (
                    "Administrator application approved."
                    if decision == "active"
                    else "Administrator application rejected."
                )
                st.rerun()

            except ValueError as exc:
                st.error(str(exc))

with invitations_tab:
    st.subheader("Create an administrator invitation")
    st.write(
        "Invite an authorised person using a new email address. "
        "The invitation is valid only for that email and "
        "your healthcare centre."
    )

    with st.form("administrator_invitation", clear_on_submit=True):
        invited_email = st.text_input(
            "Applicant's email address",
            max_chars=254,
        )

        expiry_hours = st.number_input(
            "Invitation valid for (hours)",
            min_value=1,
            max_value=168,
            value=24,
            step=1,
        )

        create_invitation = st.form_submit_button(
            "Generate invitation",
            type="primary",
        )

    if create_invitation:
        try:
            code = db.issue_administrator_invitation(
                administrator_id=user["id"],
                email=invited_email,
                healthcare_center=user["healthcare_center"],
                expires_hours=int(expiry_hours),
            )

            st.success("Administrator invitation created.")
            st.write(
                "**Invited email:** "
                + invited_email.strip().lower()
            )
            st.write(
                "**Healthcare centre:** "
                + user["healthcare_center"]
            )
            st.code(code, language=None)
            st.warning(
                "Copy this code now and share it privately with "
                "the intended applicant. It will not be displayed "
                "again after this page refreshes."
            )
            st.caption(
                "No email has been sent. After registering with "
                "this code, the applicant still needs approval."
            )

            invitations = db.list_administrator_invitations(
                user["id"]
            )

        except ValueError as exc:
            st.error(str(exc))

    st.subheader("Invitations you issued")

    if invitations:
        st.dataframe(
            [
                {
                    "Email": invitation["email"],
                    "Healthcare centre": invitation["healthcare_center"],
                    "Status": invitation_status(invitation),
                    "Created": timestamp(invitation["created_at"]),
                    "Expires": timestamp(invitation["expires_at"]),
                }
                for invitation in invitations
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("You have not issued any invitations.")

    available = {
        invitation["id"]: invitation
        for invitation in invitations
        if invitation_status(invitation) == "Available"
    }

    if available:
        st.subheader("Revoke an unused invitation")

        invitation_id = st.selectbox(
            "Select an invitation",
            options=list(available),
            format_func=lambda selected_id: (
                available[selected_id]["email"]
                + " — expires "
                + timestamp(available[selected_id]["expires_at"])
            ),
            key="invitation_to_revoke",
        )

        with st.form(f"revoke_invitation_{invitation_id}"):
            confirm_revoke = st.checkbox(
                "I confirm this invitation should no longer be used."
            )

            revoke = st.form_submit_button("Revoke invitation")

        if revoke:
            try:
                if not confirm_revoke:
                    raise ValueError(
                        "Confirm before revoking the invitation."
                    )

                db.revoke_administrator_invitation(
                    user["id"],
                    invitation_id,
                )

                st.session_state["flash"] = "Invitation revoked."
                st.rerun()

            except ValueError as exc:
                st.error(str(exc))

with accounts_tab:
    st.subheader("Accounts at your healthcare centre")

    st.dataframe(
        [
            {
                "Name": account["full_name"],
                "Email": account["email"],
                "Role": ROLE_LABELS.get(
                    account["role"],
                    account["role"],
                ),
                "Status": account["account_status"].title(),
                "Registered": timestamp(account["created_at"]),
            }
            for account in accounts
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.caption(
        "Password hashes and session tokens are not displayed. "
        "Healthcare centre names entered by workers are self-declared."
    )

    manageable = {
        account["id"]: account
        for account in accounts
        if account["id"] != user["id"]
        and account["account_status"] in {"active", "suspended"}
    }

    if not manageable:
        st.info("No other active or suspended accounts to manage.")
    else:
        selected_account_id = st.selectbox(
            "Select an account to manage",
            options=list(manageable),
            format_func=lambda account_id: (
                manageable[account_id]["full_name"]
                + " — "
                + manageable[account_id]["email"]
            ),
            key="managed_account",
        )

        selected_account = manageable[selected_account_id]
        currently_active = (
            selected_account["account_status"] == "active"
        )

        action_label = (
            "Suspend account"
            if currently_active
            else "Restore account"
        )

        st.write(
            "**Role:** "
            + ROLE_LABELS[selected_account["role"]]
        )
        st.write(
            "**Current status:** "
            + selected_account["account_status"].title()
        )

        if currently_active:
            st.warning(
                "Suspending this account prevents sign-in and "
                "ends its existing sessions. Saved records are retained."
            )
        else:
            st.info(
                "Restoring this account allows the user to sign in again."
            )

        with st.form(f"manage_account_{selected_account_id}"):
            confirm_action = st.checkbox(
                "I confirm this account action is authorised."
            )

            perform_action = st.form_submit_button(
                action_label,
                type="primary",
            )

        if perform_action:
            try:
                if not confirm_action:
                    raise ValueError(
                        "Confirm the account action before saving."
                    )

                db.review_account(
                    user["id"],
                    selected_account_id,
                    "suspended" if currently_active else "active",
                )

                st.session_state["flash"] = (
                    "Account suspended."
                    if currently_active
                    else "Account restored."
                )
                st.rerun()

            except ValueError as exc:
                st.error(str(exc))