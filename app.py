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

    st.divider()
    st.header('Base de données')
    if client is not None and user is not None:
        if st.button('Tester la connexion', use_container_width=True):
            try:
                response = client.table('portfolio').select('id').eq('user_id', user.id).limit(1).execute()
                st.success('Lecture authentifiée réussie.')
                if not response.data:
                    st.info('Aucun portefeuille visible pour ce compte.')
            except Exception as exc:
                st.error('Lecture impossible : vérifie la politique RLS et les autorisations API.')
                st.caption(f'Type : {type(exc).__name__}')
    else:
        st.caption('Connecte-toi pour tester la lecture de ton portefeuille.')
    st.caption('Utilise uniquement une clé publishable/anon côté application, jamais une clé service_role ou secrète.')

if client is None:
    st.error('Configure la connexion Supabase avant de continuer.')
    st.stop()
if user is None:
    st.info('Connecte-toi dans le menu latéral pour accéder à DjoFin.')
    st.stop()

st.subheader('Mon portefeuille DjoFin')
try:
    result = client.table('portfolio').select('id,name,initial_capital,cash_balance,currency,user_id').eq('user_id', user.id).execute()
    if not result.data:
        st.warning('Aucun portefeuille accessible. Vérifie que le portefeuille est associé à ton compte et que la politique SELECT RLS est active.')
    else:
        for p in result.data:
            currency_p = p.get('currency') or 'EUR'
            st.write(f"**{p.get('name') or 'Portefeuille'}**")
            x, y = st.columns(2)
            x.metric('Capital initial', f"{float(p['initial_capital']):,.2f} {currency_p}")
            y.metric('Solde disponible', f"{float(p['cash_balance']):,.2f} {currency_p}")
except Exception as exc:
    st.error('Impossible de lire le portefeuille. Vérifie les autorisations Data API et la politique RLS.')
    st.caption(f'Type : {type(exc).__name__}')

st.divider()
asset = st.selectbox('Actif à analyser', list(ASSETS))
ticker = ASSETS[asset]
with st.spinner('Chargement des cours…'):
    try:
        df = prices(ticker)
    except Exception:
        df = pd.DataFrame()
if df.empty:
    st.error('Cours indisponibles pour cet actif. Réessaie plus tard ou choisis un autre actif.')
    st.stop()

close = df['Close']
last = float(close.iloc[-1])
previous = float(close.iloc[-2]) if len(close) > 1 else last
change = (last / previous - 1) * 100 if previous else 0
currency = 'EUR' if ticker.endswith('.PA') else 'USD'
a, b, c = st.columns(3)
a.metric('Dernière clôture', f'{last:,.2f} {currency}', f'{change:+.2f} % vs précédente')
b.metric('Variation sur la période disponible', f'{(last / float(close.iloc[0]) - 1) * 100:+.2f} %')
c.metric('Observations', str(len(df)))
st.line_chart(df['Close'], x_label='Date', y_label=f'Cours ({currency})')

st.subheader('Indicateurs techniques simples')
ma20 = close.rolling(20).mean()
ma50 = close.rolling(50).mean()
if pd.notna(ma20.iloc[-1]) and pd.notna(ma50.iloc[-1]):
    st.write(f'Moyenne mobile 20 séances : **{ma20.iloc[-1]:.2f} {currency}** · 50 séances : **{ma50.iloc[-1]:.2f} {currency}**')
    if last > ma20.iloc[-1] and last > ma50.iloc[-1]:
        st.info('Tendance descriptive : cours au-dessus des deux moyennes.')
    else:
        st.info("Tendance non confirmée au-dessus des deux moyennes. Aucune recommandation d'achat ou de vente.")

st.subheader('Simulation pédagogique')
st.caption('Achat théorique à la première clôture de la période, sans frais ni change. Aucune transaction réelle.')
capital = st.number_input('Capital fictif', min_value=100, max_value=100000, value=1000, step=100)
start_price = float(close.iloc[0])
value = capital * last / start_price
st.metric('Valeur théorique de cette position', f'{value:,.2f} {currency}', f'{value - capital:+,.2f} {currency}')
st.warning('Les actifs USD sont calculés en USD : 1 000 unités fictives en USD, pas 1 000 € convertis. Les performances passées ne préjugent pas des performances futures.')

st.subheader('Sauvegarde des simulations')
st.caption('Les transactions et sauvegardes seront activées dans une prochaine version, avec des règles RLS propres à chaque utilisateur. Aucun ordre réel.')
st.info('Portefeuille en lecture seule : aucune écriture n’est effectuée dans cette version.')
st.caption(f"Dernière séance disponible : {df.index[-1].strftime('%d/%m/%Y')}. Source expérimentale : yfinance ; cours potentiellement retardés ou incomplets. Usage personnel et éducatif.")
