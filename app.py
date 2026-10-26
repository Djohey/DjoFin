import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client
import re

st.set_page_config(page_title="DjoFin", page_icon="📈", layout="wide")
st.title("DjoFin | Laboratoire financier")
st.caption("Version 0.4 · Données historiques indicatives · Simulation uniquement · Aucun ordre réel")

ASSETS = {
    "Apple (USD)": "AAPL", "Microsoft (USD)": "MSFT", "Nvidia (USD)": "NVDA",
    "ETF S&P 500 SPY (USD)": "SPY", "ETF Monde URTH (USD)": "URTH",
    "LVMH (EUR)": "MC.PA",
}

@st.cache_data(ttl=3600, show_spinner=False)
def prices(ticker):
    data = yf.Ticker(ticker).history(period="1y", interval="1d", auto_adjust=True)
    if data.empty or "Close" not in data:
        return pd.DataFrame()
    return data[["Close"]].dropna()

@st.cache_resource(show_spinner=False)
def db_client(url, key):
    return create_client(url, key)

def connect_db():
    try:
        url = str(st.secrets["SUPABASE_URL"]).strip()
        key = str(st.secrets["SUPABASE_KEY"]).strip()
        if not url.startswith("https://") or not key:
            return None, "URL ou clé Supabase manquante / invalide dans les Secrets Streamlit."
        return db_client(url, key), None
    except KeyError:
        return None, "Ajoute SUPABASE_URL et SUPABASE_KEY dans les Secrets Streamlit."
    except Exception as exc:
        return None, f"Initialisation impossible ({type(exc).__name__}). Vérifie les Secrets Streamlit."

with st.sidebar:
    st.header("Base de données")
    client, config_error = connect_db()
    if config_error:
        st.warning(config_error)
    elif st.button("Tester la connexion", use_container_width=True):
        try:
            response = client.table("assets").select("*").limit(1).execute()
            st.success("Lecture Supabase réussie !")
            if not response.data:
                st.info("La table assets est vide. Cela n'empêche pas la connexion de fonctionner.")
            else:
                st.write("Exemple de données :", response.data)
        except Exception as exc:
            st.error("Échec de lecture Supabase")
            st.write("Type d'erreur :", type(exc).__name__)
            detail = str(exc)
            # Masquer les clés fréquentes avant d'afficher l'erreur.
            detail = re.sub(r"sb_(?:publishable|secret)_[A-Za-z0-9_-]+", "[CLE_MASQUEE]", detail)
            detail = re.sub(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[JETON_MASQUE]", detail)
            st.code(detail[:1200] or "Aucun détail fourni par Supabase.")
            st.caption("Vérifie qu'aucune information sensible ne figure dans le message avant de partager une capture.")
    st.caption("La clé publishable respecte les politiques RLS. Ne jamais mettre de clé secrète dans GitHub.")

asset = st.selectbox("Actif à analyser", list(ASSETS))
ticker = ASSETS[asset]
with st.spinner("Chargement des cours…"):
    try:
        df = prices(ticker)
    except Exception:
        df = pd.DataFrame()
if df.empty:
    st.error("Cours indisponibles pour cet actif. Réessaie plus tard ou choisis un autre actif.")
    st.stop()

close = df["Close"]
last = float(close.iloc[-1])
previous = float(close.iloc[-2]) if len(close) > 1 else last
change = (last / previous - 1) * 100 if previous else 0
currency = "EUR" if ticker.endswith(".PA") else "USD"
a, b, c = st.columns(3)
a.metric("Dernière clôture", f"{last:,.2f} {currency}", f"{change:+.2f} % vs précédente")
b.metric("Variation sur la période disponible", f"{(last / float(close.iloc[0]) - 1) * 100:+.2f} %")
c.metric("Observations", str(len(df)))
st.line_chart(df["Close"], x_label="Date", y_label=f"Cours ({currency})")

st.subheader("Indicateurs techniques simples")
ma20 = close.rolling(20).mean()
ma50 = close.rolling(50).mean()
if pd.notna(ma20.iloc[-1]) and pd.notna(ma50.iloc[-1]):
    st.write(f"Moyenne mobile 20 séances : **{ma20.iloc[-1]:.2f} {currency}** · 50 séances : **{ma50.iloc[-1]:.2f} {currency}**")
    if last > ma20.iloc[-1] and last > ma50.iloc[-1]:
        st.info("Tendance descriptive : cours au-dessus des deux moyennes.")
    else:
        st.info("Tendance non confirmée au-dessus des deux moyennes. Aucune recommandation d'achat ou de vente.")

st.subheader("Simulation pédagogique")
st.caption("Achat théorique à la première clôture de la période, sans frais ni change. Aucune transaction réelle.")
capital = st.number_input("Capital fictif", min_value=100, max_value=100000, value=1000, step=100)
start_price = float(close.iloc[0])
value = capital * last / start_price
st.metric("Valeur théorique de cette position", f"{value:,.2f} {currency}", f"{value - capital:+,.2f} {currency}")
st.warning("Les actifs USD sont calculés en USD : 1 000 unités fictives en USD, pas 1 000 € convertis. Les performances passées ne préjugent pas des performances futures.")
# ==========================================
# DJOFIN V0.5 - PORTEFEUILLE FICTIF
# ==========================================

st.subheader("Mon portefeuille DjoFin")
st.caption("Portefeuille fictif enregistré dans Supabase.")

if client is not None:
    try:
        response = (
            client.table("portfolio")
            .select("id,name,initial_capital,cash_balance,currency")
            .eq("id", 1)
            .limit(1)
            .execute()
        )

        if response.data:
            portfolio = response.data[0]

            st.success("Portefeuille récupéré depuis Supabase !")

            col1, col2 = st.columns(2)

            col1.metric(
                "Capital initial",
                f"{float(portfolio['initial_capital']):,.2f} {portfolio['currency']}"
            )

            col2.metric(
                "Liquidités disponibles",
                f"{float(portfolio['cash_balance']):,.2f} {portfolio['currency']}"
            )

            st.write("Portefeuille :", portfolio["name"])

        else:
            st.warning("Aucun portefeuille accessible.")

    except Exception:
        st.error(
            "Impossible de lire le portefeuille. "
            "Vérifie les autorisations Supabase."
        )
else:
    st.warning("Connexion Supabase indisponible.")
st.subheader("Sauvegarde des simulations")
st.caption("Les écritures seront activées après création d'une table dédiée et de règles RLS adaptées à un utilisateur authentifié. Aucun accès public en écriture.")
if client is None:
    st.info("Connexion Supabase à configurer.")
else:
    st.info("Client Supabase initialisé. Utilise « Tester la connexion » dans le menu latéral pour vérifier la lecture.")

st.caption(f"Dernière séance disponible : {df.index[-1].strftime('%d/%m/%Y')}. Source expérimentale : yfinance ; cours potentiellement retardés ou incomplets. Usage personnel et éducatif.")
