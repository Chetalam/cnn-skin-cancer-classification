from translations import t, display_data, translated_format, language_selector
import csv
import io
import streamlit as st
import db
from referral import show_referral_guidance
from ui import setup, disclaimer, timestamp, flash
from review_actions import review_view, archive_controls
user = setup('Reviews')
st.title(t('Reviews'))
disclaimer()
flash()
st.page_link('pages/2_Analyse_Image.py', label=t('Create a new review'), icon='🔬')
view = review_view('history_view')
rows = db.history(user['id'], view=view)
if not rows:
    st.info(t('No reviews in this view.'))
    st.page_link('pages/2_Analyse_Image.py', label=t('Upload your first image'))
    st.stop()
display_rows = [{'Record': r['id'], 'Case reference': r['case_reference'] or '—', 'File': r['file_name'], 'Status': 'Awaiting model' if r['status'] == 'awaiting_model' else 'Predicted', 'Class': r['cancer_class'] or 'Unavailable', 'Model score': f"{r['confidence']:.1%}" if r['confidence'] is not None else 'Unavailable', 'Saved': timestamp(r['uploaded_at']), 'Archive state': t('Archived' if r['archived_at'] is not None else 'Active')} for r in rows]
st.dataframe(display_data(display_rows), hide_index=True, use_container_width=True)

def safe_cell(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text
buffer = io.StringIO()
writer = csv.DictWriter(buffer, fieldnames=list(display_rows[0]))
writer.writeheader()
writer.writerows(({k: safe_cell(v) for k, v in row.items()} for row in display_rows))
st.download_button(t('Download reviews as CSV'), buffer.getvalue(), 'my_reviews.csv', 'text/csv', key='pages/3_History.py:31:download_button')
by_id = {r['id']: r for r in rows}
selected = st.selectbox(t('Open a saved review'), list(by_id), format_func=translated_format(lambda key: f'Review #{key}'), key='history_selection_'+view)
row = by_id[selected]
left, right = st.columns(2)
with left:
    thumbnail = db.get_thumbnail(user['id'], selected)
    if thumbnail:
        st.image(thumbnail, caption=t('Stored preview'), width=320)
with right:
    st.write(t('Status:'), 'Awaiting model' if row['status'] == 'awaiting_model' else 'Predicted')
    st.write(t('Original dimensions:'), f"{row['width']} × {row['height']}")
    st.caption(t('Research record. No clinical diagnosis is implied.'))
    if row['archived_at'] is None:
        with st.form(f'update_review_{selected}'):
            reference = st.text_input(t('Case reference'), value=row['case_reference'] or '', max_chars=80)
            update = st.form_submit_button(t('Update case reference'), type='primary')
        if update:
            try:
                db.update_review(user['id'], selected, reference)
                st.session_state['flash'] = 'Case reference updated.'
                st.rerun()
            except ValueError as exc:
                st.error(t(str(exc)))
    archive_controls(user['id'], row, 'history_'+str(selected))

if row['status'] == 'predicted':
    detail = db.prediction_detail(user['id'], selected)
    st.caption(t('Model version') + ': ' + detail['model_name'])
    st.bar_chart({t('Model score'): detail['scores']})
    st.caption(t('Model scores are uncalibrated and do not represent diagnostic accuracy.'))
    show_referral_guidance('history_referral_checklist', detail)
