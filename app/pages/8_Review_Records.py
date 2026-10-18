import streamlit as st
import db
from ui import setup, flash, timestamp

user = setup("Review Records")
st.title("Review Records")
st.write("Create in Analyse Image, read your saved records here, update a case reference or delete a review.")
flash()
st.page_link("pages/2_Analyse_Image.py", label="Create a new review", icon="🔬")
rows = db.history(user["id"])
if not rows:
    st.info("No saved reviews yet.")
    st.stop()
st.dataframe([{
    "ID": r["id"], "Case reference": r["case_reference"] or "—",
    "File": r["file_name"], "Status": r["status"],
    "Saved": timestamp(r["uploaded_at"]),
} for r in rows], hide_index=True, use_container_width=True)
by_id = {r["id"]:r for r in rows}
selected = st.selectbox("Select your review", list(by_id), format_func=lambda key: str(key) + " — " + by_id[key]["file_name"])
row = by_id[selected]
thumbnail = db.get_thumbnail(user["id"], selected)
if thumbnail:
    st.image(thumbnail, width=240)
with st.form(f"update_review_{selected}"):
    reference = st.text_input("Case reference", value=row["case_reference"], max_chars=80)
    update = st.form_submit_button("Update case reference", type="primary")
if update:
    try:
        db.update_review(user["id"], selected, reference)
        st.session_state["flash"] = "Case reference updated."
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
st.warning("Deleting a review permanently removes its thumbnail and related prediction records. Your account remains saved.")
with st.form(f"delete_review_{selected}"):
    confirm = st.checkbox("Permanently delete this review.")
    delete = st.form_submit_button("Delete review")
if delete:
    try:
        if not confirm:
            raise ValueError("Confirm deletion first.")
        if not db.delete_review(user["id"], selected):
            raise ValueError("Review unavailable.")
        st.session_state["flash"] = "Review deleted."
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))