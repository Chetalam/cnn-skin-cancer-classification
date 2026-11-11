"""Compatibility route for old Review Records links."""
import streamlit as st
from ui import setup

setup('Reviews')
st.switch_page('pages/3_History.py')
