import streamlit as st
import pandas as pd
from datetime import datetime, timezone

st.set_page_config(page_title="Alpha AI", page_icon="📊", layout="wide")
st.title("Alpha AI")
st.caption("Prototype de tableau de bord — simulations uniquement, aucune donnée de marché en direct")

finance, football = st.tabs(["Alpha Finance", "Alpha Football"])
with finance:
    st.subheader("Portefeuille fictif")
    a,b,c=st.columns(3)
    a.metric("Capital initial", "1 000 €")
    b.metric("Capital simulé", "1 000 €")
    c.metric("Performance", "0,00 %")
    st.info("Aucun ordre simulé pour le moment. Les données financières et les modèles seront connectés dans une prochaine version.")
with football:
    st.subheader("Prédictions football")
    a,b,c=st.columns(3)
    a.metric("Capital fictif", "1 000 €")
    b.metric("Paris simulés", "0")
    c.metric("Performance", "0,00 %")
    st.info("Aucun pari simulé pour le moment. Les prédictions ne sont pas encore activées.")

st.divider()
st.caption(f"Prototype initial • Affichage actualisé : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
