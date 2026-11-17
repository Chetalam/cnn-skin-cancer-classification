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
