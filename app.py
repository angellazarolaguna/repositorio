import streamlit as st
import pandas as pd
import altair as alt
import requests
import re
import unicodedata
from urllib.parse import quote, urljoin
from io import StringIO
from bs4 import BeautifulSoup

# --- HUBS ---
HUB_OPTIONS = [
    "Sustainable Finance",
    "Net Zero & PA",
    "Analytics Data & IA",
    "Sustainability & reporting",
]


# ===================== CONFIG =====================
st.set_page_config(page_title="Observatorio ESG — NFQ", page_icon=None, layout="wide")

# Google Sheet y pestaña
SHEET_ID = "1tGyDxmB1TuBFiC8k-j19IoSkJO7gkdFCBIlG_hBPUCw"
WORKSHEET = "BBDD"

# Google Form (para altas)
FORM_ACTION_URL = "https://docs.google.com/forms/d/e/1FAIpQLScTbCS0DRON_-aVzdA4y65_18cicMQdLy98uiapoXqc5B6xeQ/formResponse"

ENTRY_MAP = {k: "" for k in [
    "Nombre","Documento","Link","Autoridad emisora","Tipo de documento","Ámbito de aplicación",
    "Tema ESG","Temática ESG","Descripción","Aplicación",
    "Fecha de publicación","Fecha de aplicación","Comentarios",
    "UG 01, 02, 03 - bancos","UG04 - Asset management","UG05 - Seguros","UG06 - LATAM","UG07 - Corporates",
    "Estado","Mes publicación","Año publicación"
]}

def summarize_url(url, max_sent=3):
    try:
        html = safe_get(url)
        soup = BeautifulSoup(html,"html.parser")
        text = " ".join(p.get_text(" ",strip=True) for p in soup.find_all("p"))
        sents = re.split(r"(?<=[.!?]) +", text)
        return " ".join(sents[:max_sent])
    except:
        return "No se pudo generar resumen."
        
COLUMNS = list(ENTRY_MAP.keys())

# ===================== THEME (NFQ) =====================
NFQ_RED = "#9e1927"; NFQ_BLUE = "#6fa2d9"; NFQ_ORANGE = "#d4781b"; NFQ_PURPLE = "#5a64a8"; NFQ_GREY = "#5c6773"
BG_GRADIENT = f"linear-gradient(135deg, {NFQ_ORANGE}20, {NFQ_RED}20 33%, {NFQ_PURPLE}20 66%, {NFQ_BLUE}20)"

# --- CSS (KPI blanco + gráficos sin fondo + estilos portal) ---
st.markdown(f"""
<style>
:root {{
  --nfq-red: {NFQ_RED};
  --nfq-blue: {NFQ_BLUE};
  --nfq-orange: {NFQ_ORANGE};
  --nfq-purple: {NFQ_PURPLE};
}}
.stApp {{
  background: {BG_GRADIENT};
  background-attachment: fixed;
}}
.block-container {{ padding-top: 1.2rem; padding-bottom: 2.5rem; }}
h1, h2, h3 {{ letter-spacing: 0.2px; }}

/* KPI cards */
[data-testid="stMetric"]{{
  background:#fff !important;
  border:1px solid #eee !important;
  border-radius:16px !important;
  padding:14px 16px !important;
  box-shadow:0 6px 22px rgb(0 0 0 / 10%) !important;
}}



/* Sidebar */
section[data-testid="stSidebar"] > div {{
  background: #ffffffd8;
  border-left: 4px solid var(--nfq-purple);
}}

/* Charts: quitar fondo contenedor */
.vega-embed, .stAltairChart {{ background: transparent !important; }}

/* Portal / What's new */
.portal-wrap{{ background:#f2dbe6; padding:18px 22px; border-radius:18px; margin-top:8px; }}
.portal-card{{ background:#fff; border-radius:24px; box-shadow: 0 10px 24px rgb(0 0 0 / 10%); padding:14px 18px; }}
.portal-title{{ font-size:28px; font-weight:800; color:#6b2242; margin:0 0 12px 2px; }}
.table-header,.table-row{{ display:grid; grid-template-columns:1.6fr 1fr 4fr 1.6fr; gap:12px; align-items:center; }}
.table-header{{ font-weight:700; border-bottom:1px solid #eee; padding:10px 4px; }}
.badge-src{{ padding:4px 8px; border-radius:999px; background:#eef4ff; color:#25467a; font-weight:600; font-size:12px; }}
.desc{{ color:#404040; font-size:14px; }}
.hub-tag{{ font-weight:700; color:#222; }}
</style>
""", unsafe_allow_html=True)


##### metemos la cosa para que nos salga bonita para la tabla sin el fondo pesado blanco

st.markdown("""
<style>
/* Contenedor principal de la tabla */
[data-testid="stDataFrame"] > div {
    background: transparent !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08) !important;
    overflow: hidden;
}

/* Quitar fondo de las celdas */
[data-testid="stDataFrame"] table {
    background: transparent !important;
}

/* Quitar fondo de las cabeceras */
[data-testid="stDataFrame"] thead {
    background: transparent !important;
}

/* Celdas de cabecera con borde inferior */
[data-testid="stDataFrame"] thead tr th {
    background: transparent !important;
    border-bottom: 1px solid #ddd !important;
}

/* Filas */
[data-testid="stDataFrame"] tbody tr {
    background: transparent !important;
    border-bottom: 1px solid #eee !important;
}

/* Hover filas */
[data-testid="stDataFrame"] tbody tr:hover {
    background-color: rgba(0,0,0,0.05) !important;
}
</style>
""", unsafe_allow_html=True)


# --- Tema  NFQ: fondo transparente + estética ---
def _nfq_altair_theme():
    return {
        "config": {
            "background": "transparent",
            "view": {"stroke": "transparent"},
            "font": "Inter, Segoe UI, Roboto, Arial, sans-serif",
            "axis": {
                "labelColor": "#2b2b2b",
                "titleColor": "#2b2b2b",
                "grid": True,
                "gridColor": "#E6E6E6",
                "gridOpacity": 0.55,
                "domain": False,
                "tickColor": "#CFCFCF",
            },
            "legend": {"labelColor":"#2b2b2b","titleColor":"#2b2b2b"},
            "range": {"category": [NFQ_RED,NFQ_BLUE,NFQ_ORANGE,NFQ_PURPLE,"#2aa876","#f25f5c"]},
            "bar": {"cornerRadiusTopLeft": 6, "cornerRadiusTopRight": 6}
        }
    }
alt.themes.register("nfq", _nfq_altair_theme)
alt.themes.enable("nfq")

# ===================== HELPERS =====================
def _norm_txt(x: str) -> str:
    if x is None: return ""
    import unicodedata
    s = unicodedata.normalize("NFD", str(x))
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()

def ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    for c in COLUMNS:
        if c not in df.columns: df[c] = pd.NA
    df = df[COLUMNS]
    for c in ["Fecha de publicación","Fecha de aplicación"]:
        df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    df["Año publicación"] = pd.to_numeric(df["Año publicación"], errors="coerce").astype("Int64")
    df["Mes publicación"] = df["Mes publicación"].astype(str).replace({"<NA>": ""})
    return df

@st.cache_data(ttl=30, show_spinner=False)
def load_sheet(sheet_id: str, worksheet: str) -> pd.DataFrame:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={quote(worksheet)}"
    r = requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0"}); r.raise_for_status()
    return ensure_schema(pd.read_csv(StringIO(r.text)).dropna(how="all"))

# ---- SCRAPING (What's new) ----
DEFAULT_KEYWORDS = ["climate","esg","sustainable","transition","risk","net zero"]
def safe_get(url): return requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0"}).text

from urllib.parse import urljoin
def extract_links(html, base):
    soup = BeautifulSoup(html,"html.parser"); out=[]
    for a in soup.find_all("a", href=True):
        href = urljoin(base,a["href"])
        txt = a.get_text(" ", strip=True)
        if len(txt)<5: continue
        out.append({"title":txt,"url":href,"source":base})
    return out

@st.cache_data(ttl=600, show_spinner=False)
def fetch_all_news(kws):
    rows=[]
    for label,url in [
        ("PCAF","https://carbonaccountingfinancials.com/en/news-events"),
        ("NZBA","https://www.unepfi.org/net-zero-banking/"),
        ("PACTA","https://pacta.rmi.org/"),
        ("EBA","https://www.eba.europa.eu/homepage"),
        ("ECB","https://www.ecb.europa.eu/ecb/climate/html/index.en.html"),
        ("ESMA","https://www.esma.europa.eu/esmas-activities/sustainable-finance"),
        ("ICC","https://iccwbo.org/news-publications/policies-reports/icc-principles-for-sustainable-trade/?utm_source=chatgpt.com"),
        ("ICMA","https://www.icmagroup.org/sustainable-finance/the-principles-guidelines-and-handbooks/"),
        ("CE","https://single-market-economy.ec.europa.eu/industry/sustainability_en"),
        ("BIS","https://www.bis.org/")]:
        try:
            html=safe_get(url)
            for it in extract_links(html,url):
                if any(_norm_txt(k) in _norm_txt(it["title"]) for k in kws):
                    it["source"]=label; rows.append(it)
        except Exception:
            continue
    return pd.DataFrame(rows).drop_duplicates("url")

def classify_hub(source,title):
    t=_norm_txt(title)
    if "net zero" in t: return "Net Zero"
    if "data" in t or "analytics" in t or "ai" in t: return "Data, Analytics & AI"
    if "pacta" in _norm_txt(source): return "Corporate"
    return "Sustainable Finance"

# ===================== UI =====================
st.title("Observatorio ESG — NFQ")
tabs = st.tabs(["Home","New","What’s new"])

# ------------ TAB 1: REPOSITORIO ------------
with tabs[0]:
    try:
        df_full = load_sheet(SHEET_ID, WORKSHEET)
    except Exception:
        st.error("No se pudo cargar el Google Sheet. Verifica permisos (Lector público), SHEET_ID y nombre de pestaña.")
        df_full = pd.DataFrame(columns=COLUMNS)

    # Filtros
    with st.expander("Filtros", expanded=False):
        col0,col1, col2, col3, col4, col5 = st.columns(6)
        with col0: filtro_anio = st.multiselect("HUB", HUB_OPTIONS)
        with col1: filtro_anio = st.multiselect("Año publicación", sorted([x for x in df_full["Año publicación"].dropna().unique()]))
        with col2: filtro_tema = st.multiselect("Tema ESG", sorted([str(x) for x in df_full["Tema ESG"].dropna().unique()]))
        with col3: filtro_tipo = st.multiselect("Tipo de documento", sorted([str(x) for x in df_full["Tipo de documento"].dropna().unique()]))
        with col4: filtro_ambito = st.multiselect("Ámbito de aplicación", sorted([str(x) for x in df_full["Ámbito de aplicación"].dropna().unique()]))
        with col5: filtro_estado = st.multiselect("Estado", sorted([str(x) for x in df_full["Estado"].dropna().unique()]))
        texto_busqueda = st.text_input("Búsqueda libre (Nombre, Documento, Descripción, Temática)")

    df = df_full.copy()
    if not df.empty:
        if filtro_anio: df = df[df["Año publicación"].isin(filtro_anio)]
        if filtro_tema: df = df[df["Tema ESG"].astype(str).isin(filtro_tema)]
        if filtro_tipo: df = df[df["Tipo de documento"].astype(str).isin(filtro_tipo)]
        if filtro_ambito: df = df[df["Ámbito de aplicación"].astype(str).isin(filtro_ambito)]
        if filtro_estado: df = df[df["Estado"].astype(str).isin(filtro_estado)]
        if texto_busqueda:
            mask = pd.Series(False, index=df.index)
            for col in ["Nombre","Documento","Descripción","Temática ESG"]:
                mask = mask | df[col].astype(str).str.contains(texto_busqueda, case=False, na=False)
            df = df[mask]

    # KPIs (con fondo blanco por CSS)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total documentos", int(len(df)))
    with c2: st.metric("Años distintos", int(df["Año publicación"].nunique()) if not df.empty else 0)
    with c3: st.metric("Temas ESG", int(df["Tema ESG"].nunique()) if not df.empty else 0)
    with c4: st.metric("Autoridades emisoras", int(df["Autoridad emisora"].nunique()) if not df.empty else 0)

    # Gráficos  
    st.markdown("#### Vista general")
    gcol1, gcol2 = st.columns(2)
    with gcol1:
        d1 = df.dropna(subset=["Año publicación"])
        if not d1.empty:
            base1 = alt.Chart(d1)
            bars1 = base1.mark_bar().encode(
                x=alt.X("Año publicación:O", title="Año", sort=None),
                y=alt.Y("count()", title="Nº documentos"),
                color=alt.Color("Año publicación:O", legend=None),
                tooltip=[alt.Tooltip("Año publicación:O", title="Año"),
                         alt.Tooltip("count()", title="Nº documentos")]
            ).properties(height=220)
            labels1 = base1.mark_text(dy=-6, color="#333").encode(
                x="Año publicación:O",
                y="count()",
                text=alt.Text("count():Q", format="d"),
            )
            st.altair_chart((bars1 + labels1).interactive(), use_container_width=True)

    with gcol2:
        d2 = df.dropna(subset=["Tema ESG"])
        if not d2.empty:
            base2 = alt.Chart(d2)
            bars2 = base2.mark_bar().encode(
                x=alt.X("count()", title="Nº documentos"),
                y=alt.Y("Tema ESG:O", sort="-x", title="Tema ESG"),
                color=alt.Color("Tema ESG:N", legend=None),
                tooltip=[alt.Tooltip("Tema ESG:O", title="Tema"),
                         alt.Tooltip("count()", title="Nº documentos")]
            ).properties(height=220)
            labels2 = base2.mark_text(dx=6, align="left", color="#333").encode(
                x="count()",
                y="Tema ESG:O",
                text=alt.Text("count():Q", format="d"),
            )
            st.altair_chart((bars2 + labels2).interactive(), use_container_width=True)

    # Tabla con links clicables NO FUNCIONA hacer un check o klk 
    st.markdown("#### Repositorio")
    st.dataframe(
    df,
    use_container_width=True,
    column_config={
        "Link": st.column_config.LinkColumn("Link", help="Abrir documento"),
    },
    height=520
)

# ------------ TAB 2: ALTA NUEVO ------------
with tabs[1]:
    st.markdown("#### Dar de alta un nuevo documento")
    if not FORM_ACTION_URL.strip():
        st.warning("Configura FORM_ACTION_URL (termina en /formResponse) para habilitar el alta.")
    missing_entries = [k for k,v in ENTRY_MAP.items() if v.strip()=="" and k in COLUMNS]
    if missing_entries:
        st.info("Faltan `entry.xxxxx` para: " + ", ".join(missing_entries))

    with st.form("alta_form"):
        colA, colB = st.columns(2)
        with colA:
            nombre = st.text_input("Nombre*", placeholder="Título breve del documento")
            documento = st.text_input("Documento", placeholder="Código/Identificador si aplica")
            link = st.text_input("Link", placeholder="https://...")
            autoridad = st.selectbox("Autoridad Emisora", ["", "EBA", "ESMA", "UE", "CNMV"])
            tipo = st.text_input("Tipo de documento", placeholder="Normativa, guía, consulta, informe...")
            ambito = st.text_input("Ámbito de aplicación", placeholder="UE, ES, Global...")
            tema_esg = st.selectbox("Tema ESG", ["", "E", "S", "G", "Mixto"])
            tematica_esg = st.text_input("Temática ESG", placeholder="Taxonomía, divulgación, riesgos, etc.")
            descripcion = st.text_area("Descripción", placeholder="Resumen breve")
            aplicacion = st.text_input("Aplicación", placeholder="Obligatoria/voluntaria, sectores, etc.")
        with colB:
            f_pub = st.date_input("Fecha de publicación", value=None)
            f_apl = st.date_input("Fecha de aplicación", value=None)
            comentarios = st.text_area("Comentarios")
            ug_bancos = st.checkbox("UG 01, 02, 03 - bancos", value=False)
            ug_am = st.checkbox("UG04 - Asset management", value=False)
            ug_seguros = st.checkbox("UG05 - Seguros", value=False)
            ug_latam = st.checkbox("UG06 - LATAM", value=False)
            ug_corp = st.checkbox("UG07 - Corporates", value=False)
            estado = st.selectbox("Estado", ["", "Borrador", "Propuesta", "En consulta", "Publicado", "Derogado", "Fuera de alcance"])
            mes_pub = st.text_input("Mes publicación", placeholder="Ej. enero / 01 / Q1")
            anio_pub = st.number_input("Año publicación", min_value=1900, max_value=2100, step=1, format="%d")

        submitted = st.form_submit_button("Añadir documento")
        if submitted:
            if not nombre.strip():
                st.error("El campo *Nombre* es obligatorio.")
            elif not FORM_ACTION_URL.strip():
                st.error("Falta configurar FORM_ACTION_URL (termina en /formResponse).")
            elif any(v.strip()=="" for v in ENTRY_MAP.values()):
                st.error("Faltan `entry.xxxxx` en ENTRY_MAP. Complétalos para enviar al Form.")
            else:
                payload = {
                    ENTRY_MAP["Nombre"]: nombre.strip(),
                    ENTRY_MAP["Documento"]: documento.strip(),
                    ENTRY_MAP["Link"]: link.strip(),
                    ENTRY_MAP["Autoridad emisora"]: autoridad.strip(),
                    ENTRY_MAP["Tipo de documento"]: tipo.strip(),
                    ENTRY_MAP["Ámbito de aplicación"]: ambito.strip(),
                    ENTRY_MAP["Tema ESG"]: tema_esg.strip(),
                    ENTRY_MAP["Temática ESG"]: tematica_esg.strip(),
                    ENTRY_MAP["Descripción"]: descripcion.strip(),
                    ENTRY_MAP["Aplicación"]: aplicacion.strip(),
                    ENTRY_MAP["Fecha de publicación"]: f_pub.isoformat() if f_pub else "",
                    ENTRY_MAP["Fecha de aplicación"]: f_apl.isoformat() if f_apl else "",
                    ENTRY_MAP["Comentarios"]: comentarios.strip(),
                    ENTRY_MAP["UG 01, 02, 03 - bancos"]: "Sí" if ug_bancos else "",
                    ENTRY_MAP["UG04 - Asset management"]: "Sí" if ug_am else "",
                    ENTRY_MAP["UG05 - Seguros"]: "Sí" if ug_seguros else "",
                    ENTRY_MAP["UG06 - LATAM"]: "Sí" if ug_latam else "",
                    ENTRY_MAP["UG07 - Corporates"]: "Sí" if ug_corp else "",
                    ENTRY_MAP["Estado"]: estado,
                    ENTRY_MAP["Mes publicación"]: str(mes_pub).strip(),
                    ENTRY_MAP["Año publicación"]: int(anio_pub) if anio_pub else ""
                }
                try:
                    r = requests.post(FORM_ACTION_URL, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=20)
                    if r.status_code in (200, 302):
                        st.success("Documento enviado correctamente.")
                        st.balloons()
                    else:
                        st.error(f"No se pudo enviar al Form (status {r.status_code}). Revisa FORM_ACTION_URL y ENTRY_MAP.")
                except Exception as e:
                    st.error(f"Error al enviar al Form: {e}")

# --- NOTICIAS + RESÚMENES ---
with tabs[2]:
    st.markdown("### What´s New")

    kws = st.text_input("Palabras clave", ", ".join(DEFAULT_KEYWORDS)).split(",")

    if st.button("Cargar noticias"):
        with st.spinner("Loading…"):
            df_news = fetch_all_news(kws).copy()
            if not df_news.empty:
                df_news["Hub"] = df_news.apply(lambda r: classify_hub(r["source"], r["title"]), axis=1)
                df_news["Resumen"] = df_news["url"].apply(lambda u: summarize_url(u, max_sent=2))
            st.session_state["df_news"] = df_news

    df_news = st.session_state.get("df_news", pd.DataFrame())

    if df_news.empty:
        st.info("Pulsa **Cargar noticias** para obtener resultados.")
    else:
        selected_hubs = st.multiselect("Filtrar por HUB", HUB_OPTIONS, default=HUB_OPTIONS)
        df_show = df_news[df_news["Hub"].isin(selected_hubs)].copy()

        if df_show.empty:
            st.warning("No hay noticias para los HUB seleccionados.")
        else:
            st.write("Resultados filtrados:")
            for i, row in df_show.iterrows():
                c1, c2, c3, c4, c5 = st.columns([1.5, 1, 3, 2, 1.5])
                with c1: st.markdown(f"**{row['Hub']}**")
                with c2: st.markdown(f"{row['source']}")
                with c3: st.markdown(f"[{row['title']}]({row['url']})")
                with c4: st.markdown(row['Resumen'][:180] + "..." if len(row['Resumen'])>180 else row['Resumen'])
                with c5:
                    add_key = f"add_{i}"
                    del_key = f"del_{i}"
                    if st.button("Add", key=add_key):
                        # Enviar al Google Form como nuevo registro
                        payload = {
                            ENTRY_MAP["Nombre"]: row["title"],
                            ENTRY_MAP["Documento"]: "",
                            ENTRY_MAP["Link"]: row["url"],
                            ENTRY_MAP["Autoridad emisora"]: row["source"],
                            ENTRY_MAP["Tipo de documento"]: "Noticia",
                            ENTRY_MAP["Ámbito de aplicación"]: "",
                            ENTRY_MAP["Tema ESG"]: "",
                            ENTRY_MAP["Temática ESG"]: "",
                            ENTRY_MAP["Descripción"]: row["Resumen"],
                            ENTRY_MAP["Aplicación"]: "",
                            ENTRY_MAP["Fecha de publicación"]: date.today().isoformat(),
                            ENTRY_MAP["Fecha de aplicación"]: "",
                            ENTRY_MAP["Comentarios"]: "Añadido desde Noticias",
                            ENTRY_MAP["UG 01, 02, 03 - bancos"]: "",
                            ENTRY_MAP["UG04 - Asset management"]: "",
                            ENTRY_MAP["UG05 - Seguros"]: "",
                            ENTRY_MAP["UG06 - LATAM"]: "",
                            ENTRY_MAP["UG07 - Corporates"]: "",
                            ENTRY_MAP["Estado"]: "Publicado",
                            ENTRY_MAP["Mes publicación"]: str(date.today().month),
                            ENTRY_MAP["Año publicación"]: date.today().year
                        }
                        try:
                            r = requests.post(
                                FORM_ACTION_URL,
                                data=payload,
                                headers={"Content-Type": "application/x-www-form-urlencoded"},
                                timeout=20
                            )
                            if r.status_code in (200, 302):
                                st.success("Noticia añadida al Repositorio")
                            else:
                                st.error(f"No se pudo enviar al Form (status {r.status_code}).")
                        except Exception as e:
                            st.error(f"Error al enviar al Form: {e}")

                    if st.button("Delete", key=del_key):
                        df_news = df_news.drop(i)
                        st.session_state["df_news"] = df_news
                        st.warning("Noticia eliminada de la vista")
