import secrets
import streamlit as st
import db
from images import validate_image
from ui import setup, disclaimer

user = setup("Analyse Image")
st.title("Analyse a skin lesion image")
disclaimer()
left, right = st.columns(2, gap="large")
image = None
digest = None
with left:
    st.subheader("1. Upload and preview")
    upload = st.file_uploader("Choose a JPG or PNG image", type=["jpg", "jpeg", "png"])
    st.caption("Maximum 10 MB and 20 million pixels. Use a de-identified image.")
    if upload:
        try:
            image, digest = validate_image(upload.getvalue())
            if st.session_state.get("upload_digest") != digest:
                st.session_state["upload_digest"] = digest
                st.session_state["review_key"] = secrets.token_urlsafe(24)
                st.session_state.pop("saved_review", None)
            st.image(image, use_column_width=True)
            st.caption(f"{image.width} × {image.height} pixels · {upload.size / 1024:.1f} KB")
            st.success("Image is readable.")
        except ValueError as exc:
            image = None
            st.error(str(exc))
    else:
        for key in ["upload_digest", "review_key", "saved_review"]:
            st.session_state.pop(key, None)
        st.info("Choose an image to begin.")
with right:
    st.subheader("2. Save a review")
    reference = st.text_input("Optional case reference", max_chars=80, help="Use an anonymous reference, not a patient name or ID.")
    consent = st.checkbox("Save a small preview and file metadata in my history.")
    st.caption("The original image is not stored. A preview up to 320 × 320 pixels is retained when saved.")
    if st.button("Save review", type="primary", disabled=image is None or not consent, use_container_width=True):
        try:
            st.session_state["saved_review"] = db.save_review(user["id"], st.session_state["review_key"], reference, upload.name, image, digest)
        except ValueError as exc:
            st.error(str(exc))
    if image is not None and st.session_state.get("saved_review"):
        st.success("Review saved to your history.")
        st.info("Awaiting model integration. Classification was not performed.")
        st.page_link("pages/3_History.py", label="View saved history")
    else:
        st.info("Predictions remain unavailable until model integration.")
    st.caption("Readability validation cannot confirm that the image depicts a skin lesion.")