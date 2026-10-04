import streamlit as st
from ui import setup,disclaimer

setup('Help')
st.title('Help and project information')
disclaimer()
instructions,project=st.tabs(['Using the app','Project status'])
with instructions:
    st.markdown('''
    1. Open **Analyse Image** from the sidebar.
    2. Choose a de-identified JPG or PNG, up to 10 MB.
    3. Inspect the preview and optionally add an anonymous case reference.
    4. Agree to save the preview and click **Analyse image and save review**.
    5. Open **History** to view, export or delete your records.
    ''')
    st.write('Account settings let you update your name or change your password. Log out when finished.')
    st.caption('Refreshing the browser may require signing in again. Sessions expire after eight hours.')
with project:
    st.write('Target classes: Melanoma, Basal Cell Carcinoma (BCC), Squamous Cell Carcinoma (SCC).')
    st.write('Datasets: HAM10000 and PAD-UFES-20. Planned comparison: MobileNetV2, EfficientNetB0 and ResNet50.')
    st.success('Database setup, exploratory analysis and initial cleaning completed in Colab.')
    st.info('Remaining: grouped splitting, architecture-specific preprocessing, training, evaluation and model integration.')
    st.write('The local app database includes users, hashed sessions, cancer classes, image previews, result records, model metadata, audit events and imported dataset metadata.')
    st.caption('Email verification and email-based password recovery need a mail service and are not enabled. The 30% milestone covers the working interface and data preparation, not clinical validation.')