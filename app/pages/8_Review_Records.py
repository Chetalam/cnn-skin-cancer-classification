from translations import t, display_data, translated_format, language_selector
import streamlit as st
import db
from ui import setup, flash, timestamp
user = setup('Review Records')
st.title(t('Review Records'))
st.write(t('Create in Analyse Image, read your saved records here, update a case reference or delete a review.'))
flash()
st.page_link('pages/2_Analyse_Image.py', label=t('Create a new review'), icon='🔬')
rows = db.history(user['id'])
if not rows:
    st.info(t('No saved reviews yet.'))
    st.stop()
st.dataframe(display_data([{'ID': r['id'], 'Case reference': r['case_reference'] or '—', 'File': r['file_name'], 'Status': r['status'], 'Saved': timestamp(r['uploaded_at'])} for r in rows]), hide_index=True, use_container_width=True)
by_id = {r['id']: r for r in rows}
selected = st.selectbox(t('Select your review'), list(by_id), format_func=translated_format(lambda key: str(key) + ' — ' + by_id[key]['file_name']), key='pages/8_Review_Records.py:20:selectbox')
row = by_id[selected]
thumbnail = db.get_thumbnail(user['id'], selected)
if thumbnail:
    st.image(thumbnail, width=240)
with st.form(f'update_review_{selected}'):
    reference = st.text_input(t('Case reference'), value=row['case_reference'], max_chars=80, key='pages/8_Review_Records.py:26:text_input')
    update = st.form_submit_button(t('Update case reference'), type='primary')
if update:
    try:
        db.update_review(user['id'], selected, reference)
        st.session_state['flash'] = 'Case reference updated.'
        st.rerun()
    except ValueError as exc:
        st.error(t(str(exc)))
st.warning(t('Deleting a review permanently removes its thumbnail and related prediction records. Your account remains saved.'))
with st.form(f'delete_review_{selected}'):
    confirm = st.checkbox(t('Permanently delete this review.'), key='pages/8_Review_Records.py:37:checkbox')
    delete = st.form_submit_button(t('Delete review'))
if delete:
    try:
        if not confirm:
            raise ValueError('Confirm deletion first.')
        if not db.delete_review(user['id'], selected):
            raise ValueError('Review unavailable.')
        st.session_state['flash'] = 'Review deleted.'
        st.rerun()
    except ValueError as exc:
        st.error(t(str(exc)))
