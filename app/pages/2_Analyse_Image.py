import secrets
import streamlit as st
import db
from images import validate_image
from inference import inspect_package, predict_image
from translations import t
from ui import setup, disclaimer

user = setup('Analyse Image')
st.title(t('Analyse a skin lesion image'))
disclaimer()
st.warning(t('Experimental model: SCC performance and darker-skin reliability requirements are not met. Scores are not a diagnosis or a calibrated cancer risk.'))
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
            st.image(image, use_container_width=True)
            st.caption(t('Preview orientation may follow EXIF metadata. Inference uses the original orientation to match training.'))
        except ValueError as exc:
            st.error(t(str(exc)))
    else:
        for key in ['upload_digest', 'review_key', 'saved_review']:
            st.session_state.pop(key, None)
with right:
    reference = st.text_input(t('Optional case reference'), max_chars=80)
    consent = st.checkbox(t('Save a small preview and file metadata in my history.'))
    st.caption(t('The original image is not stored. A preview up to 320 × 320 pixels is retained when saved.'))
    analyse = st.button(t('Analyse and save'), type='primary', disabled=image is None or not consent or not model_ready)
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
                        result = predict_image(raw)
                        db.record_prediction(user['id'], image_id, digest, result)
        except ValueError as exc:
            st.error(t(str(exc)))
    if image is not None and st.session_state.get('saved_review'):
        result = db.prediction_detail(user['id'], st.session_state['saved_review'])
        st.success(t('Review saved to your history.'))
        if result['status'] == 'predicted':
            st.metric(t('Predicted class'), result['cancer_class'])
            st.metric(t('Model score'), f"{result['confidence']:.1%}")
            st.bar_chart({t('Model score'): result['scores']})
            st.caption(t('Model version') + ': ' + result['model_name'])
        else:
            st.info(t('Saved without a prediction. Upload the original image again to analyse it.'))
        st.page_link('pages/3_History.py', label=t('View saved history'))
    st.caption(t('Readability validation cannot confirm that the image depicts a skin lesion.'))
