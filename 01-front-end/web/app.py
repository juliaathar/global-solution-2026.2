"""Interface EloBairro. Rodar a partir de 01-front-end: streamlit run web/app.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from web.features import visao  # noqa: E402

st.set_page_config(page_title="EloBairro", page_icon="🏘️", layout="wide")
st.title("EloBairro")
visao.render()
