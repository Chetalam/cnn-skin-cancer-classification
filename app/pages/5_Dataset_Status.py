import streamlit as st
import db
from ui import setup

user=setup('Dataset Status')
st.title('Dataset and database status')
st.write('Track the cleaned training manifest separately from uploaded application images.')
summary=db.dataset_summary()
if summary:
    st.metric('Imported cleaned images',sum(r['image_count'] for r in summary))
    st.dataframe(summary,hide_index=True,use_container_width=True)
else:
    st.info('No cleaned manifest imported into the application database yet.')
st.caption('Notebook result: 2,703 cleaned records (1,165 Melanoma, 1,353 BCC, 185 SCC). App totals are shown only after import.')

if user['role']=='system_administrator':
    imports,health=st.tabs(['Import cleaned manifest','Database checks'])
    with imports:
        st.write('Download Datasets/Cleaned/clean_metadata.csv from your Gmail Drive, then select it here.')
        manifest=st.file_uploader('Clean metadata CSV',type=['csv'])
        confirmed=st.checkbox('Replace the app’s previous manifest with this file. Original datasets and skin_cancer.db stay unchanged.')
        if st.button('Import manifest',type='primary',disabled=manifest is None or not confirmed):
            try:
                total=db.import_manifest(user['id'],manifest.getvalue())
                st.success(f'Imported {total:,} verified metadata rows. Refresh this page to see the updated totals.')
            except (ValueError,UnicodeError) as exc:
                st.error(str(exc))
        st.caption('Import validates metadata and unique hashes. It cannot verify Drive image paths from your Windows computer and does not copy images.')
    with health:
        report=db.database_health(user['id'])
        if report['integrity']=='ok' and not report['foreign_key_errors'] and report['foreign_keys_enabled']:
            st.success('SQLite integrity and foreign-key checks passed.')
        else:
            st.error('Database checks need investigation.')
        st.write('Schema version:',report['schema_version'])
        st.dataframe([{'Table':t,'Rows':n} for t,n in report['counts'].items()],hide_index=True,use_container_width=True)
        st.caption('The model tables remain empty until trained models are registered. Pending reviews correctly contain no class or confidence.')
else:
    st.info('Only the project system_administrator can import datasets or inspect database internals.')