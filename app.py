import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from openai import OpenAI

st.set_page_config(page_title="WineAI - B2B Market Intelligence", layout="wide")

st.title("🍷WineExportAI")
st.markdown("Platform B2B di Market Intelligence per l'Export Vinicolo Italiano con Assistente LLM integrato.")

@st.cache_data
def load_data():
    return pd.read_csv("dataset_vini_intelligence.csv")

df = load_data()

# --- REPERIMENTO CHIAVE API AUTOMATICO DA SECRETS ---
try:
    openai_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai_key = None

# --- BARRA LATERALE FILTRI ---
st.sidebar.header("Configurazione Analisi")

# Filtro Macro: Regione
regioni_disponibili = sorted(df['region'].unique())
regione_selezionata = st.sidebar.selectbox("1. Seleziona il Territorio:", regioni_disponibili)

df_regione = df[df['region'] == regione_selezionata]

# Scelta Livello di Analisi (Regione Intera o Singola Cantina)
livello_analisi = st.sidebar.radio("2. Livello di Analisi:", ["Intero Comparto Regionale", "Singola Cantina Specifica"])

if livello_analisi == "Singola Cantina Specifica":
    cantine_disponibili = sorted(df_regione['winery_name'].unique())
    cantina_selezionata = st.sidebar.selectbox("3. Seleziona la Cantina:", cantine_disponibili)
    df_filtrato = df_regione[df_regione['winery_name'] == cantina_selezionata]
    titolo_dashboard = f"📊 Analisi Competitiva: {cantina_selezionata} ({regione_selezionata})"
else:
    df_filtrato = df_regione
    titolo_dashboard = f"📊 Analisi Macro-Trend Territoriali: {regione_selezionata}"

# --- VISUALIZZAZIONE KPI ---
st.subheader(titolo_dashboard)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Volume Recensioni Estere", len(df_filtrato))
with kpi2:
    st.metric("Punteggio Medio Critica", f"{df_filtrato['points'].mean().round(1)} / 100")
with kpi3:
    st.metric("Rating Stimato Consumatori", f"{df_filtrato['rating'].mean().round(1)} / 5")
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

# --- SEZIONE GRAFICI INTERATTIVI CON PLOTLY ---
col_sinistra, col_destra = st.columns(2)

with col_sinistra:
    st.subheader("🎭 Sentiment Analysis della Critica")
    sentiment_counts = df_filtrato['sentiment_label'].value_counts().reset_index()
    sentiment_counts.columns = ['Sentiment', 'Recensioni']
    
    # Grafico a barre interattivo
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
        # Grafico a dispersione (Scatter) INTERATTIVO con HOVER dei dettagli del vino
        fig_scatter = px.scatter(
            df_grafico_prezzo,
            x='points',
            y='price',
            color_discrete_sequence=['#800020'],
            labels={'points': 'Punteggio Critica (points)', 'price': 'Prezzo Bottiglia ($)'},
            hover_name='full_name',  # Nome del vino in cima al box di hover
            hover_data={
                'points': ':.1f',    # Mostra i punti
                'price': ':.1f$',    # Mostra il prezzo con simbolo $
                'wine_type': True,   # Mostra la tipologia
                'winery_name': True  # Mostra la cantina
            },
            template='plotly_white'
        )
        fig_scatter.update_traces(marker=dict(size=10, opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Dati sui prezzi non disponibili per questo blocco filtri.")

st.markdown("---")

# --- WORDCLOUD MODIFICATA (PIÙ PICCOLA E CENTRATA) ---
# INCOLLA QUESTA RIGA AL SUO POSTO:
st.markdown("<h3 style='text-align: center;'>☁️ Text Mining: Attributi Sensoriali e Linguistici Prevalenti</h3>", unsafe_allow_html=True)
testo_unito = " ".join(df_filtrato['description_clean'].dropna().astype(str))
if len(testo_unito.strip()) > 0:
    # Ridotte le dimensioni interne dell'immagine WordCloud
    wordcloud = WordCloud(width=600, height=250, background_color='white', colormap='plasma', max_words=30).generate(testo_unito)
    
    # Ridotta la dimensione della figura Matplotlib
    fig_wc, ax_wc = plt.subplots(figsize=(8, 3.5))
    ax_wc.imshow(wordcloud, interpolation='bilinear')
    ax_wc.axis('off')
    plt.tight_layout()
    
    # Centratura perfetta tramite colonne Streamlit (colonna principale al centro più larga)
    col_spazio1, col_centro_wc, col_spazio2 = st.columns([1, 2, 1])
    with col_centro_wc:
        st.pyplot(fig_wc)
else:
    st.info("Testo insufficiente per estrarre parole chiave.")

st.markdown("---")

# --- 📋 REGISTRO ANALITICO MODIFICATO (COLLASSIBILE E CHIUSO DI DEFAULT) ---
# Usiamo st.expander con expanded=False per presentarlo chiuso all'avvio
with st.expander("📋 Visualizza il Registro Analitico dei Record di Mercato", expanded=False):
    st.dataframe(df_filtrato[['full_name', 'wine_type', 'points', 'price', 'sentiment_score', 'description']].rename(
        columns={'full_name': 'Nome Vino / Titolo', 'wine_type': 'Tipologia', 'points': 'Punteggio', 'price': 'Prezzo ($)', 'sentiment_score': 'Sentiment Score', 'description': 'Testo Recensione'}
    ), use_container_width=True)

st.markdown("---")

# --- 🤖 SEZIONE IN FONDO: ASSISTENTE REALE GPT (PROTETTO E DINAMICO) ---
st.subheader("🤖 Bunchy: Generative AI Specialist")
st.markdown("L'assistente che ti aiuta a trovare le soluzioni strategiche che stai cercando.")

# Svuota automaticamente la chat se l'utente cambia regione o cantina per evitare cortocircuiti nei dati!
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
    # Messaggio di benvenuto dinamico senza dati fissi
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
        
       # --- PREPARAZIONE DEL CONTESTO REALE (RAG TOTALE E DINAMICO SU TUTTE LE REGIONI) ---
        # 1. Dati specifici della selezione corrente (MICRO)
        punteggio_medio = df_filtrato['points'].mean().round(1) if len(df_filtrato) > 0 else 0
        prezzo_medio_str = f"{df_filtrato['price'].mean().round(1)} $" if not pd.isna(df_filtrato['price'].mean()) else "Non Disponibile"
        sentiment_prevalente = df_filtrato['sentiment_label'].value_counts().index[0] if len(df_filtrato) > 0 else "Neutro"
        
        lista_parole = df_filtrato['description_clean'].dropna().str.cat(sep=' ').split()
        parole_chiave_reali = ", ".join(list(set(lista_parole[:20]))) if len(lista_parole) > 0 else "elegante, tipico, strutturato"
        focus_entita = cantina_selezionata if livello_analisi == "Singola Cantina Specifica" else "intero territorio regionale complessivo"

        # 2. CALCOLO DINAMICO DI TUTTI I BENCHMARK REGIONALI + ESTRAZIONE SENTIMENT NEGATIVO REALE
        # Calcoliamo per ogni regione le metriche chiave e la percentuale esatta di critiche negative
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
        
        # Calcoliamo la percentuale di negativo per regione e la uniamo al benchmark
        df_benchmarks['pct_negativo'] = df.groupby('region').apply(calcola_pct_negativo, include_groups=False)
        
        # Ordiniamo le regioni da quella con più sentiment negativo a quella con meno per darla già pronta all'LLM
        df_benchmarks_sorted = df_benchmarks.sort_values(by='pct_negativo', ascending=False)
        df_benchmarks_dict = df_benchmarks_sorted.to_dict(orient='index')
        
        stringa_benchmark_nazionale = ""
        for reg, metrics in df_benchmarks_dict.items():
            prezzo_str = f"{metrics['prezzo_medio']}$" if not pd.isna(metrics['prezzo_medio']) else "N/D"
            stringa_benchmark_nazionale += f"- {reg}: Media {metrics['punteggio_medio']}/100, Prezzo {prezzo_str}, Tasso Recensioni Negative: {metrics['pct_negativo']}%, Vol. {metrics['volume_recensioni']} recensioni.\n"

        # Troviamo al volo qual è la singola cantina in assoluto nel dataset regionale con più recensioni negative (se esistono)
        df_neg = df_regione[df_regione['sentiment_label'] == 'Negativo']
        if len(df_neg) > 0 and 'winery_name' in df_neg.columns:
            cantina_piu_negativa = df_neg['winery_name'].value_counts().index[0]
            conteggio_cantina_neg = df_neg['winery_name'].value_counts().values[0]
            info_cantina_negativa = f"{cantina_piu_negativa} (con {conteggio_cantina_neg} recensioni negative rilevate nel comparto di questa regione)"
        else:
            info_cantina_negativa = "Nessuna cantina specifica mostra anomalie critiche evidenti rispetto alla media."



       # --- 🤖 L'LLM AGENTE: MASSIMA LIBERTÀ DI ANALISI SU TUTTO IL DATASET ---
        
        # 1. Calcolo dinamico di tutti i benchmark regionali
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

        # 2. CALCOLO DELLA TOP 5 DELLE CANTINE CON PIÙ RECENSIONI NEGATIVE A LIVELLO NAZIONALE (TUTTA ITALIA)
        df_tutte_neg = df[df['sentiment_label'] == 'Negativo']
        if len(df_tutte_neg) > 0:
            classifica_cantine_neg = df_tutte_neg.groupby(['winery_name', 'region']).size().reset_index(name='conteggio')
            classifica_cantine_neg = classifica_cantine_neg.sort_values(by='conteggio', ascending=False).head(5)
            
            stringa_cantine_peggiori_italia = ""
            for idx, row in classifica_cantine_neg.iterrows():
                stringa_cantine_peggiori_italia += f"- Cantina '{row['winery_name']}' ({row['region']}): {row['conteggio']} recensioni negative.\n"
        else:
            stringa_cantine_peggiori_italia = "Nessuna cantina in Italia registra anomalie negative significative nel dataset."

        # 3. Informazioni specifiche sulla selezione corrente della dashboard (Contesto Micro)
        punteggio_medio = df_filtrato['points'].mean().round(1) if len(df_filtrato) > 0 else 0
        prezzo_medio_str = f"{df_filtrato['price'].mean().round(1)} $" if not pd.isna(df_filtrato['price'].mean()) else "Non Disponibile"
        sentiment_prevalente = df_filtrato['sentiment_label'].value_counts().index[0] if len(df_filtrato) > 0 else "Neutro"
        
        lista_parole = df_filtrato['description_clean'].dropna().str.cat(sep=' ').split()
        parole_chiave_reali = ", ".join(list(set(lista_parole[:20]))) if len(lista_parole) > 0 else "elegante, tipico, strutturato"
        focus_entita = cantina_selezionata if livello_analisi == "Singola Cantina Specifica" else "intero territorio regionale complessivo"

        # 4. Costruzione della System Instruction Globale con i due Database di Benchmark nazionali
        system_instruction = f"""
        Sei Bunchy, il Direttore Creativo di un'agenzia di Wine Marketing italiana, esperto nel lanciare vini italiani nel mercato globale.
        Hai totale libertà di analisi e accesso completo ai dati competitivi di performance reali di TUTTE le regioni e cantine italiane.
        
        Ecco i dati reali della SELEZIONE CORRENTE sulla dashboard:
        - Regione Territoriale Attuale: {regione_selezionata}
        - Focus Specifico Selezionato: {focus_entita}
        - Numero di recensioni analizzate: {len(df_filtrato)}
        - Punteggio Medio della Critica Internazionale: {punteggio_medio}/100
        - Prezzo Medio di Vendita stimato (Export): {prezzo_medio_str}
        - Sentiment Emotivo Prevalente: {sentiment_prevalente}
        - Parole chiave Text Mining: {parole_chiave_reali}

        Ecco la classifica delle TOP 5 CANTINE CON PIÙ RECENSIONI NEGATIVE IN ASSOLUTO IN TUTTA ITALIA:
        {stringa_cantine_peggiori_italia}

        Ecco la mappa di BENCHMARK COMPLETA DI TUTTI I TERRITORI ITALIANI (ordinata dal tasso di sentiment più NEGATIVO a quello più positivo):
        {stringa_benchmark_nazionale}

        REGOLE TASSATIVE DI OUTPUT:
        1. Se l'utente ti chiede un COPYWRITING, un testo pubblicitario, un payoff o uno slogan per il mercato americano, devi scriverlo OBBLIGATORIAMENTE IN LINGUA INGLESE (American English). L'introduzione e la spiegazione della strategia di marketing possono essere in italiano, ma i testi pubblicitari finali devono essere in inglese.
        2. All'interno del testo pubblicitario (Copy) DEVI INTEGRARE ALMENO 3 o 4 delle parole chiave sensoriali reali che ti ho fornito sopra (es. crisp, mineral, citrus, ecc.). Non usare parole generiche o inventate.
        3. Fai leva sui dati reali: cita il punteggio reale ({punteggio_medio}) o il volume di recensioni per dare autorevolezza al brand di fronte ai buyer americani.
        4. COERENZA ENOLOGICA CRITICA: Se stiamo analizzando un vino "Bianco" (White Wine), non inventare mai caratteristiche da vino rosso (es. NO "tannini morbidi", NO "frutti rossi"). Concentrati su acidità, freschezza, note floreali o fruttate bianche in base dei dati.
        5. Evita risposte standard da AI con elenchi puntati chilometrici. Sii directo, strategico e orientato al business B2B.
        6. Se l'utente chiede un'analisi strategica, una proposta di posizionamento o una strategia di marketing, basati sui dati reali per formulare una risposta concreta e attuabile. Non fare mai risposte vaghe o generiche. Sii specifico e pragmatico.
        7. Se l'utente chiede un confronto o una classifica basata sul SENTIMENT NEGATIVO, sulle CRITICHE o sui PUNTEGGI delle regioni o di qualsiasi cantina d'Italia, DEVI USARE I DATI REALI forniti sopra. Leggi il numero esatto di recensioni negative delle cantine o le percentuali delle regioni d'Italia per stabilire chi ha la performance peggiore o migliore. Esegui il confronto basandoti unicamente sui numeri delle liste fornite, senza limitarti alla sola regione corrente.
        8. Se l'utente chiede un consiglio su come migliorare la percezione del brand o aumentare le vendite, suggerisci strategie basate sui punti di forza reali evidenziati dai dati.
        9. Se l'utente chiede di scrivere un testo pubblicitario, assicurati che sia coinvolgente, persuasivo e che rispecchi fedelmente le caratteristiche reali del vino analizzato.
        10. Se l'utente chiede un'analisi del sentiment, basati sui dati reali del sentiment prevalente per formulare una risposta concreta su come il vino è percepito dai critici internazionali.
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