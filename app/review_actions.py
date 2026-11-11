"""Reversible archive and restore controls for the Reviews page."""
import streamlit as st
import db
from translations import t
from ui import timestamp


def review_view(key):
    return st.radio(t('Show reviews'), options=['active', 'archived', 'all'],
                    format_func=lambda value: t({'active':'Active reviews','archived':'Archived reviews','all':'All reviews'}[value]), key=key, horizontal=True)


def archive_controls(user_id, row, key):
    if row['archived_at'] is not None:
        st.info(t('This review is archived. Its preview and predictions remain saved.'))
        st.caption(t('Archived on') + ': ' + timestamp(row['archived_at']))
        if st.button(t('Restore review'), key=key+'_restore'):
            if db.restore_review(user_id, row['id']):
                st.session_state['flash'] = 'Review restored.'
                st.rerun()
    else:
        st.info(t('Archiving hides this review from your active list. Its preview, predictions and model version remain in the database. You can restore it later.'))
        confirm = st.checkbox(t('Move this review to the archive.'), key=key+'_confirm')
        if st.button(t('Archive review'), disabled=not confirm, key=key+'_archive'):
            if db.archive_review(user_id, row['id']):
                st.session_state['flash'] = 'Review archived. All saved data was retained.'
                st.rerun()
