import streamlit as st
import db

from translations import t, display_data
from ui import setup


user = setup("Database Guide")

if (
    user["role"] != "system_administrator"
    or user.get("account_status") != "active"
):
    st.error(
        t("Only active administrators can view database health.")
    )
    st.stop()

st.title(t("Database Guide"))

st.write(
    t(
        "The app database stores accounts, sessions, saved reviews "
        "and imported dataset metadata. The Colab training "
        "database is a separate file."
    )
)

st.subheader(t("Create, Read, Update, Delete"))

crud_steps = [
    {
        "Action": "Create",
        "Meaning": "Add a record",
        "In the app": "Register an account or save an image review",
    },
    {
        "Action": "Read",
        "Meaning": "View saved records",
        "In the app": "Open your history or view account details",
    },
    {
        "Action": "Update",
        "Meaning": "Change a record",
        "In the app": (
            "Edit your profile, change a case reference, "
            "deactivate or restore access"
        ),
    },
    {
        "Action": "Delete",
        "Meaning": "Permanently remove a record",
        "In the app": (
            "Delete your own review and its related prediction records"
        ),
    },
]

st.table(display_data(crud_steps))

st.info(
    t(
        "Deactivation is Update, not Delete. "
        "The account and its reviews remain saved."
    )
)

st.subheader(t("What the tables mean"))

table_descriptions = [
    {
        "Table": "users",
        "Purpose": (
            "Profiles, roles, account status and salted password hashes"
        ),
    },
    {
        "Table": "sessions",
        "Purpose": "Hashed sign-in tokens and expiry times",
    },
    {
        "Table": "login_attempts",
        "Purpose": "Failed sign-in counts and temporary lockouts",
    },
    {
        "Table": "skin_lesion_images",
        "Purpose": (
            "Review ownership, filenames, case references and thumbnails"
        ),
    },
    {
        "Table": "prediction_results / prediction_scores",
        "Purpose": "Review status and model results when integrated",
    },
    {
        "Table": "model_versions / cancer_classes",
        "Purpose": "Model descriptions and supported classes",
    },
    {
        "Table": "dataset_imports / dataset_images",
        "Purpose": "Imported clean metadata and import history",
    },
    {
        "Table": "audit_events",
        "Purpose": "Timestamped account and review actions",
    },
    {
        "Table": "schema_version",
        "Purpose": "Database migration versions",
    },
]

st.table(display_data(table_descriptions))

health = db.database_health(user["id"])

st.subheader(t("Current database checks"))

st.write(
    t("Integrity:"),
    t(health["integrity"]),
)

st.write(
    t("Relationship errors:"),
    len(health["foreign_key_errors"]),
)

st.write(
    t("Foreign keys enabled:"),
    t(str(health["foreign_keys_enabled"])),
)

st.write(
    t("Schema version:"),
    health["schema_version"],
)

st.dataframe(
    display_data(
        [
            {
                "Table": name,
                "Saved rows": count,
            }
            for name, count in health["counts"].items()
        ]
    ),
    hide_index=True,
    use_container_width=True,
)

st.caption(
    t(
        "No password hashes, session tokens or other users' "
        "review content are displayed here."
    )
)