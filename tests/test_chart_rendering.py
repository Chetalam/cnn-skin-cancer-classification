"""Regression check for chart serialization with the installed NumPy/PyArrow pair."""
import importlib.util
import unittest

@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit is not installed')
class ChartRendering(unittest.TestCase):
    def test_prediction_chart_and_analytics_serialize(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_string('''
import streamlit as st
import pandas as pd
scores = {'BCC': 0.1, 'Melanoma': 0.7, 'SCC': 0.2}
st.bar_chart({'Model score': scores})
st.line_chart(pd.DataFrame({'Saved reviews': [1, 2]}, index=['2026-11-01', '2026-11-02']))
st.dataframe(pd.DataFrame({'Class': list(scores), 'Score': list(scores.values())}))
''').run(timeout=20)
        self.assertEqual([error.message for error in app.exception], [])
        self.assertEqual(len(app.dataframe), 1)
