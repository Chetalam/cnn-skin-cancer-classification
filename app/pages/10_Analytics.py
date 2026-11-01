from datetime import datetime, time, timedelta, timezone
import pandas as pd
import streamlit as st
import db
from inference import evaluation_metrics, inspect_package
from translations import t, display_data
from ui import setup

user = setup('Analytics')
st.title(t('Analytics'))
admin = user['role'] == 'system_administrator'
st.caption(t('Healthcare centre aggregate activity' if admin else 'Your review activity'))
start = st.date_input(t('From date'), value=datetime.now(timezone.utc).date()-timedelta(days=30))
end = st.date_input(t('To date'), value=datetime.now(timezone.utc).date())
if start > end:
    st.error(t('The start date must not be after the end date.'))
    st.stop()
start_ts = datetime.combine(start, time.min, tzinfo=timezone.utc).timestamp()
end_ts = datetime.combine(end+timedelta(days=1), time.min, tzinfo=timezone.utc).timestamp()
data = db.analytics(user['id'], start_ts, end_ts)
a,b,c = st.columns(3)
a.metric(t('Saved reviews'), data['total'])
b.metric(t('Completed predictions'), data['predicted'])
c.metric(t('Awaiting model'), data['awaiting'])
st.caption(t('Review dates use UTC. Activity counts do not measure diagnostic accuracy or cancer prevalence.'))
if data['total']:
    st.subheader(t('Reviews over time'))
    days = pd.date_range(start, end, freq='D').strftime('%Y-%m-%d')
    daily = pd.Series(data['daily'], dtype=int).reindex(days, fill_value=0)
    st.line_chart(pd.DataFrame({t('Saved reviews'):daily}))
    if data['predicted']:
        st.subheader(t('Predicted classes'))
        st.bar_chart(pd.DataFrame({t('Predictions'): pd.Series(data['classes'])}))
        st.subheader(t('Model score distribution'))
        st.bar_chart(pd.DataFrame({t('Predictions'): pd.Series(data['score_bins'])}))
        st.caption(t('Model scores are uncalibrated and do not represent diagnostic accuracy.'))
        st.subheader(t('Model versions used'))
        st.dataframe(display_data([{'Model version':name,'Predictions':count} for name,count in data['model_versions'].items()]), hide_index=True)
else:
    st.info(t('No reviews in the selected date range.'))

st.subheader(t('Active model evaluation'))
st.caption(t('Held-out development results are separate from live app activity. This test set was previously inspected.'))
try:
    metrics = evaluation_metrics()
    if metrics is None:
        st.info(t('No matching evaluation report is installed.'))
    else:
        st.write(t('Source run') + ': ' + metrics['source_run_id'])
        a,b = st.columns(2)
        a.metric(t('Test accuracy'), f"{metrics['accuracy']:.2%}")
        b.metric(t('Test macro F1'), f"{metrics['macro_f1']:.4f}")
        folder, _, _ = inspect_package()
        report_path = folder / 'per_class_metrics.csv'
        if report_path.exists():
            report = pd.read_csv(report_path)
            columns = ['class_label', 'support', 'precision', 'sensitivity_recall', 'f1_score']
            if set(columns).issubset(report.columns):
                st.dataframe(report[columns].rename(columns={
                    'class_label': t('Class'), 'support': t('Test images'),
                    'precision': t('Precision'), 'sensitivity_recall': t('Sensitivity'),
                    'f1_score': 'F1',
                }), hide_index=True)
        st.warning(t('Experimental model: SCC performance and darker-skin reliability requirements are not met. Scores are not a diagnosis or a calibrated cancer risk.'))
except (ValueError, KeyError, OSError) as exc:
    st.info(t('Model evaluation unavailable.') + ' ' + str(exc))
