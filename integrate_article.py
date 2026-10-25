# -*- coding: utf-8 -*-
"""Integra la Sección V-B (adenda) en el artículo IEEE original y exporta .docx/.pdf."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parent
ORIG = Path(r"C:\Users\Admin\Downloads\DriveData\Articulo IEEE Metro Traffic.docx")
OUT_DOCX = BASE / "docs" / "Articulo_IEEE_Metro_Traffic_Completo.docx"
FIGS = BASE / "figs"

# ---- contenido V-B (estilo 'normal', títulos en negrita) ----
VB_BLOCKS = [
    ("bold", "V-B. Arquitectura Visual y Diseño de la Interfaz"),
    ("normal", "Esta sección documenta la traducción del pipeline de datos (Fases I–V) en una interfaz "
               "analítica interactiva de baja carga cognitiva, complementando las conclusiones de la Sección V."),
    ("bold", "V-B.1 Justificación teórica de canales visuales"),
    ("normal", "La interfaz se diseñó siguiendo la Gramática de los Gráficos [9], que separa la representación "
               "en marcas (puntos, líneas, barras, áreas) y canales (posición, longitud, ángulo, área, color, "
               "saturación, forma). La elección de canales se rigió por la efectividad perceptiva demostrada "
               "experimentalmente [10]:"),
    ("bullet", "Posición y longitud son los canales de mayor precisión para comparaciones cuantitativas; por ello "
               "las comparaciones de tráfico por hora, día, mes y condición meteorológica se codifican con barras y "
               "líneas (longitud/posición vertical)."),
    ("bullet", "El color y la saturación se usan únicamente con propósito funcional o de alerta: azul para la "
               "variable objetivo (tráfico), naranja para temperatura, rojo para anomalías/feriados y gris para "
               "referencias neutras. No se emplea color decorativo."),
    ("bullet", "Se prohíben los elementos que distorsionan la percepción: no se usan gráficos 3D, gráficos "
               "circulares densos ni ejes truncados sin justificación analítica. Las escalas de los ejes parten de "
               "cero cuando se comparan magnitudes."),
    ("bullet", "Para la relación entre dos variables continuas (temperatura vs. tráfico) se usa un diagrama de "
               "dispersión con línea de tendencia (OLS), y para la asociación entre variables se emplea una matriz "
               "de correlación de Spearman (canal de color con escala centrada en 0)."),
    ("bold", "V-B.2 Taxonomía de tareas visuales"),
    ("normal", "El dashboard soporta las tareas visuales identificadas por Munzner [11] para datos tabulares con "
               "dimensión temporal:"),
    ("bullet", "Búsqueda y recuperación de valores (lookup): KPIs de cabecera (registros, tráfico medio, máximo, "
               "hora pico, temperatura media, feriados)."),
    ("bullet", "Comparación: tráfico por hora, por día de la semana, por mes y por estación (barras/líneas)."),
    ("bullet", "Tendencia: serie horaria del tráfico medio con anotación de los picos de la mañana y la tarde."),
    ("bullet", "Distribución: histograma del volumen de tráfico (bimodal) y boxplots por condición meteorológica."),
    ("bullet", "Correlación: matriz de Spearman y dispersión temperatura–tráfico."),
    ("bullet", "Detección de anomalías: contraste feriados vs. días normales y auditoría pre/post (outliers)."),
    ("bold", "V-B.3 Reducción de carga cognitiva (Gestalt y Tufte)"),
    ("normal", "Se aplicaron los principios de Gestalt y el concepto de data-to-ink ratio de Tufte [12] para "
               "minimizar la carga cognitiva:"),
    ("bullet", "Maximización del ratio señal/ruido: eliminación de chartjunk, bordes innecesarios, cuadrículas "
               "redundantes, leyendas duplicadas y saturación tipográfica."),
    ("bullet", "Ley de proximidad: los KPIs se agrupan en una fila superior; los filtros se concentran en la barra "
               "lateral; las vistas se organizan por pestañas temáticas."),
    ("bullet", "Ley de similitud: color y forma consistentes para la misma variable en todas las vistas "
               "(azul = tráfico, naranja = temperatura)."),
    ("bullet", "Ley de cierre: cada gráfico es una unidad visual autocontenida con título, ejes etiquetados y una "
               "línea de caption interpretativa."),
    ("bullet", "Jerarquía tipográfica clara: títulos en negrita, subtítulos por sección y captions en itálica de "
               "menor tamaño para la interpretación."),
    ("bold", "V-B.4 Flujos de interactividad (heurística de Shneiderman)"),
    ("normal", "La interactividad sigue la tríada overview first → zoom and filter → details-on-demand [13]:"),
    ("bullet", "Overview first: tarjetas de KPIs y panorámica general (distribución del tráfico, auditoría "
               "pre/post) en la primera pestaña."),
    ("bullet", "Zoom and filter: filtros cruzados globales y sincronizados en la barra lateral (rango de fechas, "
               "rango de hora, día de la semana, condición meteorológica, estación, feriados, horas pico). Todos los "
               "gráficos reaccionan al mismo subconjunto."),
    ("bullet", "Details-on-demand: tooltips enriquecidos en los gráficos, tabla de inspección de los primeros 200 "
               "registros y descarga del subconjunto filtrado en CSV."),
    ("normal", "El estado filtrado se muestra siempre (registros filtrados y cobertura porcentual), de modo que el "
               "usuario conoce el soporte estadístico de cada vista."),
    ("bold", "V-B.5 Narrativa de datos (Data Storytelling)"),
    ("normal", "La interfaz articula un flujo guiado que transforma datos en decisión:"),
    ("bullet", "Diagnóstico inicial: calidad de los datos (sin nulos ni outliers imposibles tras el pipeline) y "
               "auditoría pre/post de skewness y curtosis."),
    ("bullet", "Detección de patrones y anomalías: patrón bimodal por hora (picos ~07:00 y ~16:00), reducción del "
               "tráfico los fines de semana y en feriados."),
    ("bullet", "Análisis de causa raíz: el factor temporal (hora) es predictor más fuerte que el meteorológico "
               "(ρ de Spearman 0.33 vs. 0.14 para la temperatura); el clima modula pero no determina el tráfico."),
    ("bullet", "Recomendación de acción/decisión: priorizar variables temporales en modelos predictivos, usar "
               "escalado robusto (RobustScaler) para precipitación y considerar transformaciones logarítmicas para "
               "las variables cero-infladas."),
    ("bold", "Conclusiones de la interfaz"),
    ("normal", "La interfaz resultante traduce el pipeline de datos en una herramienta analítica accionable: "
               "maximiza el ratio señal/ruido, usa canales visuales de alta efectividad perceptiva, ofrece "
               "interactividad fluida (overview → filter → details) y articula una narrativa que va del "
               "diagnóstico a la recomendación. El dashboard es reproducible (repositorio con requirements.txt "
               "y datos limpios) y se despliega con Streamlit. Enlace interactivo (tras despliegue): "
               "[URL a completar tras el despliegue en Streamlit Community Cloud]."),
    ("bold", "Figuras anotadas (casos de uso reales)"),
]

FIG_CAPTIONS = [
    ("fig01_auditoria_prepost.png",
     "Fig. 4. Auditoría pre/post: distribuciones de temp y rain_1h antes (crudo) y después (limpio) de la "
     "corrección de outliers."),
    ("fig02_trafico_por_hora.png",
     "Fig. 5. Volumen de tráfico medio por hora del día (canal posición/longitud). Se anotan los dos picos de "
     "congestión (~07:00 y ~16:00)."),
    ("fig03_heatmap_hora_dia.png",
     "Fig. 6. Mapa de calor hora × día de la semana (canal de color, escala secuencial). Zonas oscuras = picos de "
     "congestión en días laborales."),
    ("fig04_boxplot_clima.png",
     "Fig. 7. Distribución del tráfico por condición meteorológica (boxplot, canal posición)."),
    ("fig05_scatter_temp.png",
     "Fig. 8. Dispersión temperatura (°C) vs. volumen de tráfico con línea de tendencia OLS."),
    ("fig06_correlacion.png",
     "Fig. 9. Matriz de correlación de Spearman del dataset procesado (canal de color centrado en 0)."),
    ("fig07_feriado.png",
     "Fig. 10. Tráfico medio en días normales vs. feriados (canal longitud + color funcional)."),
]

NEW_REFS = [
    "[9] L. Wilkinson, The Grammar of Graphics, 2nd ed. New York, NY, USA: Springer, 2005.",
    "[10] W. S. Cleveland and R. McGill, “Graphical perception: Theory, experimentation, and application to the "
    "development of graphical methods,” J. Amer. Statist. Assoc., vol. 79, no. 387, pp. 531–554, 1984.",
    "[11] T. Munzner, Visualization Analysis and Design. Boca Raton, FL, USA: CRC Press, 2014.",
    "[12] E. R. Tufte, The Visual Display of Quantitative Information, 2nd ed. Cheshire, CT, USA: Graphics Press, 2001.",
    "[13] B. Shneiderman, “The eyes have it: A task by data type taxonomy for information visualizations,” in Proc. "
    "IEEE Symp. Visual Languages, 1996, pp. 336–343.",
    "[14] C. Ware, Information Visualization: Perception for Design, 3rd ed. Waltham, MA, USA: Morgan Kaufmann, 2012.",
    "[15] [POR COMPLETAR] Referencia de la biblioteca institucional UEES (sustituir por la referencia elegida por el "
    "equipo).",
]

def main():
    # copy original
    shutil.copyfile(ORIG, OUT_DOCX)

    doc = Document(OUT_DOCX)

    # find REFERENCIAS paragraph
    refs_para = None
    for p in doc.paragraphs:
        if p.text.strip().upper() == "REFERENCIAS":
            refs_para = p
            break
    if refs_para is None:
        raise RuntimeError("No se encontró el párrafo REFERENCIAS")

    # build list of new paragraph specs to insert before refs_para (in final order)
    # We'll insert in reverse order using addprevious.
    to_insert = []  # list of ('type', payload)

    # blank line
    to_insert.append(("blank", None))
    for kind, text in VB_BLOCKS:
        to_insert.append((kind, text))
    # figures
    for fname, cap in FIG_CAPTIONS:
        to_insert.append(("figure", (fname, cap)))
    to_insert.append(("blank", None))

    # insert in reverse
    for kind, payload in reversed(to_insert):
        if kind == "blank":
            new_p = doc.add_paragraph()
            refs_para._p.addprevious(new_p._p)
        elif kind == "bold":
            new_p = doc.add_paragraph()
            r = new_p.add_run(payload)
            r.bold = True
            refs_para._p.addprevious(new_p._p)
        elif kind == "bullet":
            new_p = doc.add_paragraph()
            r = new_p.add_run("•  " + payload)
            r.font.size = Pt(10.5)
            new_p.paragraph_format.left_indent = Inches(0.25)
            refs_para._p.addprevious(new_p._p)
        elif kind == "normal":
            new_p = doc.add_paragraph()
            r = new_p.add_run(payload)
            r.font.size = Pt(10.5)
            refs_para._p.addprevious(new_p._p)
        elif kind == "figure":
            fname, cap = payload
            fpath = FIGS / fname
            # paragraph with picture
            new_p = doc.add_paragraph()
            new_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if fpath.exists():
                run = new_p.add_run()
                run.add_picture(str(fpath), width=Inches(6.2))
            refs_para._p.addprevious(new_p._p)
            # caption
            cap_p = doc.add_paragraph()
            cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = cap_p.add_run(cap)
            r.italic = True
            r.font.size = Pt(9)
            refs_para._p.addprevious(cap_p._p)

    # append new references at end (after [8])
    for ref in NEW_REFS:
        p = doc.add_paragraph(ref)
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        p.paragraph_format.space_after = Pt(2)
        for run in p.runs:
            run.font.size = Pt(9.5)

    doc.save(OUT_DOCX)
    print("saved", OUT_DOCX)

if __name__ == "__main__":
    main()
