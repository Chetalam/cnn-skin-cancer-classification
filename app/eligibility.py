"""Explicit human scope check; not an automated benign/normal detector."""
import streamlit as st
from translations import t

OPTIONS = ['Not assessed / unsure', 'Normal skin / no lesion',
           'Benign-looking lesion / another condition', 'Clinically suspected BCC, Melanoma or SCC']

def scope_control(digest):
    choice = st.radio(t('Clinical scope assessment'), OPTIONS, format_func=t, key='image_scope_' + digest)
    st.caption(t('A visible lesion can be benign. This three-class model has no normal or benign class. This check records your assessment; it is not automatic detection.'))
    if choice != OPTIONS[-1]:
        st.info(t('Classification is blocked for this assessment. You can save the review without a prediction and arrange clinical assessment.'))
    return choice == OPTIONS[-1]
