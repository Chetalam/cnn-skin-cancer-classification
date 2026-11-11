"""Referral guidance for healthcare workers, independent of model scores."""
import streamlit as st
import math
from datetime import datetime, timezone

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


def checklist_text(prediction):
    """Attach the owned, saved prediction; never infer again for a download."""
    labels = ('BCC', 'Melanoma', 'SCC')
    scores = prediction.get('scores', {})
    if prediction.get('status') != 'predicted' or prediction.get('cancer_class') not in labels:
        raise ValueError('A saved prediction is required for this referral checklist.')
    if set(scores) != set(labels) or any(not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in scores.values()):
        raise ValueError('Saved prediction scores are incomplete.')
    if not prediction.get('model_name') or not prediction.get('created_at'):
        raise ValueError('Saved model version or prediction date is missing.')
    clean = lambda value: ' '.join(str(value).split())
    saved_at = datetime.fromtimestamp(prediction['created_at'], timezone.utc).strftime('%d %b %Y, %H:%M UTC')
    lines = [t(TITLE), '', t('Saved prediction — decision support only'),
             f"{t('Review ID')}: {prediction['image_id']}",
             f"{t('Case reference')}: {clean(prediction.get('case_reference') or '—')}",
             f"{t('Prediction saved')}: {saved_at}",
             f"{t('Predicted class')}: {prediction['cancer_class']}",
             f"{t('Model score')}: {prediction['confidence']:.1%}",
             f"{t('Model version')}: {clean(prediction['model_name'])}", '', t('All class scores')]
    lines.extend(f"{label}: {scores[label]:.1%}" for label in labels)
    lines.extend(('', t('Model scores are uncalibrated and do not represent diagnostic accuracy.'), '', t(NOTICE), '', t(SCC_LIMITATION), ''))
    lines.extend(f"{i}. {t(step)}" for i, step in enumerate(STEPS, 1))
    lines.extend(("", t(HANDOVER)))
    lines.extend(f"{t(field)}: ____________________" for field in FIELDS)
    return "\n".join(lines) + "\n"


def show_referral_guidance(key, prediction):
    st.subheader(t(TITLE))
    st.info(t(NOTICE))
    st.warning(t(SCC_LIMITATION))
    for number, step in enumerate(STEPS, 1):
        st.write(f"{number}. {t(step)}")
    try:
        text = checklist_text(prediction)
    except ValueError as exc:
        st.error(t(str(exc)))
        return
    st.download_button(
        t(DOWNLOAD), text, f"referral_review_{int(prediction['image_id'])}.txt",
        mime="text/plain; charset=utf-8", key=key,
    )
