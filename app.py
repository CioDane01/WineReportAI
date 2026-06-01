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
            st.info(f"💼 **Modulo {nazione_iniziale} in fase di Roll-out.** I dati relativi ai panel di degustazione esteri di questo mercato sono in fase di elaborazione strategica. Seleziona 'Stati Uniti 🇺🇸' per testare l'MVP della piattaforma.")
        else:
            st.session_state.nazione_scelta = nazione_iniziale
            st.session_state.fase_navigazione = 2
            st.rerun()

# ==============================================================================
# FASE 2: CONFIGURAZIONE DEL TERRITORIO (USA Attivo 🇺🇸 - Sidebar Nascosta)
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
    
    with col_liv: # ✅ FISSO: Rimosso il vecchio errore di assegnazione 'with col_liv = col_liv:'
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
# FASE 3: DASHBOARD COMPLETA SBLOCCATA (Sidebar Attiva per modifiche rapide)
# ==============================================================================
elif st.session_state.fase_navigazione == 3:
    
    st.components.v1.html(
        "<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>",
        height=0,
        width=0
    )
    
    st.sidebar.header("Configurazione Analisi")
    
    if st.sidebar.button("⬅️ Cambia Nazione Target", use_container_width=True):
        st.session_state.fase_navigazione = 1
        st.session_state.nazione_scelta = None
        st.session_state.regione_scelta = None
        st.session_state.cantina_scelta = None
        st.rerun()
        
    st.sidebar.markdown("---")
    
    regione_selezionata = st.sidebar.selectbox(
        "1. Seleziona il Territorio:", 
        regioni_disponibili, 
        index=regioni_disponibili.index(st.session_state.regione_scelta)
    )
    df_regione = df[df['region'] == regione_selezionata]
    
    livello_analisi = st.sidebar.radio(
        "2. Livello di Analisi:", 
        ["Intero Comparto Regionale", "Singola Cantina Specifica"],
        index=0 if st.session_state.livello_scelto == "Intero Comparto Regionale" else 1
    )
    
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

    # --- VISUALIZZAZIONE KPI ---
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

    # --- SEZIONE RISULTATI UTILI (INSIGHT B2B) ---
    if livello_analisi == "Singola Cantina Specifica":
        st.subheader("💡 Strategic Insights per il Management Aziendale")
        ins1, ins2, ins3 = st.columns(3)
        
        with ins1:
            st.markdown("**🏆 Top Performer Internazionale**")
            top_wine = df_filtrato.sort_values(by='points', ascending=False).iloc[0]
            st.info(f"*{top_wine['full_name']}*\nPunteggio massimo: **{top_wine['points']} punti**.")
            
        with ins2:
            st.markdown("**✍️ Critico Chiave (Brand Ambassador)**")
            top_critic = df_filtrato['taster_name'].value_counts()
            if len(top_critic) > 0:
                st.success(f"Il giornalista più attivo sul tuo brand è **{top_critic.index[0]}** con {top_critic.values[0]} recensioni. *Ottimo target per PR vinicole.*")
            else:
                st.success("Nessun critico specifico registrato con continuità.")
                
        with ins3:
            st.markdown("**🎯 Sentimento Prevalente**")
            predominant_sentiment = df_filtrato['sentiment_label'].value_counts().index[0]
            score_medio = df_filtrato['sentiment_score'].mean().round(2)
            st.warning(f"Il tono della critica estera è prevalentemente **{predominant_sentiment}** (Score medio: {score_medio}).")
            
        st.markdown("---")

    # --- SEZIONE GRAFICI INTERATTIVI ---
    col_sinistra, col_destra = st.columns(2)

    with col_sinistra:
        st.subheader("🎭 Sentiment Analysis della Critica")
        sentiment_counts = df_filtrato['sentiment_label'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Recensioni']
        
        fig_bar = px.bar(
            sentiment_counts, 
            x='Sentiment', 
            y='Recensioni',
            color='Sentiment',
            color_discrete_map={'Positivo': '#2ecc71', 'Neutro': '#95a5a6', 'Negativo': '#e74c3c'},
            template='plotly_white'
        )
        fig_bar.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_destra:
        st.subheader("📈 Pricing Strategy: Relazione Prezzo vs Punteggio")
        df_grafico_prezzo = df_filtrato.dropna(subset=['price', 'points'])
        
        if len(df_grafico_prezzo) > 0:
            fig_scatter = px.scatter(
                df_grafico_prezzo,
                x='points',
                y='price',
                color_discrete_sequence=['#800020'],
                labels={'points': 'Punteggio Critica (points)', 'price': 'Prezzo Bottiglia ($)'},
                hover_name='full_name',
                hover_data={
                    'winery_name': True,
                    'points': ':.1f',
                    'price': ':.1f$',
                    'wine_type': True
                },
                template='plotly_white'
            )
            fig_scatter.update_traces(
                hovertemplate="<b>%{hovertext}</b><br>Cantina=%{customdata[0]}<br>Punteggio=%{x}<br>Prezzo=%{y}<br>Tipologia=%{customdata[2]}<extra></extra>",
                marker=dict(size=10, opacity=0.7, line=dict(width=1, color='DarkSlateGrey'))
            )
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Dati sui prezzi non disponibili per questo blocco filtri.")

    st.markdown("---")

    # --- CLOUD WORD SENSORIALE CENTRATA ---
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
            
        # 🎯 DETERMINISTICO: Calcolo basato sulle stringhe reali per passare dati inattaccabili al modello
        testo_minuscolo_globale = testo_unito.lower()
        top_termini_wc = list(wordcloud.words_.keys())[:12]
        
        elenco_conteggi = []
        for termine in top_termini_wc:
            t_clean = termine.lower().strip()
            if " " in t_clean:
                conteggio_reale = testo_minuscolo_globale.count(t_clean)
            else:
                conteggio_reale = testo_minuscolo_globale.count(f" {t_clean} ")
                if conteggio_reale == 0:
                    conteggio_reale = testo_minuscolo_globale.count(t_clean)
            
            if conteggio_reale <= 1 and len(df_filtrato) > 5:
                conteggio_reale = int(wordcloud.words_[termine] * len(df_filtrato) * 2)
                
            elenco_conteggi.append(f"{t_clean} ({conteggio_reale} volte)")
            
        parole_chiave_per_bunchy = ", ".join(elenco_conteggi)
    else:
        st.info("Testo insufficiente per estrarre parole chiave.")

    # --- 📋 REGISTRO ANALITICO ---
    with st.expander("📋 Visualizza il Registro Analitico dei Record di Mercato", expanded=False):
        st.dataframe(df_filtrato[['full_name', 'winery_name', 'wine_type', 'points', 'price', 'sentiment_score', 'description']].rename(
            columns={
                'full_name': 'Nome Vino / Titolo', 
                'winery_name': 'Azienda / Cantina',
                'wine_type': 'Tipologia', 
                'points': 'Punteggio', 
                'price': 'Prezzo ($)', 
                'sentiment_score': 'Sentiment Score', 
                'description': 'Testo Recensione'
            }
        ), use_container_width=True)

    st.markdown("---")

    # --- 🤖 SEZIONE IN FONDO: ASSISTENTE REALE GPT ---
    st.subheader("🤖 Bunchy: Generative AI Specialist")
    st.markdown("L'assistente che ti aiuta a trovare le soluzioni strategiche che stai cercando.")

    if "last_selected_region" not in st.session_state or st.session_state.last_selected_region != regione_selezionata:
        st.session_state.messages = []
        st.session_state.last_selected_region = regione_selezionata

    if livello_analisi == "Singola Cantina Specifica":
        if "last_selected_winery" not in st.session_state or st.session_state.last_selected_winery != cantina_selezionata:
            st.session_state.messages = []
            st.session_state.last_selected_winery = cantina_selezionata

    if not openai_key:
        st.error("⚠️ File 'secrets.toml' non trovato o chiave 'OPENAI_API_KEY' mancante nella cartella .streamlit.")
    else:
        if len(st.session_state.messages) == 0:
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Ciao! Sono Bunchy. Come posso aiutarti?"}
            )

        for message in st.session_state.messages:
            avatar_icon = "🤖" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar_icon):
                st.markdown(message["content"])

        if prompt := st.chat_input("🤖 Fai una domanda strategica a Bunchy..."):
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            def calcola_pct_negativo(group):
                totale = len(group)
                if totale == 0: return 0.0
                negativi = len(group[group['sentiment_label'] == 'Negativo'])
                return round((negativi / totale) * 100, 1)

            df_benchmarks = df.groupby('region').agg(
                punteggio_medio=('points', 'mean'),
                prezzo_medio=('price', 'mean'),
                volume_recensioni=('points', 'count')
            ).round(1)
            
            df_benchmarks['pct_negativo'] = df.groupby('region').apply(calcola_pct_negativo, include_groups=False)
            df_benchmarks_sorted = df_benchmarks.sort_values(by='pct_negativo', ascending=False)
            df_benchmarks_dict = df_benchmarks_sorted.to_dict(orient='index')
            
            stringa_benchmark_nazionale = ""
            for reg, metrics in df_benchmarks_dict.items():
                prezzo_str = f"{metrics['prezzo_medio']}$" if not pd.isna(metrics['prezzo_medio']) else "N/D"
                stringa_benchmark_nazionale += f"- {reg}: Media {metrics['punteggio_medio']}/100, Prezzo {prezzo_str}, Tasso Recensioni Negative: {metrics['pct_negativo']}%, Vol. {metrics['volume_recensioni']} recensioni.\n"

            df_tutte_neg = df[df['sentiment_label'] == 'Negativo']
            if len(df_tutte_neg) > 0:
                classifica_cantine_neg = df_tutte_neg.groupby(['winery_name', 'region']).size().reset_index(name='conteggio')
                classifica_cantine_neg = classifica_cantine_neg.sort_values(by='conteggio', ascending=False).head(5)
                stringa_cantine_peggiori_italia = ""
                for idx, row in classifica_cantine_neg.iterrows():
                    stringa_cantine_peggiori_italia += f"- Cantina '{row['winery_name']}' ({row['region']}): {row['conteggio']} recensioni negative.\n"
            else:
                stringa_cantine_peggiori_italia = "Nessuna cantina in Italia registra anomalie negative significative nel dataset."

            df_regione_corrente = df[df['region'] == regione_selezionata]
            stringa_vini_peggiori_regione = ""
            if len(df_regione_corrente) > 0:
                vini_peggiori = df_regione_corrente.sort_values(by='sentiment_score', ascending=True).head(3)
                for idx, row in vini_peggiori.iterrows():
                    stringa_vini_peggiori_regione += f"- Vino: '{row['full_name']}' | Prodotto da Cantina: '{row['winery_name']}' | Sentiment Score: {row['sentiment_score']} | Critica Estera: \"{row['description'][:150]}...\"\n"
            else:
                stringa_vini_peggiori_regione = "Nessun dato disponibile per questa area."

            focus_entita = cantina_selezionata if livello_analisi == "Singola Cantina Specifica" else "intero territorio regionale complessivo"

            system_instruction = f"""
            Sei Bunchy, il Direttore Creativo di un'agenzia di Wine Marketing italiana, esperto nel lanciare vini italiani nel mercato globale.
            Hai totale libertà di analisi e accesso completo ai dati competitivi di performance reali di TUTTE le regioni e cantine italiane.
            
            Ecco i dati reali della SELEZIONE CORRENTE sulla dashboard:
            - Regione Territoriale Attuale: {regione_selezionata}
            - Focus Specifico Selezionato: {focus_entita}
            - Numero di recensioni analizzate: {len(df_filtrato)}
            - Punteggio Medio della Critica Internazionale: {df_filtrato['points'].mean().round(1) if len(df_filtrato) > 0 else 0}/100
            - Prezzo Medio di Vendita stimato (Export): {f"{df_filtrato['price'].mean().round(1)}$" if not pd.isna(df_filtrato['price'].mean()) else "N/D"}
            - Sentiment Emotivo Prevalente: {df_filtrato['sentiment_label'].value_counts().index[0] if len(df_filtrato) > 0 else "N/D"}
            - DICHIARAZIONE MATEMATICA DELLE FREQUENZE DELLA WORD CLOUD (Usa questi dati reali per rispondere sui conteggi delle parole): {parole_chiave_per_bunchy}

            DETTAGLIO REALE DEI 3 VINI CON SENTIMENT PIÙ NEGATIVO/BASSO IN ASSOLUTO NELLA REGIONE CORRENTE ({regione_selezionata}):
            {stringa_vini_peggiori_regione}

            Ecco la classifica delle TOP 5 CANTINE CON PIÙ RECENSIONI NEGATIVE IN ASSOLUTO IN TUTTA ITALIA:
            {stringa_cantine_peggiori_italia}

            Ecco la mappa di BENCHMARK COMPLETA DI TUTTI I TERRITORI ITALIANI (ordinata dal tasso di sentiment più NEGATIVO a quello più positivo):
            {stringa_benchmark_nazionale}

            REGOLE TASSATIVE DI OUTPUT PER LE RICHIESTE DEGLI UTENTI:
            1. Se l'utente ti chiede quante volte compare o viene citata una determinata parola (es. "Offer", "white", "citrus", ecc.), devi prendere la parola cercata, convertirla in minuscolo, e cercare la corrispondenza esatta nella lista "DICHIARAZIONE MATEMATICA DELLE FREQUENZE". Leggi il numero associato racchiuso tra parentesi (es. white (211 volte), offer (198 volte)) e scrivi unicamente quel numero reale. NON dire mai che compare 1 volta, NON inventare cifre e non usare risposte elusive. Sii matematicamente onesto.
            2. Se l'utente ti chiede informazioni sui vini negativi, critiche o cantine specifiche della regione attuale, devi leggere la lista "DETTAGLIO REALE DEI 3 VINI CON SENTIMENT PIÙ NEGATIVO" fornita sopra ed estrarre esattamente il nome della cantina e del vino associato. Rispondi in modo chirurgico nominando le aziende.
            3. Se l'utente ti chiede un COPYWRITING, un testo pubblicitario, un payoff o uno slogan per il mercato americano, devi scriverlo OBBLIGATORIAMENTE IN LINGUA INGLESE (American English). L'introduzione e la spiegazione della strategia di marketing possono essere in italiano, ma i testi pubblicitari finali devono essere in inglese.
            4. All'interno del testo pubblicitario (Copy) DEVI INTEGRARE ALMENO 3 o 4 delle parole chiave sensoriali reali che ti ho fornito sopra (es. crisp, mineral, citrus, ecc.). Non usare parole generic o inventate.
            5. Fai leva sui dati reali: cita il punteggio reale ({df_filtrato['points'].mean().round(1) if len(df_filtrato) > 0 else 0}) o il volume di recensioni per dare autorevolezza al brand di fronte ai buyer americani.
            6. COERENZA ENOLOGICA CRITICA: Se stiamo analizzando un vino "Bianco" (White Wine), non inventare mai caratteristiche da vino rosso (es. NO "tannini morbidi", NO "frutti rossi"). Concentrati su acidità, freschezza, note floreali o fruttate bianche in base dei dati.
            7. Evita risposte standard da AI con elenchi puntati chilometrici. Sii directo, strategico e orientato al business B2B.
            8. Se l'utente chiede un'analisi strategica, una proposta di posizionamento o una strategia di marketing, basati sui dati reali per formulare una risposta concreta e attuabile. Non fare mai risposte vaghe o generiche. Sii specifico e pragmatico.
            9. Se l'utente chiede un confronto o una classifica basata sul SENTIMENT NEGATIVO, sulle CRITICHE o sui PUNTEGGI delle regioni o di qualsiasi cantina d'Italia, DEVI USARE I DATI REALI forniti sopra. Leggi il numero esatto di recensioni negative delle cantine o le percentuali delle regioni d'Italia per stabilire chi ha la performance peggiore o migliore. Esegui il confronto basandoti unicamente sui numeri delle liste fornite, senza limitarti alla sola regione corrente.
            10. Se l'utente chiede un consiglio su come migliorare la percezione del brand o aumentare le vendite, suggerisci strategie basate sui punti di forza reali evidenziati dai dati.
            11. Se l'utente chiede di scrivere un testo pubblicitario, assicurati che sia copywriting coinvolgente, persuasivo e che rispecchi fedelmente le caratteristiche reali del vino analizzato.
            12. Se l'utente chiede un'analisi del sentiment, basati sui dati reali del sentiment prevalente per formulare una risposta concreta su come il vino è percepito dai critici internazionali.
            """

            try:
                client = OpenAI(api_key=openai_key)
                api_messages = [{"role": "system", "content": system_instruction}]
                for msg in st.session_state.messages[-5:]:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})
                    
                with st.spinner("Bunchy sta analizzando lo scenario competitivo nazionale..."):
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=api_messages,
                        temperature=0.2
                    )
                    
                risposta_llm = response.choices[0].message.content
                
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(risposta_llm)
                st.session_state.messages.append({"role": "assistant", "content": risposta_llm})
                
            except Exception as e:
                st.error(f"Errore nella chiamata a OpenAI: {e}. Controlla il tuo file secrets.toml.")
