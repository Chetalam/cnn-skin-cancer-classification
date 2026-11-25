import secrets
import streamlit as st
import db
from referral import show_referral_guidance
from images import validate_image
from inference import inspect_package, predict_image
from translations import t
from ui import setup, disclaimer
from eligibility import lesion_checks, classification_allowed
from explanation_view import show_explanation

user = setup('Analyse Image')
st.title(t('Analyse a skin lesion image'))
disclaimer()
st.warning(t('Experimental model. Scores are not a diagnosis or a calibrated cancer risk.'))
try:
    _, model_metadata, _ = inspect_package()
    model_ready = True
    st.caption(t('Active model') + ': ' + model_metadata['model_name'] + ' / ' + model_metadata['run_id'])
except ValueError as exc:
    model_ready = False
    st.info(t(str(exc)))

left, right = st.columns(2, gap='large')
image = None
with left:
    upload = st.file_uploader(t('Choose a JPG or PNG image'), type=['jpg', 'jpeg', 'png'])
    if upload:
        try:
            raw = upload.getvalue()
            image, digest = validate_image(raw)
            if st.session_state.get('upload_digest') != digest:
                st.session_state['upload_digest'] = digest
                st.session_state['review_key'] = secrets.token_urlsafe(24)
                st.session_state.pop('saved_review', None)
            st.image(image, width='stretch')
            st.caption(t('Preview orientation may follow EXIF metadata. Inference uses the original orientation to match training.'))
        except ValueError as exc:
            st.error(t(str(exc)))
    else:
        for key in ['upload_digest', 'review_key', 'saved_review']:
            st.session_state.pop(key, None)
with right:
    visibility, limitation_acknowledged = lesion_checks(digest) if image is not None else (None, False)
    visibility_confirmed = visibility == 'Yes'
    classification_ready = classification_allowed(visibility, limitation_acknowledged)
    reference = st.text_input(t('Optional case reference'), max_chars=80)
    consent = st.checkbox(t('Save a small preview and file metadata in Reviews.'))
    st.caption(t('The original image is not stored. A preview up to 320 × 320 pixels is retained when saved.'))
    analyse = st.button(t('Analyse and save'), type='primary', disabled=not classification_ready or not consent or not model_ready)
    save_only = st.button(t('Save without prediction'), disabled=image is None or not consent)
    if analyse or save_only:
        try:
            # Prediction failure does not turn into a fabricated result; the saved review stays pending.
            image_id = db.save_review(user['id'], st.session_state['review_key'], reference, upload.name, image, digest)
            st.session_state['saved_review'] = image_id
            if analyse:
                with st.spinner(t('Analysing image...')):
                    existing = db.prediction_detail(user['id'], image_id)
                    if existing['status'] != 'predicted':
                        result = predict_image(raw, lesion_confirmed=visibility_confirmed, limitation_acknowledged=limitation_acknowledged)
                        db.record_prediction(user['id'], image_id, digest, result)
        except ValueError as exc:
            st.error(t(str(exc)))

# Render saved results across the page, outside the upload/control columns.
if image is not None and st.session_state.get('saved_review'):
    result = db.prediction_detail(user['id'], st.session_state['saved_review'])
    st.divider()
    st.success(t('Review saved in Reviews.'))
    if result['status'] == 'predicted' and classification_ready:
        class_column, score_column = st.columns(2, gap='large')
        class_column.metric(t('Predicted class'), result['cancer_class'])
        score_column.metric(t('Model score'), f"{result['confidence']:.1%}")
        st.bar_chart({t('Model score'): result['scores']})
        st.caption(t('Model version') + ': ' + result['model_name'])
        explanation = show_explanation(result, raw=raw, key='analysis')
        show_referral_guidance('analysis_referral_checklist', result, explanation=explanation)
    elif result['status'] == 'predicted':
        st.info(t('A historical prediction is saved in Reviews. It does not establish that a lesion is present.'))
    else:
        st.info(t('Saved without a prediction. To finish this review later, open Reviews, choose Awaiting prediction and upload the original file.'))
    st.page_link('pages/3_History.py', label=t('View Reviews'))
