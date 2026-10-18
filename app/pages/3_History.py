import csv
import io
import streamlit as st
import db
from ui import setup, disclaimer, timestamp, flash

user = setup("History")
st.title("Your review history")
disclaimer()
flash()
rows = db.history(user["id"])
if not rows:
    st.info("No saved reviews yet.")
    st.page_link("pages/2_Analyse_Image.py", label="Upload your first image")
    st.stop()
display_rows = [{
    "Record": r["id"], "Case reference": r["case_reference"] or "—", "File": r["file_name"],
    "Status": "Awaiting model" if r["status"] == "awaiting_model" else "Predicted",
    "Class": r["cancer_class"] or "Unavailable",
    "Confidence": f"{r['confidence']:.1%}" if r["confidence"] is not None else "Unavailable",
    "Saved": timestamp(r["uploaded_at"]),
} for r in rows]
st.dataframe(display_rows, hide_index=True, use_container_width=True)
def safe_cell(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text
buffer = io.StringIO()
writer = csv.DictWriter(buffer, fieldnames=list(display_rows[0]))
writer.writeheader()
writer.writerows({k:safe_cell(v) for k,v in row.items()} for row in display_rows)
st.download_button("Download my history as CSV", buffer.getvalue(), "my_review_history.csv", "text/csv")
by_id = {r["id"]:r for r in rows}
selected = st.selectbox("Open a saved review", list(by_id), format_func=lambda key: f"Review #{key}")
row = by_id[selected]
left, right = st.columns(2)
with left:
    thumbnail = db.get_thumbnail(user["id"], selected)
    if thumbnail:
        st.image(thumbnail, caption="Stored preview", width=320)
with right:
    st.write("Status:", "Awaiting model" if row["status"] == "awaiting_model" else "Predicted")
    st.write("Original dimensions:", f"{row['width']} × {row['height']}")
    st.caption("Research record. No clinical diagnosis is implied.")
    confirm = st.checkbox("Delete this saved review and its preview permanently.", key=f"delete_{selected}")
    if st.button("Delete review", disabled=not confirm):
        try:
            if not db.delete_review(user["id"], selected):
                raise ValueError("Review unavailable.")
            st.session_state["flash"] = "Review deleted."
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))