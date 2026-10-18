import streamlit as st
import db
from ui import setup, flash, timestamp

user = setup("User Management")
if user["role"] != "system_administrator" or user.get("account_status") != "active":
    st.error("Only active System Administrators can manage accounts.")
    st.stop()
st.title("User Management")
st.write("Healthcare centre:", user["healthcare_center"])
st.caption("Manage access within your centre. Suspending or deactivating an account retains its saved records.")
flash()
try:
    accounts = db.list_accounts_for_review(user["id"])
except ValueError as exc:
    st.error(str(exc))
    st.stop()
roles = {"system_administrator":"System Administrator", "healthcare_worker":"Healthcare Worker"}
columns = st.columns(3)
for column, status in zip(columns, ["active", "suspended", "deactivated"]):
    column.metric(status.title() + " accounts", sum(a["account_status"] == status for a in accounts))
st.dataframe([{
    "Name": a["full_name"], "Email": a["email"],
    "Role": roles.get(a["role"], a["role"]),
    "Status": a["account_status"].title(),
    "Registered": timestamp(a["created_at"]),
    "Deactivated": timestamp(a["deactivated_at"]) if a.get("deactivated_at") else "—",
} for a in accounts], hide_index=True, use_container_width=True)
st.caption("Password hashes and session tokens are not displayed. Centre names remain self-declared.")
manageable = {a["id"]: a for a in accounts if a["id"] != user["id"]}
if not manageable:
    st.info("No other accounts to manage.")
else:
    selected = st.selectbox("Select an account", list(manageable), format_func=lambda key: manageable[key]["full_name"] + " — " + manageable[key]["email"])
    target = manageable[selected]
    active = target["account_status"] == "active"
    st.write("Current status:", target["account_status"].title())
    st.info("Suspend prevents access. Restore/reactivate permits sign-in again. Saved reviews are retained.")
    with st.form(f"manage_{selected}"):
        confirmed = st.checkbox("I confirm this account action is authorised.")
        submit = st.form_submit_button("Suspend account" if active else "Restore / reactivate account", type="primary")
    if submit:
        try:
            if not confirmed:
                raise ValueError("Confirm the account action first.")
            db.review_account(user["id"], selected, "suspended" if active else "active")
            st.session_state["flash"] = "Account suspended." if active else "Account restored. The user can sign in again."
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))