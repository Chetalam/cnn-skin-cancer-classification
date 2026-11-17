import streamlit as st
from translations import t
from explainability import (
    explain_saved_image, validate_explanation, LIMITATION,
    COLOUR_GUIDE_TITLE, COLOUR_GUIDE_INTRO, COLOUR_GUIDE_RED,
    COLOUR_GUIDE_BLUE, COLOUR_GUIDE_STRENGTH,
    COLOUR_GUIDE_EXAMPLE, COLOUR_GUIDE_CAUTION,
)


def show_explanation(prediction, raw=None, *, key):
    st.subheader(t('Visual explanation'))
    st.write(t(COLOUR_GUIDE_INTRO))
    st.caption(t('Optional: this requires extra model runs and may take a few minutes on CPU.'))
    if raw is None:
        upload = st.file_uploader(t('Upload the original image to explain this saved review'), type=['jpg','jpeg','png'], key=key+'_explanation_original')
        raw = upload.getvalue() if upload else None
        st.caption(t('The stored preview cannot be used. The image and model must match the saved review exactly.'))
    identity = (prediction['image_id'], prediction['model_name'], prediction.get('image_sha256'))
    if st.button(t('Generate visual explanation'), disabled=raw is None, key=key+'_explain'):
        st.session_state.pop('current_explanation', None)
        try:
            with st.spinner(t('Checking image, model and region scores...')):
                result = explain_saved_image(raw, prediction, prediction.get('image_sha256'))
                st.session_state['current_explanation'] = (identity, result)
        except ValueError as exc:
            st.error(t(str(exc)))
        except Exception:
            st.error(t('The explanation could not be generated. Check the installed model and environment. The saved prediction was not changed.'))
    cached = st.session_state.get('current_explanation')
    if not cached or cached[0] != identity:
        return None
    result = cached[1]
    validate_explanation(result, prediction)
    left, right = st.columns(2)
    left.image(result['original'], caption=t('Original model input'), use_container_width=True)
    right.image(result['overlay'], caption=t('Regions affecting the predicted-class score'), use_container_width=True)
    st.markdown('**' + t(COLOUR_GUIDE_TITLE) + '**')
    st.write(t(COLOUR_GUIDE_RED))
    st.write(t(COLOUR_GUIDE_BLUE))
    st.caption(t(COLOUR_GUIDE_STRENGTH))
    st.caption(t(COLOUR_GUIDE_EXAMPLE))
    st.warning(t(COLOUR_GUIDE_CAUTION))
    a, b = st.columns(2)
    a.metric(t('Largest score decrease'), f"{max(0, result['regions'][0]['drop_pp']):.2f} pp")
    b.metric(t('Largest score increase'), f"{max(0, -result['regions'][-1]['drop_pp']):.2f} pp")
    st.caption(t('pp means percentage points, not a change in cancer risk.'))
    if result['max_abs_pp'] < .01:
        st.info(t('Masking produced no meaningful score change at this grid size. No regions are highlighted.'))
    with st.expander(t('View all region score changes')):
        st.dataframe([{t('Row'):r['row'],t('Column'):r['column'],t('Score decrease (pp)'):r['drop_pp']} for r in result['regions']], hide_index=True)
    st.warning(t(LIMITATION))
    return result
