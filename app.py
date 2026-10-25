import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
from supabase import create_client

st.set_page_config(page_title='DjoFin', page_icon='📈', layout='wide')
st.title('DjoFin | Laboratoire financier')
st.caption('Version 0.3 · Données historiques indicatives · Simulation uniquement · Aucun ordre réel')

ASSETS = {'Apple (USD)': 'AAPL', 'Microsoft (USD)': 'MSFT', 'Nvidia (USD)': 'NVDA', 'ETF S&P 500 SPY (USD)': 'SPY', 'ETF Monde URTH (USD)': 'URTH', 'LVMH (EUR)': 'MC.PA'}

@st.cache_data(ttl=3600, show_spinner=False)
def prices(ticker):
    data = yf.Ticker(ticker).history(period='1y', interval='1d', auto_adjust=True)
    if data.empty or 'Close' not in data:
        return pd.DataFrame()
    return data[['Close']].dropna()

@st.cache_resource(show_spinner=False)
def db_client(url, key):
    return create_client(url, key)

def connect_db():
    try:
        url = st.secrets['SUPABASE_URL']
        key = st.secrets['SUPABASE_KEY']
        return db_client(url, key), None
    except Exception:
        return None, 'Connexion non configurée. Vérifie SUPABASE_URL et SUPABASE_KEY dans les Secrets Streamlit.'

with st.sidebar:
    st.header('Base de données')
    client, config_error = connect_db()
    if config_error:
        st.warning(config_error)
    elif st.button('Tester la connexion'):
        try:
            client.table('assets').select('*').limit(1).execute()
            st.success('Lecture de la table assets réussie.')
        except Exception:
            st.error('Test de lecture impossible : vérifie la table assets et les règles RLS. Consulte les journaux Streamlit pour diagnostiquer.')
    st.caption('La clé publishable ne contourne pas les politiques RLS. Ne jamais exposer une clé secrète dans le dépôt public.')

asset = st.selectbox('Actif à analyser', list(ASSETS))
ticker = ASSETS[asset]
with st.spinner('Chargement des cours…'):
    try:
        df = prices(ticker)
    except Exception:
        df = pd.DataFrame()
if df.empty:
    st.error('Données indisponibles pour cet actif. Réessaie plus tard ou choisis un autre actif.')
    st.stop()

close = df['Close']
last = float(close.iloc[-1])
previous = float(close.iloc[-2]) if len(close) > 1 else last
change = (last / previous - 1) * 100 if previous else 0
currency = 'EUR' if ticker.endswith('.PA') else 'USD'
a, b, c = st.columns(3)
a.metric('Dernière clôture', f'{last:,.2f} {currency}', f'{change:+.2f} % vs précédente')
b.metric('Variation sur 1 an disponible', f'{(last / float(close.iloc[0]) - 1)*100:+.2f} %')
c.metric('Observations', str(len(df)))
st.line_chart(df['Close'], x_label='Date', y_label=f'Cours ({currency})')

st.subheader('Indicateurs techniques simples')
ma20 = close.rolling(20).mean()
ma50 = close.rolling(50).mean()
if pd.notna(ma20.iloc[-1]) and pd.notna(ma50.iloc[-1]):
    st.write(f'Moyenne mobile 20 séances : **{ma20.iloc[-1]:.2f} {currency}** · 50 séances : **{ma50.iloc[-1]:.2f} {currency}**')
    st.info('Tendance descriptive : cours au-dessus des deux moyennes.' if last > ma20.iloc[-1] and last > ma50.iloc[-1] else 'Tendance non confirmée au-dessus des deux moyennes. Aucune recommandation d’achat ou de vente.')

st.subheader('Simulation pédagogique')
st.caption('Achat théorique à la première clôture de la période, sans frais ni change. Aucune transaction réelle.')
capital = st.number_input('Capital fictif', min_value=100, max_value=100000, value=1000, step=100)
start_price = float(close.iloc[0])
value = capital * last / start_price
st.metric('Valeur théorique de cette position', f'{value:,.2f} {currency}', f'{value-capital:+,.2f} {currency}')
st.warning('Les actifs USD sont calculés en USD : 1 000 unités fictives en USD, pas 1 000 € convertis. Les performances passées ne préjugent pas des performances futures.')

st.subheader('Sauvegarde des simulations')
st.caption('Pour activer les écritures, il faudra créer une table de simulations et une politique RLS adaptée à un utilisateur authentifié. Aucun accès public en écriture ne sera accordé.')
if client is None:
    st.info('Connexion Supabase à configurer.')
else:
    st.info('Connexion configurée. Utilise « Tester la connexion » dans le menu latéral. La sauvegarde sera activée après configuration des droits et du schéma de données.')

st.caption(f'Dernière séance disponible : {df.index[-1].strftime("%d/%m/%Y")}. Source expérimentale : yfinance ; cours potentiellement retardés ou incomplets. Usage personnel et éducatif.')
