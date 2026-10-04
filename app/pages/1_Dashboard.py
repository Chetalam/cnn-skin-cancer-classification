import streamlit as st
import db
from ui import setup, flash, timestamp


user = setup("Dashboard")

st.title("Your dashboard")
st.write("Welcome back, " + user["full_name"] + ".")

role_labels = {
    "system_administrator": "System Administrator",
    "healthcare_worker": "Healthcare Worker",
}

role_column, centre_column = st.columns(2)

with role_column:
    st.write(
        "**Account role:** "
        + role_labels.get(user["role"], "Unknown")
    )

with centre_column:
    st.write(
        "**Healthcare centre:** "
        + (user.get("healthcare_center") or "Not provided")
    )

flash()

rows = db.history(user["id"])
summary = db.dataset_summary()

col1, col2, col3 = st.columns(3)

col1.metric("Your saved reviews", len(rows))

col2.metric(
    "Completed predictions",
    sum(row["status"] == "predicted" for row in rows),
)

col3.metric(
    "Imported dataset images",
    sum(row["image_count"] for row in summary),
)

st.subheader("Start a review")
st.write(
    "Upload a lesion image, check the preview "
    "and save it to your history."
)

st.page_link(
    "pages/2_Analyse_Image.py",
    label="Open Analyse Image",
    icon="🔬",
)

st.info(
    "The CNN is not integrated. Saved reviews have the status "
    "“Awaiting model”, with no predicted class or confidence."
)

st.subheader("Recent activity")

if rows:
    recent_activity = [
        {
            "Case reference": row["case_reference"] or "—",
            "File": row["file_name"],
            "Status": (
                "Awaiting model"
                if row["status"] == "awaiting_model"
                else "Predicted"
            ),
            "Saved": timestamp(row["uploaded_at"]),
        }
        for row in rows[:5]
    ]

    st.dataframe(
        recent_activity,
        hide_index=True,
        use_container_width=True,
    )
else:
    st.write(
        "No reviews yet. Your first saved image will appear here."
    )