"""Image-bound acknowledgement for an experimental three-class model.

The worker, not the software, judges whether a lesion is visible. This is
not an automatic normal-skin, benign-lesion or cancer detector.
"""
import streamlit as st
from translations import t

LIMITATION = (
    'A visible skin lesion is not necessarily cancer. This model only '
    'classifies BCC, Melanoma and SCC; it cannot identify normal skin '
    'or benign lesions.'
)
ACKNOWLEDGEMENT = (
    'I understand this three-class limitation and that the result is not a diagnosis.'
)


def classification_allowed(visibility, acknowledged):
    """Require a visible lesion AND an explicit Boolean acknowledgement."""
    return visibility == 'Yes' and acknowledged is True


def acknowledgement_control(digest):
    """Show one acknowledgement only for a worker who selected Yes.

    The checkbox key binds consent to the exact uploaded image; uploading
    another image creates a new, unchecked control.
    """
    st.info(t(LIMITATION))
    return st.checkbox(t(ACKNOWLEDGEMENT), key='lesion_limitation_ack_' + digest)


def lesion_checks(key):
    limitation_acknowledged = False
    # Bind this answer to the image digest so it cannot carry over to another upload.
    visibility = st.radio(
        t('Can you clearly identify a skin lesion in this image?'),
        options=['Not sure', 'No lesion / normal skin', 'Yes'],
        format_func=t,
        key='lesion_visibility_' + key,
    )
    st.caption(t('This is your visual assessment. The current model cannot automatically detect normal skin, benign lesions, or unrelated images.'))
    if visibility == 'No lesion / normal skin':
        st.warning(t('You indicated that no lesion is visible. Classification is blocked. Upload a clear lesion image to analyse.'))
    elif visibility == 'Not sure':
        st.info(t('Lesion visibility is uncertain. Classification is blocked; obtain a clearer image or qualified review.'))
    elif visibility == 'Yes':
        limitation_acknowledged = acknowledgement_control(key)
    return visibility, limitation_acknowledged
