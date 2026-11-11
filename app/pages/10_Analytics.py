import pandas as pd
import streamlit as st

import db
from analytics_view import date_filters, render_activity, render_evaluation, timestamps, valid_class_report
from inference import evaluation_metrics, inspect_package
from translations import t
from ui import setup

user = setup('Analytics')
st.title(t('Analytics'))
admin = user['role'] == 'system_administrator'
st.caption(t('Healthcare centre aggregate activity' if admin else 'Your review activity'))
if admin:
    st.caption(user.get('healthcare_center') or '')
start, end = date_filters()
start_ts, end_ts = timestamps(start, end)
data = db.analytics(user['id'], start_ts, end_ts)
evaluation_tab = render_activity(data, start, end)
with evaluation_tab:
    try:
        metrics = evaluation_metrics()
        if metrics is None:
            st.info(t('No matching evaluation report is installed.'))
        else:
            folder, _, _ = inspect_package()
            path = folder / 'per_class_metrics.csv'
            report = valid_class_report(pd.read_csv(path)) if path.exists() else None
            render_evaluation(metrics, report, metrics['source_run_id'])
            if report is None:
                st.info(t('Per-class evaluation details are unavailable.'))
    except (ValueError, KeyError, OSError) as exc:
        st.info(t('Model evaluation unavailable.') + ' ' + str(exc))
