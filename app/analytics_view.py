"""Presentation of scoped aggregates; live counts never imply clinical accuracy."""
from datetime import datetime, time, timedelta, timezone

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from translations import t

BLUE = '#2563eb'
TEAL = '#0891b2'
INK = '#475569'
PALETTE = [BLUE, '#6366f1', TEAL]


def finish(chart, height=285):
    return chart.properties(height=height).configure_view(strokeWidth=0).configure_axis(
        labelColor=INK, titleColor=INK, gridColor='#edf2f7', labelFontSize=12,
        titleFontSize=12, domain=False, tickSize=0,
    ).configure_legend(labelColor=INK, title=None, orient='bottom')


def date_filters():
    today = datetime.now(timezone.utc).date()
    with st.container(border=True):
        a, b, c = st.columns([1.2, 1, 1])
        period = a.selectbox(t('Reporting period'), ['30', '7', '90', 'custom'],
                             format_func=lambda value: t({'7': 'Last 7 days', '30': 'Last 30 days', '90': 'Last 90 days', 'custom': 'Custom dates'}[value]),
                             key='analytics_period')
        if period == 'custom':
            start = b.date_input(t('From date'), today-timedelta(days=29), key='analytics_custom_start')
            end = c.date_input(t('To date'), today, key='analytics_custom_end')
        else:
            start, end = today-timedelta(days=int(period)-1), today
            b.caption(t('From date')); b.write(start.strftime('%d %b %Y'))
            c.caption(t('To date')); c.write(end.strftime('%d %b %Y'))
    if start > end:
        st.error(t('The start date must not be after the end date.'))
        st.stop()
    return start, end


def timestamps(start, end):
    return (datetime.combine(start, time.min, tzinfo=timezone.utc).timestamp(),
            datetime.combine(end+timedelta(days=1), time.min, tzinfo=timezone.utc).timestamp())


def render_activity(data, start, end):
    columns = st.columns(4)
    for column, label, value in zip(columns,
            ['Saved reviews', 'Completed predictions', 'Awaiting model', 'Archived reviews'],
            [data['total'], data['predicted'], data['awaiting'], data['archived']]):
        column.metric(t(label), f'{value:,}', border=True)
    st.caption(t('Analytics includes archived reviews because their data remains stored.'))
    overview, patterns, evaluation = st.tabs([t('Overview'), t('Prediction patterns'), t('Model evaluation')])
    with overview:
        if not data['total']:
            st.info(t('No reviews in the selected date range.'))
        else:
            left, right = st.columns([1.7, 1])
            with left, st.container(border=True):
                st.subheader(t('Review activity'))
                days = pd.date_range(start, end, freq='D')
                values = [data['daily'].get(day.strftime('%Y-%m-%d'), 0) for day in days]
                frame = pd.DataFrame({'date': days, 'count': values})
                base = alt.Chart(frame).encode(
                    x=alt.X('date:T', title=None, axis=alt.Axis(format='%d %b', labelAngle=0)),
                    y=alt.Y('count:Q', title=t('Saved reviews'), axis=alt.Axis(tickMinStep=1), scale=alt.Scale(domainMin=0)),
                    tooltip=[alt.Tooltip('date:T', title=t('Date'), format='%d %b %Y'), alt.Tooltip('count:Q', title=t('Saved reviews'), format=',')],
                )
                st.altair_chart(finish(base.mark_area(color=BLUE, opacity=.12) + base.mark_line(color=BLUE, strokeWidth=3, point=True)), width='stretch')
                busiest = int(max(values))
                st.caption(t('Highest daily review count') + f': {busiest}')
            with right, st.container(border=True):
                st.subheader(t('Review status'))
                counts = pd.DataFrame({'status': [t('Completed predictions'), t('Awaiting model')],
                                       'count': [data['predicted'], data['awaiting']]})
                chart = alt.Chart(counts).mark_arc(innerRadius=65, outerRadius=100, cornerRadius=5).encode(
                    theta=alt.Theta('count:Q'), color=alt.Color('status:N', scale=alt.Scale(range=[BLUE, '#cbd5e1'])),
                    tooltip=[alt.Tooltip('status:N', title=t('Status')), alt.Tooltip('count:Q', title=t('Reviews'))],
                )
                st.altair_chart(finish(chart), width='stretch')
                rate = data['predicted']/data['total']
                st.caption(t('Prediction completion') + f': {rate:.0%}')
                st.caption(t('Completion measures workflow activity, not diagnostic quality.'))
        st.caption(t('Review dates use UTC. Activity counts do not measure diagnostic accuracy or cancer prevalence.'))
    with patterns:
        if not data['predicted']:
            st.info(t('No completed predictions in the selected period.'))
        else:
            left, right = st.columns(2)
            with left, st.container(border=True):
                st.subheader(t('Predicted classes'))
                classes = pd.DataFrame({'class': ['BCC', 'Melanoma', 'SCC'],
                                        'count': [data['classes'].get(name, 0) for name in ['BCC', 'Melanoma', 'SCC']]})
                chart = alt.Chart(classes).mark_bar(cornerRadiusEnd=6, size=32).encode(
                    y=alt.Y('class:N', title=None, sort=['BCC', 'Melanoma', 'SCC']),
                    x=alt.X('count:Q', title=t('Predictions'), axis=alt.Axis(tickMinStep=1)),
                    color=alt.Color('class:N', scale=alt.Scale(domain=['BCC', 'Melanoma', 'SCC'], range=PALETTE), legend=None),
                    tooltip=[alt.Tooltip('class:N', title=t('Class')), alt.Tooltip('count:Q', title=t('Predictions'))],
                )
                st.altair_chart(finish(chart), width='stretch')
                st.caption(t('Predicted labels are not confirmed diagnoses.'))
            with right, st.container(border=True):
                st.subheader(t('Model score distribution'))
                bins = list(data['score_bins'])
                frame = pd.DataFrame({'band': bins, 'count': [data['score_bins'][key] for key in bins]})
                chart = alt.Chart(frame).mark_bar(color=TEAL, cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                    x=alt.X('band:N', sort=bins, title=t('Model score'), axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('count:Q', title=t('Predictions'), axis=alt.Axis(tickMinStep=1)),
                    tooltip=[alt.Tooltip('band:N', title=t('Model score')), alt.Tooltip('count:Q', title=t('Predictions'))],
                )
                st.altair_chart(finish(chart), width='stretch')
                st.caption(t('Model scores are uncalibrated and do not represent diagnostic accuracy.'))
            with st.container(border=True):
                st.subheader(t('Model versions used'))
                versions = []
                for value, count in data['model_versions'].items():
                    parts = value.split(' / ')
                    versions.append({t('Model'): parts[0], t('Source run'): parts[1] if len(parts)>1 else '—',
                                     t('Predictions'): count})
                st.dataframe(versions, hide_index=True, width='stretch')
    return evaluation


def render_evaluation(metrics, report, source_run):
    st.caption(t('Held-out development results are separate from live app activity. This test set was previously inspected.'))
    st.caption(t('Source run') + ': ' + source_run)
    a, b = st.columns(2)
    a.metric(t('Test accuracy'), f"{metrics['accuracy']:.1%}", border=True)
    b.metric(t('Test macro F1'), f"{metrics['macro_f1']:.1%}", border=True)
    if report is not None:
        with st.container(border=True):
            st.subheader(t('Performance by class'))
            columns = {'precision': t('Precision'), 'sensitivity_recall': t('Sensitivity'), 'f1_score': 'F1'}
            frame = report[['class_label', *columns]].melt(id_vars='class_label', var_name='metric', value_name='value')
            frame['metric'] = frame['metric'].map(columns)
            chart = alt.Chart(frame).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                x=alt.X('class_label:N', sort=['BCC', 'Melanoma', 'SCC'], title=None, axis=alt.Axis(labelAngle=0)),
                xOffset=alt.XOffset('metric:N'), y=alt.Y('value:Q', title=None, scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format='%')),
                color=alt.Color('metric:N', scale=alt.Scale(range=PALETTE)),
                tooltip=[alt.Tooltip('class_label:N', title=t('Class')), alt.Tooltip('metric:N', title=t('Metric')), alt.Tooltip('value:Q', title=t('Value'), format='.1%')],
            )
            st.altair_chart(finish(chart, 300), width='stretch')
            display = pd.DataFrame({t('Class'): report.class_label, t('Test images'): report.support.astype(int)})
            for key, label in columns.items():
                display[label] = report[key].map(lambda value: f'{value:.1%}')
            st.dataframe(display, hide_index=True, width='stretch')
    st.warning(t('SCC limitation: SCC detection was weaker in project evaluations. Any predicted class or model score must not be used to exclude SCC or replace clinical assessment.'))
    st.caption(t('Experimental model. Scores are not a diagnosis or a calibrated cancer risk.'))


def valid_class_report(report):
    columns = ['class_label', 'support', 'precision', 'sensitivity_recall', 'f1_score']
    if not set(columns).issubset(report.columns) or report.class_label.duplicated().any() or set(report.class_label) != {'BCC', 'Melanoma', 'SCC'}:
        return None
    result = report[columns].copy()
    for column in columns[1:]:
        result[column] = pd.to_numeric(result[column], errors='coerce')
        if not np.isfinite(result[column]).all():
            return None
    if (result.support < 0).any() or not (result.support % 1 == 0).all():
        return None
    if not result[columns[2:]].ge(0).all().all() or not result[columns[2:]].le(1).all().all():
        return None
    return result.set_index('class_label').loc[['BCC', 'Melanoma', 'SCC']].reset_index()
