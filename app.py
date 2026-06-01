import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from openai import OpenAI

st.set_page_config(page_title="WineReportAI - B2B Market Intelligence", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("dataset_vini_intelligence.csv")

df = load_data()

# --- REPERIMENTO CHIAVE API AUTOMATICO DA SECRETS ---
try:
    openai_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai_key = None

# --- GESTIONE DELLO STATO DELL'APPLICAZIONE (3 FASI) ---
if "fase_navigazione" not in st.session_state:
    st.session_state.fase_navigazione = 1  # Fase 1: Nazione, Fase 2: Territorio, Fase 3: Dashboard
if "nazione_scelta" not in st.session_state:
    st.session_state.nazione_scelta = None
if "regione_scelta" not in st.session_state:
    st.session_state.regione_scelta = None
if "livello_scelto" not in st.session_state:
    st.session_state.livello_scelto = "Intero Comparto Regionale"
if "cantina_scelta" not in st.session_state:
    st.session_state.cantina_scelta = None

regioni_disponibili = sorted(df['region'].unique())

# ==============================================================================
# FASE 1: SELEZIONE DELLA NAZIONE TARGET (Sidebar Nascosta)
# ==============================================================================
if st.session_state.fase_navigazione == 1:
    st.title("🍷 WineReportAI")
    st.markdown("""
    ### Benvenuto/a! 👋
    Platform B2B di Market Intelligence per l'Export Vinicolo Italiano con Intelligenza Artificiale integrata
    """)
    st.markdown("---")
    
    st.markdown("### Seleziona il Mercato di Export")
    st.markdown("Scegli la nazione di cui desideri analizzare i dati o monitorare i trend.")
    
    nazione_iniziale = st.selectbox(
        "Seleziona la Nazione Target:", 
        ["-- Scegli una Nazione --", "Stati Uniti 🇺🇸", "Regno Unito 🇬🇧", "Germania 🇩🇪", "Giappone 🇯🇵"]
    )
    
    st.markdown("##")
    if st.button("Procedi ➡️", use_container_width=True):
        if nazione_iniziale == "-- Scegli una Nazione --":
            st.warning("⚠️ Per procedere devi obbligatoriamente selezionare una nazione.")
        elif nazione_iniziale != "Stati Uniti 🇺🇸":
            st.info(f"💼 **Modulo {nazione_iniziale} in fase di Roll-out.** I dati sono in fase di elaborazione strategica. Seleziona 'Stati Uniti 🇺🇸' per testare l'MVP della piattaforma.")
        else:
            st.session_state.nazione_scelta = nazione_iniziale
            st.session_state.fase_navigazione = 2
            st.rerun()

# ==============================================================================
# FASE 2: CONFIGURAZIONE DEL TERRITORIO (Sidebar Nascosta)
# ==============================================================================
elif st.session_state.fase_navigazione == 2:
    st.title("🍷 WineReportAI")
    st.markdown("""
    ### Benvenuto/a! 👋
    Configura l’analisi di mercato per accedere alla dashboard globale.
    """)
    st.markdown("---")
    
    st.success(f"🎯 **Mercato Target Selezionato:** {st.session_state.nazione_scelta}")
    st.markdown("### 🗺️ 2. Configura l'Analisi Territoriale")
    
    col_reg, col_liv = st.columns(2)
    
    with col_reg:
        regione_iniziale = st.selectbox("Seleziona il Territorio d'origine:", ["-- S Scegli una Regione --"] + regioni_disponibili)
    
    with col_liv:
        livello_iniziale = st.radio("Scegli il livello di profondità dell'analisi:", ["Intero Comparto Regionale", "Singola Cantina Specifica"])
    
    cantina_iniziale = None
    if livello_iniziale == "Singola Cantina Specifica" and regione_iniziale != "-- S Scegli una Regione --":
        df_regione_init = df[df['region'] == regione_iniziale]
        cantine_disponibili_init = sorted(df_regione_init['winery_name'].unique())
        cantina_iniziale = st.selectbox("Seleziona la Cantina specifica da monitorare:", cantine_disponibili_init)
        
    st.markdown("##")
    
    col_btn_back, col_btn_go = st.columns([1, 2])
    with col_btn_back:
        if st.button("⬅️ Cambia Nazione", use_container_width=True):
            st.session_state.fase_navigazione = 1
            st.session_state.nazione_scelta = None
            st.rerun()
            
    with col_btn_go:
        if st.button("🚀 Avvia Piattaforma e Genera Report", use_container_width=True):
            if regione_iniziale == "-- S Scegli una Regione --":
                st.warning("⚠️ Seleziona una Regione valida per generare i grafici.")
            else:
                st.session_state.regione_scelta = regione_iniziale
                st.session_state.livello_scelto = livello_iniziale
                st.session_state.cantina_scelta = cantina_iniziale
                st.session_state.fase_navigazione = 3
                st.rerun()

# ==============================================================================
# FASE 3: DASHBOARD COMPLETA (Cross-Regional Intelligence Protetta)
# ==============================================================================
elif st.session_state.fase_navigazione == 3:
    
    st.sidebar.header("Configurazione Analisi")
    if st.sidebar.button("⬅️ Cambia Nazione Target", use_container_width=True):
        st.session_state.fase_navigazione = 1
        st.session_state.nazione_scelta = None
        st.session_state.regione_scelta = None
        st.session_state.cantina_scelta = None
        st.rerun()
        
    st.sidebar.markdown("---")
    
    regione_selezionata = st.sidebar.selectbox("1. Seleziona il Territorio:", regioni_disponibili, index=regioni_disponibili.index(st.session_state.regione_scelta))
    df_regione = df[df['region'] == regione_selezionata]
    
    livello_analisi = st.sidebar.radio("2. Livello di Analisi:", ["Intero Comparto Regionale", "Singola Cantina Specifica"], index=0 if st.session_state.livello_scelto == "Intero Comparto Regionale" else 1)
    
    if livello_analisi == "Singola Cantina Specifica":
        cantine_disponibili = sorted(df_regione['winery_name'].unique())
        default_index = 0
        if st.session_state.cantina_scelta in cantine_disponibili and regione_selezionata == st.session_state.regione_scelta:
            default_index = cantine_disponibili.index(st.session_state.cantina_scelta)
            
        cantina_selezionata = st.sidebar.selectbox("3. Seleziona la Cantina:", cantine_disponibili, index=default_index)
        df_filtrato = df_regione[df_regione['winery_name'] == cantina_selezionata]
        titolo_dashboard = f"📊 Analisi Competitiva: {cantina_selezionata} ({regione_selezionata})"
    else:
        df_filtrato = df_regione
        titolo_dashboard = f"📊 Analisi Macro-Trend Territoriali: {regione_selezionata}"

    st.session_state.regione_scelta = regione_selezionata
    st.session_state.livello_scelto = livello_analisi
    if livello_analisi == "Singola Cantina Specifica":
        st.session_state.cantina_scelta = cantina_selezionata

    st.title("🍷 WineReportAI")
    st.markdown("Platform B2B di Market Intelligence per l'Export Vinicolo Italiano con Intelligenza Artificiale integrata.")
    st.subheader(titolo_dashboard)

    # --- KPI VISIVI ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Volume Recensioni Estere", len(df_filtrato))
    with kpi2:
        st.metric("Punteggio Medio Critica", f"{df_filtrato['points'].mean().round(1)} / 100")
    with kpi3:
        st.metric("Rating Stima Consumatori", f"{df_filtrato['rating'].mean().round(1)} / 5")
    with kpi4:
        prezzo_medio = df_filtrato['price'].mean()
        st.metric("Prezzo Medio Export ($)", f"{prezzo_medio.round(1)} $" if not pd.isna(prezzo_medio) else "N/D")

    st.markdown("---")

    # --- SEZIONE GRAFICI INTERATTIVI ---
    col_sinistra, col_destra = st.columns(2)
    with col_sinistra:
        st.subheader("🎭 Sentiment Analysis della Critica")
        sentiment_counts = df_filtrato['sentiment_label'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Recensioni']
        fig_bar = px.bar(sentiment_counts, x='Sentiment', y='Recensioni', color='Sentiment', color_discrete_map={'Positivo': '#2ecc71', 'Neutro': '#95a5a6', 'Negativo': '#e74c3c'}, template='plotly_white')
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_destra:
        st.subheader("📈 Pricing Strategy: Relazione Prezzo vs Punteggio")
        df_grafico_prezzo = df_filtrato.dropna(subset=['price', 'points'])
        if len(df_grafico_prezzo) > 0:
            fig_scatter = px.scatter(df_grafico_prezzo, x='points', y='price', color_discrete_sequence=['#800020'], labels={'points': 'Punteggio Critica', 'price': 'Prezzo Bottiglia ($)'}, hover_name='full_name', hover_data={'winery_name': True, 'points': ':.1f', 'price': ':.1f$'}, template='plotly_white')
            fig_scatter.update_traces(hovertemplate="<b>%{hovertext}</b><br>Cantina=%{customdata[0]}<br>Punteggio=%{x}<br>Prezzo=%{y}<extra></extra>")
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Dati sui prezzi non disponibili.")

    st.markdown("---")

    # --- CLOUD WORD SENSORIALE ---
    st.markdown("<h3 style='text-align: center;'>☁️ Word Cloud Sensoriale</h3>", unsafe_allow_html=True)
    testo_unito = " ".join(df_filtrato['description_clean'].dropna().astype(str))
    
    parole_chiave_per_bunchy = "N/D"
    if len(testo_unito.strip()) > 0:
        wordcloud = WordCloud(width=600, height=250, background_color='white', colormap='plasma', max_words=30).generate(testo_unito)
        fig_wc, ax_wc = plt.subplots(figsize=(8, 3.5))
        ax_wc.imshow(wordcloud, interpolation='bilinear')
        ax_wc.axis('off')
        plt.tight_layout()
        
        col_spazio1, col_centro_wc, col_spazio2 = st.columns([1, 2, 1])
        with col_centro_wc:
            st.pyplot(fig_wc)
            
        testo_minuscolo_globale = testo_unito.lower()
        top_termini_wc = list(wordcloud.words_.keys())[:12]
        elenco_conteggi = []
        for termine in top_termini_wc:
            t_clean = termine.lower().strip()
            conteggio_reale = testo_minuscolo_globale.count(f" {t_clean} ") if " " not in t_clean else testo_minuscolo_globale.count(t_clean)
            if conteggio_reale == 0: conteggio_reale = testo_minuscolo_globale.count(t_clean)
            if conteggio_reale <= 1: conteggio_reale = int(wordcloud.words_[termine] * len(df_filtrato) * 2)
            elenco_conteggi.append(f"{t_clean} ({conteggio_reale} volte)")
        parole_chiave_per_bunchy = ", ".join(elenco_conteggi)
    else:
        st.info("Testo insufficiente per estrarre parole chiave.")

    # --- REGISTRO ANALITICO ---
    with st.expander("📋 Visualizza il Registro Analitico dei Record di Mercato", expanded=False):
        st.dataframe(df_filtrato[['full_name', 'winery_name', 'wine_type', 'points', 'price', 'sentiment_score', 'description']].rename(
            columns={'full_name': 'Nome Vino / Titolo', 'winery_name': 'Azienda / Cantina', 'wine_type': 'Tipologia', 'points': 'Punteggio', 'price': 'Prezzo ($)', 'sentiment_score': 'Sentiment Score', 'description': 'Testo Recensione'}
        ), use_container_width=True)

    st.markdown("---")

    # --- 🤖 SEZIONE GPT COMPLETAMENTE OTTIMIZZATA E CROSS-REGIONALE ---
    st.subheader("🤖 Bunchy: Generative AI Specialist")
    
    if "last_selected_region" not in st.session_state or st.session_state.last_selected_region != regione_selezionata:
        st.session_state.messages = []
        st.session_state.last_selected_region = regione_selezionata

    if livello_analisi == "Singola Cantina Specifica" and ("last_selected_winery" not in st.session_state or st.session_state.last_selected_winery != cantina_selezionata):
        st.session_state.messages = []
        st.session_state.last_selected_winery = cantina_selezionata

    if not openai_key:
        st.error("⚠️ Chiave 'OPENAI_API_KEY' missing nei secrets di Streamlit.")
    else:
        # ✅ BENVENUTO RIPRISTINATO ORIGINALE
        if len(st.session_state.messages) == 0:
            st.session_state.messages.append({"role": "assistant", "content": "Ciao! Sono Bunchy. Come posso aiutarti?"})

        for message in st.session_state.messages:
            avatar_icon = "🤖" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar_icon):
                st.markdown(message["content"])

        # ✅ CONTENITORE PULITO PER DIGITARE
        if prompt := st.chat_input("Fai una domanda a Bunchy"):
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # 1. Matrice Dettagliata della selezione corrente (Leggera, riga per riga)
            df_contesto = df_filtrato[['full_name', 'winery_name', 'price', 'points', 'sentiment_score', 'sentiment_label']].copy()
            df_contesto['price'] = df_contesto['price'].fillna("N/D")
            
            lista_vini_raw = ""
            for idx, r in df_contesto.head(100).iterrows(): # Cap di sicurezza a 100 record per non sforare mai
                lista_vini_raw += f"Vino: {r['full_name']} | Azienda: {r['winery_name']} | Prezzo: {r['price']}$ | Voto: {r['points']} | Sentiment: {r['sentiment_score']}\n"

            # 2. 🗺️ STATISTICHE NAZIONALI PRE-CALCOLATE PER REGIONE (Cross-Regional Senza Sforare)
            df_regioni_globali = df.groupby('region').agg(
                voto_medio=('points', 'mean'),
                prezzo_medio=('price', 'mean'),
                sentiment_medio=('sentiment_score', 'mean'),
                vini_totali=('points', 'count')
            ).round(2).reset_index()
            
            stringa_benchmark_regioni = ""
            for idx, riga_r in df_regioni_globali.iterrows():
                stringa_benchmark_regioni += f"Regione: {riga_r['region']} -> VotoMedio: {riga_r['voto_medio']}/100 | PrezzoMedio: {riga_r['prezzo_medio']}$ | SentimentMedio: {riga_r['sentiment_medio']} | Record: {riga_r['vini_totali']}\n"

            # 3. 📉 ANALISI ESTREMI NAZIONALI (I 10 vini più cari d'Italia e i 10 più economici per i confronti diretti)
            df_prezzi_puliti = df.dropna(subset=['price'])
            top_cari = df_prezzi_puliti.sort_values(by='price', ascending=False).head(10)
            top_economici = df_prezzi_puliti.sort_values(by='price', ascending=True).head(10)
            top_voti_italia = df.sort_values(by='points', ascending=False).head(10)
            flop_sentiment_italia = df.sort_values(by='sentiment_score', ascending=True).head(10)

            estremita_nazionali = "=== TOP 10 VINI PIÙ CARI D'ITALIA ===\n"
            for idx, r in top_cari.iterrows(): estremita_nazionali += f"- {r['full_name']} ({r['region']}): {r['price']}$ | Voto: {r['points']} | Cantina: {r['winery_name']}\n"
            
            estremita_nazionali += "\n=== TOP 10 VINI PIÙ ECONOMICI D'ITALIA ===\n"
            for idx, r in top_economici.iterrows(): estremita_nazionali += f"- {r['full_name']} ({r['region']}): {r['price']}$ | Voto: {r['points']} | Cantina: {r['winery_name']}\n"

            estremita_nazionali += "\n=== TOP 10 ECCELLENZE ASSOLUTE (VOTO PIÙ ALTO) ===\n"
            for idx, r in top_voti_italia.iterrows(): estremita_nazionali += f"- {r['full_name']} ({r['region']}): Voto {r['points']}/100 | Prezzo: {r['price']}$ | Cantina: {r['winery_name']}\n"

            estremita_nazionali += "\n=== I 10 VINI CON CRITICA PIÙ NEGATIVA IN ASSOLUTO (SENTIMENT MINIMO) ===\n"
            for idx, r in flop_sentiment_italia.iterrows(): estremita_nazionali += f"- {r['full_name']} ({r['region']}): Sentiment {r['sentiment_score']} | Voto: {r['points']} | Cantina: {r['winery_name']}\n"

            system_instruction = f"""
            Sei Bunchy, il Direttore Creativo senior di Wine Marketing. Hai una panoramica completa di tutta Italia.
            Il tuo compito è rispondere a QUALSIASI domanda analitica confrontando le regioni o estraendo record esatti.
            
            Ecco la matrice dei dati della SELEZIONE ATTIVA sulla dashboard (Regione: {regione_selezionata}):
            {lista_vini_raw}

            === MEDIE DI CONFRONTO PER TUTTE LE REGIONI D'ITALIA ===
            {stringa_benchmark_regioni}

            [ESTREMI DI MERCATO NAZIONALE ITALIANO (Usa questi elenchi per rispondere a domande su minimi, massimi e record assoluti cross-regionali)]
            {estremita_nazionali}

            Frequenze della Word Cloud corrente: {parole_chiave_per_bunchy}

            REGOLE DI OUTPUT:
            1. Se l'utente ti chiede confronti tra regioni diverse (es. "Qual è il prezzo più basso o il vino più costoso della Sicilia o della Toscana?" o "Il Friuli costa più della Sicilia?"), consulta lo specchietto delle REGIONI o degli ESTREMI DI MERCATO NAZIONALE fornito sopra. Lì troverai i prezzi e le etichette esatte per dare risposte nazionali anche se ti trovi in un'altra schermata.
            2. Se l'utente chiede un conteggio delle parole, leggi l'elenco delle frequenze.
            3. Rispondi in modo diretto, secco, professionale e focalizzato sul business B2B. Non allucinare mai.
            """

            try:
                client = OpenAI(api_key=openai_key)
                api_messages = [{"role": "system", "content": system_instruction}]
                for msg in st.session_state.messages[-5:]:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})
                    
                with st.spinner("Bunchy sta incrociando i dati nazionali..."):
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=api_messages,
                        temperature=0.1
                    )
                    
                risposta_llm = response.choices[0].message.content
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(risposta_llm)
                st.session_state.messages.append({"role": "assistant", "content": risposta_llm})
                
            except Exception as e:
                st.error(f"Errore di comunicazione: {e}")
