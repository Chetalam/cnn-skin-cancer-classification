from translations import t, display_data, translated_format, language_selector
import streamlit as st
import db
from ui import setup
user = setup('Dataset Status')
st.title(t('Dataset and database status'))
st.write(t('Track the cleaned training manifest separately from uploaded application images.'))
summary = db.dataset_summary()
if summary:
    st.metric(t('Imported cleaned images'), sum((r['image_count'] for r in summary)))
    st.dataframe(display_data(summary), hide_index=True, use_container_width=True)
else:
    st.info(t('No cleaned manifest imported into the application database yet.'))
st.caption(t('Notebook result: 2,703 cleaned records (1,165 Melanoma, 1,353 BCC, 185 SCC). App totals are shown only after import.'))
if user['role'] == 'system_administrator':
    imports, health = st.tabs(display_data(['Import cleaned manifest', 'Database checks']))
    with imports:
        st.write(t('Download Datasets/Cleaned/clean_metadata.csv from your Gmail Drive, then select it here.'))
        manifest = st.file_uploader(t('Clean metadata CSV'), type=['csv'], key='pages/5_Dataset_Status.py:20:file_uploader')
        confirmed = st.checkbox(t('Replace the app’s previous manifest with this file. Original datasets and skin_cancer.db stay unchanged.'), key='pages/5_Dataset_Status.py:21:checkbox')
        if st.button(t('Import manifest'), type='primary', disabled=manifest is None or not confirmed, key='pages/5_Dataset_Status.py:22:button'):
            try:
                total = db.import_manifest(user['id'], manifest.getvalue())
                st.success(t(f'Imported {total:,} verified metadata rows. Refresh this page to see the updated totals.'))
            except (ValueError, UnicodeError) as exc:
                st.error(t(str(exc)))
        st.caption(t('Import validates metadata and unique hashes. It cannot verify Drive image paths from your Windows computer and does not copy images.'))
    with health:
        report = db.database_health(user['id'])
        if report['integrity'] == 'ok' and (not report['foreign_key_errors']) and report['foreign_keys_enabled']:
            st.success(t('SQLite integrity and foreign-key checks passed.'))
        else:
            st.error(t('Database checks need investigation.'))
        st.write(t('Schema version:'), report['schema_version'])
        st.dataframe(display_data([{'Table': t, 'Rows': n} for t, n in report['counts'].items()]), hide_index=True, use_container_width=True)
        st.caption(t('The model tables remain empty until trained models are registered. Pending reviews correctly contain no class or confidence.'))
else:
    st.info(t('Only the project system_administrator can import datasets or inspect database internals.'))
