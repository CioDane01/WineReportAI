import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from openai import OpenAI

st.set_page_config(page_title="WineReportAI - B2B Market Intelligence", layout="wide")

# ✅ FUNZIONE DI CARICAMENTO DATI CON DIALLINEAMENTO ENOLOGICO (Base 75, Tetto 94)
@st.cache_data
def load_data():
    df_load = pd.read_csv("dataset_vini_intelligence.csv")
    df_load['rating'] = ((df_load['points'] - 75) / 19 * 5).round(1)
    df_load['rating'] = df_load['rating'].clip(lower=1.0, upper=5.0)
    return df_load

# ✅ DF DEFINITO IMMEDIATAMENTE QUI (Evita il NameError)
df = load_data()
regioni_disponibili = sorted(df['region'].unique())

# --- REPERIMENTO CHIAVE API AUTOMATICO DA SECRETS ---
try:
    openai_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai_key = None

# --- GESTIONE DELLO STATO DELL'APPLICAZIONE (3 FASI + TIP BOTTONE) ---
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

# Indice per far ruotare i consigli di Bunchy nella dashboard
if "indice_consiglio" not in st.session_state:
    st.session_state.indice_consiglio = 0

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
        regione_iniziale = st.selectbox("Seleziona il Territorio d'origine:", ["-- Scegli una Regione --"] + regioni_disponibili)
    
    with col_liv:
        livello_iniziale = st.radio("Scegli il livello di profondità dell'analisi:", ["Intero Comparto Regionale", "Singola Cantina Specifica"])
    
    cantina_iniziale = None
    if livello_iniziale == "Singola Cantina Specifica" and regione_iniziale != "-- Scegli una Regione --":
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
            if regione_iniziale == "-- Scegli una Regione --":
                st.warning("⚠️ Seleziona una Regione valida per generare i grafici.")
            else:
                st.session_state.regione_scelta = regione_iniziale
                st.session_state.livello_scelto = livello_iniziale
                st.session_state.cantina_scelta = cantina_iniziale
                st.session_state.fase_navigazione = 3
                st.rerun()

# ==============================================================================
# FASE 3: DASHBOARD COMPLETA (Sblocco dell'interfaccia analitica)
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

    # --- MODIFICA 1: REGISTRO ANALITICO CON INSERIMENTO DEL NOME DEL CRITICO ---
    # Se la colonna 'taster_name' non esiste o ha dei vuoti, usiamo un ripiego sicuro per evitare crash
    colonne_registro = ['full_name', 'winery_name', 'wine_type', 'points', 'price', 'sentiment_score']
    nomi_colonne_mappate = {
        'full_name': 'Nome Vino / Titolo', 
        'winery_name': 'Azienda / Cantina', 
        'wine_type': 'Tipologia', 
        'points': 'Punteggio', 
        'price': 'Prezzo ($)', 
        'sentiment_score': 'Sentiment Score',
        'description': 'Testo Recensione'
    }

    if 'taster_name' in df_filtrato.columns:
        colonne_registro.append('taster_name')
        nomi_colonne_mappate['taster_name'] = 'Autore Recensione / Critico'
    
    colonne_registro.append('description')

    with st.expander("📋 Visualizza il Registro Analitico dei Record di Mercato", expanded=False):
        st.dataframe(df_filtrato[colonne_registro].rename(columns=nomi_colonne_mappate), use_container_width=True)

    st.markdown("---")

    # ==============================================================================
    # 🤖 SEZIONE GPT AUTOMATIZZATA CON DIALOGO DEI CONSIGLI STRATEGICI ALTERNATI
    # ==============================================================================
    st.subheader("🤖 Bunchy: Generative AI Specialist")
    
    # --- MODIFICA 2: CONTENITORE DINAMICO DEI CONSIGLI CON FRECCIA/BOTTONE ---
    elenco_consigli = [
        "💡 **Consiglio Analitico (Prezzi e Numeri):** Chiedimi *'Qual è il vino con il prezzo più basso e che punteggio ha?'* oppure *'Quale azienda ha la media voto più alta?'* per scovare i best-buy del mercato.",
        "📊 **Consiglio Strategico (Confronti Competitivi):** Prova a chiedermi *'Fammi un confronto tra le due cantine principali della selezione per capire chi ha il sentiment migliore della critica'*, ti aiuterò a mappare il posizionamento dei competitor.",
        "✍️ **Consiglio di Marketing (Copywriting & Parole chiave):** Chiedimi *'Quali sono le parole più usate nelle recensioni con sentiment positivo superiore a 0.5?'* per scoprire quali termini fanno breccia nella mente dei critici esteri.",
        "🎯 **Consiglio Linguistico (Lessico Emozionale):** Chiedimi *'Quali termini descrittivi o sensoriali vengono ripetuti più spesso in questa Word Cloud?'* per estrarre la semantica ideale per i tuoi comunicati stampa di export."
    ]
    
    # Layout a due colonne per mostrare il consiglio corrente e il bottone di cambio
    col_testo_consiglio, col_bottone_cambio = st.columns([5, 1])
    
    with col_testo_consiglio:
        st.info(elenco_consigli[st.session_state.indice_consiglio])
        
    with col_bottone_cambio:
        if st.button("Altro consiglio 🔄", use_container_width=True):
            st.session_state.indice_consiglio = (st.session_state.indice_consiglio + 1) % len(elenco_consigli)
            st.rerun()
            
    st.markdown("##")

    # --- LOGICA STANDARD DELLA CHAT DI BUNCHY ---
    if "last_selected_region" not in st.session_state or st.session_state.last_selected_region != regione_selezionata:
        st.session_state.messages = []
        st.session_state.last_selected_region = regione_selezionata

    if livello_analisi == "Singola Cantina Specifica" and ("last_selected_winery" not in st.session_state or st.session_state.last_selected_winery != cantina_selezionata):
        st.session_state.messages = []
        st.session_state.last_selected_winery = cantina_selezionata

    if not openai_key:
        st.error("⚠️ Chiave 'OPENAI_API_KEY' missing nei secrets di Streamlit.")
    else:
        if len(st.session_state.messages) == 0:
            st.session_state.messages.append({"role": "assistant", "content": "Ciao! Sono Bunchy. Come posso aiutarti?"})

        for message in st.session_state.messages:
            avatar_icon = "🤖" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar_icon):
                st.markdown(message["content"])

        if prompt := st.chat_input("Fai una domanda a Bunchy"):
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Generazione della matrice testuale filtrata
            df_contesto = df_filtrato[['full_name', 'winery_name', 'price', 'points', 'sentiment_score', 'sentiment_label']].copy()
            df_contesto['price'] = df_contesto['price'].fillna("N/D")
            
            lista_vini_raw = ""
            for idx, r in df_contesto.iterrows():
                lista_vini_raw += f"Etichetta: {r['full_name']} | Azienda: {r['winery_name']} | Prezzo: {r['price']} $ | Punteggio: {r['points']}/100 | SentimentScore: {r['sentiment_score']} ({r['sentiment_label']})\n"

            df_medie_regionali = df_regione.groupby('winery_name').agg(
                sentiment_medio=('sentiment_score', 'mean'),
                prezzo_medio=('price', 'mean'),
                punteggio_medio=('points', 'mean'),
                conteggio_bottiglie=('points', 'count')
            ).round(2)
            
            stringa_medie_aziende = ""
            for cantina_k, m in df_medie_regionali.iterrows():
                p_str = f"{m['prezzo_medio']}$" if not pd.isna(m['prezzo_medio']) else "N/D"
                stringa_medie_aziende += f"Cantina: {cantina_k} -> SentimentMedio: {m['sentiment_medio']} | PrezzoMedio: {p_str} | VotoMedio: {m['punteggio_medio']}/100 | VolumeVini: {m['conteggio_bottiglie']}\n"

            system_instruction = f"""
            Sei Bunchy, l'esperto senior di Market Intelligence collegato in tempo reale al database vinicolo italiano.
            Il tuo compito è analizzare la tabella grezza che ti viene fornita sotto per rispondere a QUALSIASI domanda analitica o quantitativa.
            
            Ecco la matrice dei dati grezzi estratti dal dataset per la selezione corrente:
            {lista_vini_raw}

            Ecco lo specchietto delle medie aggregate di TUTTE le cantine presenti in questa regione ({regione_selezionata}):
            {stringa_medie_aziende}

            Frequenze esatte della Word Cloud visibile all'utente: {parole_chiave_per_bunchy}

            REGOLE DI RISPOSTA ASSOLUTE:
            1. Quando l'utente ti chiede un dato numerico (es. "qual è il prezzo più basso?", "chi ha il sentiment peggiore?", "trova il punteggio massimo"), tu DEVI analizzare l'elenco dei vini fornito sopra, trovare il record con il valore minimo o massimo richiesto e riportare fedelmente il nome del vino, la cantina e la cifra esatta.
            2. Se l'utente ti chiede informazioni o confronti complessi che richiedono il calcolo di troppi record, rispondi basandoti unicamente sulle tabelle di riepilogo fornite sopra.
            3. Se l'utente ti chiede conteggi sulle parole o analisi legate alla marketing intelligence e al posizionamento del testo, fai riferimento al blocco delle frequenze della Word Cloud o estrai i termini chiave dalle righe con i punteggi di sentiment più alti.
            4. Sii un consulente B2B serio, diretto, preciso al millesimo sui numeri e orientato al business strategico. Evita i preamboli inutili o risposte elusive da AI standard.
            """

            try:
                api_messages = [{"role": "system", "content": system_instruction}]
                for msg in st.session_state.messages[-5:]:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})
                
                testo_totale_da_inviare = "".join([m["content"] for m in api_messages])
                token_stimati = int(len(testo_totale_da_inviare.split()) * 1.35)
                
                if token_stimati > 95000:
                    risposta_fallback = (
                        "🤖 **Nota di Bunchy:** Questa query richiede l'elaborazione simultanea di un volume di dati "
                        "troppo elevato per le capacità di un singolo prompt di chat (limite di token superato).\n\n"
                        "💡 **Come aggirare il problema:** Prova a restringere l'analisi utilizzando la barra laterale "
                        "di sinistra (selezionando ad esempio una **Singola Cantina Specifica** anziché l'intero comparto "
                        "regionale). In questo modo ridurrai le righe in memoria e potrò fornirti all'istante l'analisi esatta!"
                    )
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(risposta_fallback)
                    st.session_state.messages.append({"role": "assistant", "content": risposta_fallback})
                
                else:
                    client = OpenAI(api_key=openai_key)
                    with st.spinner("Bunchy sta interrogando la matrice dati..."):
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
                risposta_cortesia_errore = (
                    "🤖 **Bunchy:** La mole di dati analitici per questa specifica richiesta supera i limiti attuali di memoria della chat. "
                    "Per favore, utilizza i filtri della dashboard a sinistra per isolare un set di dati più ristretto (selezionando una cantina o riducendo il comparto) così da poterti dare una risposta precisa."
                )
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(risposta_cortesia_errore)
                st.session_state.messages.append({"role": "assistant", "content": risposta_cortesia_errore})
