# -*- coding: utf-8 -*-
"""Dashboard analítico — Metro Interstate Traffic Volume (UEES, Análisis de Datos).

Traduce el pipeline de datos (Fases I–V) en una interfaz de baja carga cognitiva
siguiendo los principios de la Gramática de los Gráficos, Gestalt, Tufte y
la heurística de Shneiderman (overview → filter → details-on-demand).
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Metro Traffic · Dashboard",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Paleta semántica (color solo con propósito funcional)
# ---------------------------------------------------------------------------
C_TRAFFIC = "#2c7fb8"   # azul: variable objetivo (tráfico)
C_TEMP = "#d95f0e"      # naranja: temperatura
C_ALERT = "#e31a1c"     # rojo: alertas / anomalías
C_NEUTRAL = "#737373"   # gris: referencia / grid
C_OK = "#31a354"        # verde: calidad / OK

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
ESTACIONES_ORDEN = ["Primavera", "Verano", "Otoño", "Invierno"]


@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv("data/Metro_Interstate_Traffic_Volume_clean.csv")
    df["date_time"] = pd.to_datetime(df["date_time"])
    df["holiday"] = df["holiday"].fillna("None")
    df["dia_nombre"] = df["dia_semana"].map(lambda x: DIAS[x])
    df["mes_nombre"] = df["mes"].map(lambda x: MESES[x - 1])
    df["es_feriado_lbl"] = df["es_feriado"].map({0: "Día normal", 1: "Feriado"})
    return df


df = load_data()

# ---------------------------------------------------------------------------
# Sidebar — filtros cruzados globales (Shneiderman: zoom & filter)
# ---------------------------------------------------------------------------
st.sidebar.title("Filtros globales")
st.sidebar.caption("Los filtros se aplican a todas las vistas.")

fecha_min = df["date_time"].min().date()
fecha_max = df["date_time"].max().date()
rango_fecha = st.sidebar.date_input(
    "Rango de fechas", value=(fecha_min, fecha_max),
    min_value=fecha_min, max_value=fecha_max,
)
if isinstance(rango_fecha, tuple) and len(rango_fecha) == 2:
    f_ini, f_fin = rango_fecha
else:
    f_ini, f_fin = fecha_min, fecha_max

hora_rng = st.sidebar.slider("Rango de hora", 0, 23, (0, 23))

dias_sel = st.sidebar.multiselect("Día de la semana", DIAS, default=DIAS)
climas_sel = st.sidebar.multiselect(
    "Condición meteorológica", sorted(df["weather_main"].unique()),
    default=sorted(df["weather_main"].unique()),
)
estaciones_sel = st.sidebar.multiselect("Estación", ESTACIONES_ORDEN, default=ESTACIONES_ORDEN)
feriado_opt = st.sidebar.radio("Feriados", ["Todos", "Solo feriados", "Sin feriados"], index=0)
pico_opt = st.sidebar.checkbox("Solo horas pico (7,8,16,17 h)", value=False)

mask = (
    (df["date_time"].dt.date >= f_ini) & (df["date_time"].dt.date <= f_fin)
    & (df["hora"] >= hora_rng[0]) & (df["hora"] <= hora_rng[1])
    & (df["dia_nombre"].isin(dias_sel))
    & (df["weather_main"].isin(climas_sel))
    & (df["estacion"].isin(estaciones_sel))
)
if feriado_opt == "Solo feriados":
    mask &= df["es_feriado"] == 1
elif feriado_opt == "Sin feriados":
    mask &= df["es_feriado"] == 0
if pico_opt:
    mask &= df["hora_pico"] == 1

fdf = df.loc[mask].copy()

st.sidebar.markdown("---")
st.sidebar.metric("Registros filtrados", f"{len(fdf):,}", delta=f"de {len(df):,}")
st.sidebar.caption(f"Cobertura: {len(fdf)/len(df)*100:.1f} %")

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.title("🚦 Metro Interstate Traffic Volume — Dashboard Analítico")
st.caption(
    "Dataset: UCI ML Repository · MnDOT + OpenWeatherMap · 2012–2018 · "
    "I-94 Minneapolis–St. Paul. Proyecto UEES · Análisis de Datos."
)

# ---------------------------------------------------------------------------
# KPIs (overview first)
# ---------------------------------------------------------------------------
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Registros", f"{len(fdf):,}")
k2.metric("Tráfico medio", f"{fdf['traffic_volume'].mean():,.0f} veh/h")
k3.metric("Tráfico máximo", f"{fdf['traffic_volume'].max():,} veh/h")
k4.metric("Hora pico medio", f"{fdf.groupby('hora')['traffic_volume'].mean().idxmax():02d}:00")
k5.metric("Temp. media", f"{fdf['temp_c'].mean():.1f} °C")
k6.metric("Días con feriado", f"{fdf['es_feriado'].sum():,}")

st.markdown("---")

tabs = st.tabs([
    "1. Diagnóstico",
    "2. Patrones temporales",
    "3. Impacto meteorológico",
    "4. Explorador (drill-down)",
])

# ===========================================================================
# TAB 1 — Diagnóstico (overview + calidad + auditoría pre/post)
# ===========================================================================
with tabs[0]:
    st.subheader("Diagnóstico inicial del sistema")
    st.markdown(
        "**Narrativa:** el tráfico en la I-94 es un sistema con fuerte señal temporal "
        "y ruido meteorológico. Antes de explorar, verificamos la calidad de la data "
        "que alimenta cada vista."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Calidad de los datos (post-pipeline)")
        quality = pd.DataFrame({
            "Indicador": ["Registros totales", "Nulos totales", "Outliers imposibles (temp 0 K)",
                          "Outliers imposibles (rain > 500 mm)", "Duplicados eliminados",
                          "Variables derivadas"],
            "Valor": [f"{len(df):,}", "0", "0 (10 corregidos)", "0 (1 corregido)",
                      "7 646", "7 (hora, día, mes, es_finde, hora_pico, temp_c, es_feriado)"],
        })
        st.dataframe(quality, hide_index=True, use_container_width=True)

    with c2:
        st.markdown("#### Auditoría estadística pre / post (skewness)")
        audit = pd.DataFrame({
            "Variable": ["temp (K)", "rain_1h (mm)"],
            "Skew PRE": [-2.247, 219.389],
            "Skew POST": [-0.383, 28.644],
            "Kurt PRE": [39.915, 48155.627],
            "Kurt POST": [-0.692, 1321.760],
        })
        st.dataframe(audit, hide_index=True, use_container_width=True)
        st.caption("La limpieza redujo la asimetría de temp de −2.25 a −0.38 y la de rain_1h de 219.4 a 28.6.")

    st.markdown("#### Distribución del volumen de tráfico (variable objetivo)")
    fig = px.histogram(
        fdf, x="traffic_volume", nbins=50, color_discrete_sequence=[C_TRAFFIC],
        labels={"traffic_volume": "Volumen de tráfico (veh/h)"},
    )
    fig.update_layout(
        bargap=0.05, showlegend=False, height=320,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Vehículos / hora", yaxis_title="Frecuencia",
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Distribución bimodal: dos poblaciones (horas valle vs. horas pico). "
        "Esto motiva la variable derivada `hora_pico`."
    )

    st.markdown("#### Top 5 horas con mayor tráfico medio")
    top_horas = (fdf.groupby("hora")["traffic_volume"].mean()
                 .sort_values(ascending=False).head(5).reset_index())
    top_horas.columns = ["Hora", "Tráfico medio (veh/h)"]
    top_horas["Hora"] = top_horas["Hora"].map(lambda h: f"{h:02d}:00")
    top_horas["Tráfico medio (veh/h)"] = top_horas["Tráfico medio (veh/h)"].round(0).astype(int)
    st.dataframe(top_horas, hide_index=True, use_container_width=False)

# ===========================================================================
# TAB 2 — Patrones temporales
# ===========================================================================
with tabs[1]:
    st.subheader("Detección de patrones y anomalías temporales")
    st.markdown(
        "**Narrativa:** el factor temporal es el predictor dominante del tráfico "
        "(correlación de Spearman hora–tráfico = 0.33 vs. temp = 0.14)."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Tráfico medio por hora del día")
        by_hora = fdf.groupby("hora")["traffic_volume"].mean().reset_index()
        fig = px.line(by_hora, x="hora", y="traffic_volume", markers=True,
                      color_discrete_sequence=[C_TRAFFIC])
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10),
                          xaxis_title="Hora", yaxis_title="Tráfico medio (veh/h)",
                          xaxis=dict(tickmode="linear", dtick=1))
        fig.update_traces(line_width=2.5)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("##### Tráfico medio por día de la semana")
        by_dia = (fdf.groupby("dia_nombre")["traffic_volume"].mean()
                  .reindex(DIAS).reset_index())
        fig = px.bar(by_dia, x="dia_nombre", y="traffic_volume",
                     color_discrete_sequence=[C_TRAFFIC])
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10),
                          xaxis_title="", yaxis_title="Tráfico medio (veh/h)")
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Mapa de calor: hora × día de la semana")
    pivot = fdf.pivot_table(values="traffic_volume", index="dia_nombre",
                            columns="hora", aggfunc="mean").reindex(DIAS)
    fig = px.imshow(pivot, color_continuous_scale="Blues", aspect="auto",
                    labels=dict(x="Hora", y="Día", color="Tráfico medio"))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Zonas oscuras = picos de congestión (7–8 h y 16–17 h, lun–vie).")

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("##### Tráfico medio por mes")
        by_mes = (fdf.groupby("mes_nombre")["traffic_volume"].mean()
                  .reindex(MESES).reset_index())
        fig = px.bar(by_mes, x="mes_nombre", y="traffic_volume",
                     color_discrete_sequence=[C_TRAFFIC])
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10),
                          xaxis_title="", yaxis_title="Tráfico medio (veh/h)")
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        st.markdown("##### Tráfico por estación del año")
        by_est = (fdf.groupby("estacion")["traffic_volume"].mean()
                  .reindex(ESTACIONES_ORDEN).reset_index())
        fig = px.bar(by_est, x="estacion", y="traffic_volume",
                     color_discrete_sequence=[C_TEMP])
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10),
                          xaxis_title="", yaxis_title="Tráfico medio (veh/h)")
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Hallazgo: el tráfico es bimodal por hora (picos ~07:00 y ~16:00) y se reduce "
        "los fines de semana. La hora es un predictor más fuerte que cualquier variable meteorológica."
    )

# ===========================================================================
# TAB 3 — Impacto meteorológico
# ===========================================================================
with tabs[2]:
    st.subheader("Análisis de causa raíz: impacto meteorológico")
    st.markdown(
        "**Narrativa:** las condiciones climáticas modulan el tráfico, pero su efecto es "
        "secundario frente al patrón horario. Se prioriza el canal posición/longitud."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Tráfico por condición meteorológica (boxplot)")
        orden_clima = (fdf.groupby("weather_main")["traffic_volume"].median()
                       .sort_values(ascending=False).index.tolist())
        fig = px.box(fdf, x="weather_main", y="traffic_volume",
                     category_orders={"weather_main": orden_clima},
                     color_discrete_sequence=[C_TRAFFIC])
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10),
                          xaxis_title="", yaxis_title="Tráfico (veh/h)")
        fig.update_xaxes(tickangle=30)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("##### Tráfico medio por condición meteorológica")
        by_clima = (fdf.groupby("weather_main")["traffic_volume"].mean()
                    .sort_values(ascending=False).reset_index())
        fig = px.bar(by_clima, x="weather_main", y="traffic_volume",
                     color_discrete_sequence=[C_TRAFFIC])
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10),
                          xaxis_title="", yaxis_title="Tráfico medio (veh/h)")
        fig.update_xaxes(tickangle=30)
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Temperatura vs. volumen de tráfico")
    sample = fdf.sample(min(4000, len(fdf)), random_state=42)
    fig = px.scatter(sample, x="temp_c", y="traffic_volume", color="weather_main",
                     opacity=0.5, trendline="ols",
                     labels={"temp_c": "Temperatura (°C)", "traffic_volume": "Tráfico (veh/h)"})
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("##### Tráfico medio por nivel de nubosidad")
        fdf2 = fdf.copy()
        fdf2["nubes_bin"] = pd.cut(fdf2["clouds_all"], bins=[-1, 25, 50, 75, 100],
                                   labels=["0–25 %", "26–50 %", "51–75 %", "76–100 %"])
        by_nubes = fdf2.groupby("nubes_bin", observed=True)["traffic_volume"].mean().reset_index()
        fig = px.bar(by_nubes, x="nubes_bin", y="traffic_volume",
                     color_discrete_sequence=[C_NEUTRAL])
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10),
                          xaxis_title="Nubosidad", yaxis_title="Tráfico medio (veh/h)")
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        st.markdown("##### Tráfico en feriados vs. días normales")
        by_fer = fdf.groupby("es_feriado_lbl")["traffic_volume"].mean().reset_index()
        fig = px.bar(by_fer, x="es_feriado_lbl", y="traffic_volume",
                     color="es_feriado_lbl",
                     color_discrete_map={"Día normal": C_TRAFFIC, "Feriado": C_ALERT})
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10),
                          xaxis_title="", yaxis_title="Tráfico medio (veh/h)", showlegend=False)
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Matriz de correlación de Spearman (variables numéricas)")
    corr_cols = ["traffic_volume", "temp_c", "rain_1h", "snow_1h", "clouds_all", "hora"]
    corr = fdf[corr_cols].corr(method="spearman")
    fig = px.imshow(corr, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                    text_auto=".2f", aspect="auto")
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.warning(
        "Causa raíz: el clima modifica la mediana del tráfico, pero el efecto de la hora "
        "es dominante. Recomendación: priorizar variables temporales (hora, día, mes) en "
        "modelos predictivos y usar escalado robusto (RobustScaler) para precipitación."
    )

# ===========================================================================
# TAB 4 — Explorador (details on demand)
# ===========================================================================
with tabs[3]:
    st.subheader("Explorador interactivo (details-on-demand)")
    st.markdown(
        "Vista detallada con filtros globales ya aplicados. Permite inspeccionar registros "
        "individuales y exportar el subconjunto."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        x_var = st.selectbox("Eje X", ["hora", "temp_c", "clouds_all", "rain_1h"], index=0)
    with c2:
        y_var = st.selectbox("Eje Y", ["traffic_volume", "temp_c"], index=0)
    with c3:
        color_var = st.selectbox("Color", ["weather_main", "estacion", "es_feriado_lbl", "dia_nombre"], index=0)

    sample = fdf.sample(min(5000, len(fdf)), random_state=7)
    fig = px.scatter(sample, x=x_var, y=y_var, color=color_var, opacity=0.6,
                     hover_data=["date_time", "traffic_volume", "temp_c", "weather_main"])
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Tabla de inspección (primeras 200 filas filtradas)")
    cols_show = ["date_time", "traffic_volume", "temp_c", "rain_1h", "clouds_all",
                 "weather_main", "holiday", "hora", "dia_nombre", "mes_nombre", "estacion"]
    st.dataframe(fdf[cols_show].head(200), use_container_width=True, height=320)

    st.download_button(
        "⬇️ Descargar subconjunto filtrado (CSV)",
        data=fdf[cols_show].to_csv(index=False).encode("utf-8"),
        file_name="metro_traffic_filtrado.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption(
    "Dashboard construido con Streamlit + Plotly. Principios: Gramática de los Gráficos "
    "(posición/longitud prioritarios), Gestalt & Tufte (máximo data-to-ink), "
    "Shneiderman (overview → filter → details). Proyecto UEES · Análisis de Datos."
)
