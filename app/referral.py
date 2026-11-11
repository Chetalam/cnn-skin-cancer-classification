"""Referral guidance for healthcare workers, independent of model scores."""
import streamlit as st

from translations import t

TITLE = "What to do next: assessment and referral"
NOTICE = "Use your clinical assessment and local referral protocol. The model cannot confirm or rule out cancer, choose treatment, or set referral urgency."
SCC_LIMITATION = "SCC limitation: SCC detection was weaker in project evaluations. Any predicted class or model score must not be used to exclude SCC or replace clinical assessment."
STEPS = (
    "Assess and document. Examine the lesion and record its location, duration, changes and symptoms in the clinical record.",
    "Arrange assessment or referral. If you suspect skin cancer or are unsure, follow your local protocol and refer to a facility with dermatology or skin-cancer assessment services. Confirm the receiving facility can assess the patient; it can arrange cancer-specialist care if needed. If travel is difficult, seek advice through an approved phone or remote service. Do not delay referral while waiting for a model result.",
    "Explain and follow up. Tell the patient where to go and when, record the referral plan in the clinical record, and agree who will check whether the patient was seen.",
)
DOWNLOAD = "Download referral checklist for offline use"
HANDOVER = "Blank handover fields — complete in your approved clinical record"
FIELDS = (
    "Clinical findings and reason for referral",
    "Receiving facility or clinician and contact",
    "Urgency and appointment per local protocol",
    "Follow-up owner and date",
)


def checklist_text():
    """Return a printable blank checklist without patient or model data."""
    lines = [t(TITLE), "", t(NOTICE), "", t(SCC_LIMITATION), ""]
    lines.extend(f"{i}. {t(step)}" for i, step in enumerate(STEPS, 1))
    lines.extend(("", t(HANDOVER)))
    lines.extend(f"{t(field)}: ____________________" for field in FIELDS)
    return "\n".join(lines) + "\n"


def show_referral_guidance(key):
    st.subheader(t(TITLE))
    st.info(t(NOTICE))
    st.warning(t(SCC_LIMITATION))
    for number, step in enumerate(STEPS, 1):
        st.write(f"{number}. {t(step)}")
    st.download_button(
        t(DOWNLOAD), checklist_text(), "referral_checklist.txt",
        mime="text/plain; charset=utf-8", key=key,
    )
