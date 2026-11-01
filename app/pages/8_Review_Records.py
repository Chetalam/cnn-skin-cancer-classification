import streamlit as st
import db
from translations import t, display_data
from ui import setup, flash, timestamp
from review_actions import review_view, archive_controls

user = setup('Review Records')
st.title(t('Review Records'))
st.write(t('View and update your reviews, or archive and restore them without deleting saved data.'))
flash()
st.page_link('pages/2_Analyse_Image.py', label=t('Create a new review'), icon='🔬')
view = review_view('records_view')
rows = db.history(user['id'], view=view)
if not rows:
    st.info(t('No reviews in this view.'))
    st.stop()
st.dataframe(display_data([{
    'ID': r['id'], 'Case reference':r['case_reference'] or '—',
    'File':r['file_name'], 'Status':r['status'],
    'Archive state':t('Archived' if r['archived_at'] is not None else 'Active'),
    'Saved':timestamp(r['uploaded_at']),
} for r in rows]), hide_index=True, use_container_width=True)
by_id = {r['id']:r for r in rows}
selected = st.selectbox(t('Select your review'), list(by_id),
    format_func=lambda key: str(key)+' — '+by_id[key]['file_name'], key='record_selection_'+view)
row = by_id[selected]
thumbnail = db.get_thumbnail(user['id'],selected)
if thumbnail:
    st.image(thumbnail,width=240)
if row['archived_at'] is None:
    with st.form(f'update_review_{selected}'):
        reference = st.text_input(t('Case reference'),value=row['case_reference'] or '',max_chars=80)
        update = st.form_submit_button(t('Update case reference'),type='primary')
    if update:
        try:
            db.update_review(user['id'],selected,reference)
            st.session_state['flash']='Case reference updated.'
            st.rerun()
        except ValueError as exc:
            st.error(t(str(exc)))
archive_controls(user['id'],row,'records_'+str(selected))
