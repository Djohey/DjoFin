import re
import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client

st.set_page_config(page_title='DjoFin', page_icon='📈', layout='wide')
st.title('DjoFin | Laboratoire financier')
st.caption('Version 0.5 · Données historiques indicatives · Simulation uniquement · Aucun ordre réel')

ASSETS = {
    'Apple (USD)': 'AAPL', 'Microsoft (USD)': 'MSFT', 'Nvidia (USD)': 'NVDA',
    'ETF S&P 500 SPY (USD)': 'SPY', 'ETF Monde URTH (USD)': 'URTH',
    'LVMH (EUR)': 'MC.PA',
}

@st.cache_data(ttl=3600, show_spinner=False)
def prices(ticker):
    data = yf.Ticker(ticker).history(period='1y', interval='1d', auto_adjust=True)
    if data.empty or 'Close' not in data:
        return pd.DataFrame()
    return data[['Close']].dropna()


def connect_db():
    try:
        url = str(st.secrets['SUPABASE_URL']).strip()
        key = str(st.secrets['SUPABASE_KEY']).strip()
        if not url.startswith('https://') or not key:
            return None, 'URL ou clé Supabase manquante ou invalide.'
        # Client propre à chaque session Streamlit : ne pas partager un jeton entre utilisateurs.
        if ('db_client' not in st.session_state or
                st.session_state.get('db_config') != (url, key)):
            st.session_state.db_client = create_client(url, key)
            st.session_state.db_config = (url, key)
            st.session_state.pop('authenticated_user', None)
        return st.session_state.db_client, None
    except KeyError:
        return None, 'Ajoute SUPABASE_URL et SUPABASE_KEY dans les Secrets Streamlit.'
    except Exception as exc:
        return None, f'Initialisation impossible ({type(exc).__name__}).'


def safe_error(exc):
    detail = str(exc)
    detail = re.sub(r'sb_(?:publishable|secret)_[A-Za-z0-9_-]+', '[CLE_MASQUEE]', detail)
    detail = re.sub(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[JETON_MASQUE]', detail)
    return detail[:500]


client, config_error = connect_db()
user = None
if client is not None:
    try:
        # get_user vérifie le jeton auprès de Supabase et ne se fie pas au seul état local.
        session = client.auth.get_session()
        if session and session.access_token:
            user = client.auth.get_user(session.access_token).user
    except Exception:
        user = None
        st.session_state.pop('authenticated_user', None)

with st.sidebar:
    st.header('Compte DjoFin')
    if config_error:
        st.error(config_error)
    elif user is None:
        with st.form('login_form'):
            email = st.text_input('Adresse e-mail')
            password = st.text_input('Mot de passe', type='password')
            submitted = st.form_submit_button('Se connecter', use_container_width=True)
        if submitted:
            if not email.strip() or not password:
                st.warning('Renseigne ton e-mail et ton mot de passe.')
            else:
                try:
                    result = client.auth.sign_in_with_password({'email': email.strip(), 'password': password})
                    if not result.user or not result.session:
                        st.error('Connexion non confirmée.')
                    else:
                        st.rerun()
                except Exception:
                    st.error('Connexion impossible. Vérifie tes identifiants et la configuration Supabase.')
    else:
        st.success('Connecté')
        st.caption(user.email or 'Utilisateur authentifié')
        if st.button('Se déconnecter', use_container_width=True):
            try:
                client.auth.sign_out()
            except Exception:
                pass
            st.session_state.pop('db_client', None)
            st.session_state.pop('db_config', None)
            st.session_state.pop('authenticated_user', None)
            st.rerun()
