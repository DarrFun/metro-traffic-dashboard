# -*- coding: utf-8 -*-
"""Genera las figuras anotadas (alta resolución) para la adenda IEEE (Sección V-B)."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data" / "Metro_Interstate_Traffic_Volume_clean.csv"
FIGS = BASE / "figs"
FIGS.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
df["date_time"] = pd.to_datetime(df["date_time"])
df["holiday"] = df["holiday"].fillna("None")
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
df["dia_nombre"] = df["dia_semana"].map(lambda x: DIAS[x])
df["mes_nombre"] = df["mes"].map(lambda x: MESES[x - 1])

sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200
plt.rcParams["font.size"] = 10

C_TRAFFIC = "#2c7fb8"
C_TEMP = "#d95f0e"
C_ALERT = "#e31a1c"
C_NEUTRAL = "#737373"

def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGS / name, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


# Fig A — Tráfico medio por hora (overview)
fig, ax = plt.subplots(figsize=(8, 4))
by_h = df.groupby("hora")["traffic_volume"].mean()
ax.plot(by_h.index, by_h.values, marker="o", color=C_TRAFFIC, linewidth=2.5)
ax.fill_between(by_h.index, by_h.values, alpha=0.15, color=C_TRAFFIC)
ax.set_xticks(range(0, 24))
ax.set_xlabel("Hora del día")
ax.set_ylabel("Tráfico medio (veh/h)")
ax.set_title("Volumen de tráfico medio por hora — patrón bimodal", fontweight="bold")
ax.annotate("Pico mañana\n~07:00", xy=(7, by_h[7]), xytext=(2, by_h.max()*0.95),
            arrowprops=dict(arrowstyle="->", color=C_ALERT), color=C_ALERT, fontsize=9)
ax.annotate("Pico tarde\n~16:00", xy=(16, by_h[16]), xytext=(18, by_h.max()*0.95),
            arrowprops=dict(arrowstyle="->", color=C_ALERT), color=C_ALERT, fontsize=9)
save(fig, "fig02_trafico_por_hora.png")

# Fig B — Heatmap hora x día
fig, ax = plt.subplots(figsize=(9, 4.2))
pivot = df.pivot_table(values="traffic_volume", index="dia_nombre", columns="hora", aggfunc="mean").reindex(DIAS)
sns.heatmap(pivot, cmap="Blues", ax=ax, cbar_kws={"label": "Tráfico medio (veh/h)"})
ax.set_xlabel("Hora")
ax.set_ylabel("")
ax.set_title("Mapa de calor: tráfico medio por hora × día de la semana", fontweight="bold")
save(fig, "fig03_heatmap_hora_dia.png")

# Fig C — Boxplot clima
fig, ax = plt.subplots(figsize=(9, 4.5))
orden = df.groupby("weather_main")["traffic_volume"].median().sort_values(ascending=False).index
sns.boxplot(data=df, x="weather_main", y="traffic_volume", order=orden, ax=ax,
            color=C_TRAFFIC, showfliers=False)
ax.tick_params(axis="x", rotation=30)
for lbl in ax.get_xticklabels():
    lbl.set_ha("right")
ax.set_xlabel("")
ax.set_ylabel("Tráfico (veh/h)")
ax.set_title("Distribución del tráfico por condición meteorológica", fontweight="bold")
save(fig, "fig04_boxplot_clima.png")

# Fig D — Scatter temp vs traffic
fig, ax = plt.subplots(figsize=(8, 4.5))
sample = df.sample(4000, random_state=42)
sc = ax.scatter(sample["temp_c"], sample["traffic_volume"], c=sample["temp_c"],
                cmap="coolwarm", alpha=0.4, s=8, edgecolors="none")
ax.set_xlabel("Temperatura (°C)")
ax.set_ylabel("Tráfico (veh/h)")
ax.set_title("Temperatura vs. volumen de tráfico (muestra n=4 000)", fontweight="bold")
cb = fig.colorbar(sc, ax=ax)
cb.set_label("Temp (°C)")
save(fig, "fig05_scatter_temp.png")

# Fig E — Correlación Spearman
fig, ax = plt.subplots(figsize=(6.5, 5.5))
corr_cols = ["traffic_volume", "temp_c", "rain_1h", "snow_1h", "clouds_all", "hora"]
corr = df[corr_cols].corr(method="spearman")
sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, vmin=-1, vmax=1,
            square=True, ax=ax, cbar_kws={"label": "ρ de Spearman"})
ax.set_title("Matriz de correlación de Spearman (dataset procesado)", fontweight="bold")
save(fig, "fig06_correlacion.png")

# Fig F — Auditoría pre/post (temp y rain)
fig, axes = plt.subplots(2, 2, figsize=(10, 7))
import pandas as pd
raw = pd.read_csv("C:/Users/Admin/Downloads/Data analysis/MetroTraffic_Dashboard/data/Metro_Interstate_Traffic_Volume_clean.csv")  # placeholder for shape only
# Use original raw gz for pre; recompute quickly
import gzip
raw_df = pd.read_csv("C:/Users/Admin/AppData/Local/Temp/opencode/traffic.csv") if False else None

# Fallback: reconstruct pre-stats from notebook known values is not ideal; instead load raw gz
import os
raw_path = "C:/Users/Admin/AppData/Local/Temp/opencode/traffic.csv"
if not os.path.exists(raw_path):
    gz = "C:/Users/Admin/Downloads/DriveData/data/Metro_Interstate_Traffic_Volume.csv.gz"
    with gzip.open(gz, "rt") as f:
        raw_df = pd.read_csv(f)
else:
    raw_df = pd.read_csv(raw_path)

sns.histplot(raw_df["temp"] - 273.15, bins=50, ax=axes[0, 0], color=C_TEMP)
axes[0, 0].set_title("temp — CRUDO (con 0 K, °C)", fontweight="bold")
sns.histplot(df["temp_c"], bins=50, ax=axes[0, 1], color=C_TRAFFIC)
axes[0, 1].set_title("temp — LIMPIO (°C)", fontweight="bold")
sns.histplot(raw_df["rain_1h"], bins=50, ax=axes[1, 0], color=C_TEMP)
axes[1, 0].set_title("rain_1h — CRUDO (outlier 9831 mm)", fontweight="bold")
sns.histplot(df["rain_1h"], bins=50, ax=axes[1, 1], color=C_TRAFFIC)
axes[1, 1].set_title("rain_1h — LIMPIO", fontweight="bold")
for ax in axes.ravel():
    ax.set_ylabel("Frecuencia")
fig.suptitle("Auditoría pre/post: distribuciones antes y después de la limpieza", fontweight="bold")
save(fig, "fig01_auditoria_prepost.png")

# Fig G — Feriado vs normal
fig, ax = plt.subplots(figsize=(6, 4))
by_fer = df.groupby("es_feriado_lbl" if "es_feriado_lbl" in df else "es_feriado")["traffic_volume"].mean()
labels = ["Día normal", "Feriado"] if "es_feriado_lbl" not in df else None
vals = [df[df["es_feriado"] == 0]["traffic_volume"].mean(),
        df[df["es_feriado"] == 1]["traffic_volume"].mean()]
ax.bar(["Día normal", "Feriado"], vals, color=[C_TRAFFIC, C_ALERT])
ax.set_ylabel("Tráfico medio (veh/h)")
ax.set_title("Tráfico medio: días normales vs. feriados", fontweight="bold")
for i, v in enumerate(vals):
    ax.text(i, v + 50, f"{v:,.0f}", ha="center", fontweight="bold")
save(fig, "fig07_feriado.png")

print("DONE")
