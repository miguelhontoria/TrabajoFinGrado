"""
Orquestador principal del simulador SOC. Gestiona la navegación entre pantallas y el pipeline de análisis.

Ejecutar desde /src/: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import time
from base_datos import tablas, consultas
from analisis import ids
from correlacion import siem
from interfaz import historico, ticketing
from streamlit.components.v1 import html
from utilidades.cargar_artefactos import cargar_info_modelo
from utilidades import estilos

st.set_page_config(page_title="Simulador SOC", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed",)

DB_PATH = "soc.db"
tablas.crear_tablas(DB_PATH)

estilos.inyectar_estilos()


if "pantalla" not in st.session_state:
    st.session_state.pantalla = "principal"

if "resultado_analisis" not in st.session_state:
    st.session_state.resultado_analisis = None

if "ultimo_lote" not in st.session_state:
    st.session_state.ultimo_lote = None


def leer_archivo(archivo):
    """Lee CSV o JSON y devuelve un DataFrame."""
    nombre = archivo.name.lower()

    if nombre.endswith(".csv"):
        try:
            df = pd.read_csv(archivo)
        except ValueError:
            raise ValueError("El archivo CSV no tiene un formato válido.")
    elif nombre.endswith(".json"):
        try:
            df = pd.read_json(archivo)
        except ValueError:
            raise ValueError("El archivo JSON no tiene un formato válido.")
    else:
        raise ValueError("Formato no soportado. Solo se aceptan archivos CSV o JSON.")

    return df


def ejecutar_pipeline(df_raw):
    """
    Pipeline completo: parseo → inserción flujos → IDS → SIEM → almacenamiento resultados. Devuelve el DataFrame de resultados enriquecidos.
    """
    if "fecha_ingesta_actual" not in st.session_state:
        st.session_state.fecha_ingesta_actual = time.strftime("%Y-%m-%d %H:%M:%S")
    
    df_limpio, descartadas, mensaje_descartes = tablas.parsear_flujos(df_raw)

    id_lote = tablas.generar_id_lote()
    ids_flujo = tablas.insertar_flujos(df_limpio, id_lote, db_path=DB_PATH)

    df_pred = ids.analizar_flujos(df_limpio, id_lote, ids_flujo)

    df_resultado = siem.correlacionar_alertas(df_pred, df_limpio)

    tablas.insertar_resultados(df_resultado, db_path=DB_PATH)

    if "fecha_ingesta_actual" in st.session_state:
        del st.session_state.fecha_ingesta_actual

    return df_resultado, descartadas, mensaje_descartes, id_lote

if st.session_state.pantalla == "principal":
    col_header, col_modelo = st.columns([1.9, 2.1])

    with col_header:
        st.markdown("""
        <div class="soc-header" style="border-bottom:none;margin-bottom:1rem;">
            <p class="soc-title">Centro de Operaciones de Seguridad</p>
            <p class="soc-subtitle">Simulador SOC - Pantalla principal</p>
            <p class="soc-status">● SISTEMA OPERATIVO</p>
        </div>
        """, unsafe_allow_html=True)

    info_modelo = cargar_info_modelo()

    with col_modelo:
        modelo = info_modelo["modelo"]
        acc = info_modelo["Exactitud(ACC)"]
        prec_macro = info_modelo["Precisión(macro avg)"]
        rec_macro = info_modelo["Exhaustividad(macro avg)"]
        f1_macro = info_modelo["Puntuación F1(macro avg)"]
        n_features = info_modelo["Número de atributos"]
        n_clases = info_modelo["Número de clases"]
        n_train = info_modelo["Número de muestras conjunto entrenamiento"]
        n_test = info_modelo["Número de muestras conjunto test"]

        html_modelo = f"""
        <div style="
            background-color:#161921; border:1px solid #2a2d35; border-radius:4px; padding:1.2rem 1.4rem;
            margin-top:1rem; font-family:'IBM Plex Sans', sans-serif; color:#e8ecf2; font-size:0.85rem;
        ">
            <div style="
                font-family:'IBM Plex Mono', monospace; font-size:0.75rem; letter-spacing:0.12em;
                color:#5a6478; text-transform:uppercase; margin-bottom:1rem;
            ">
                Modelo IDS
            </div>

            <div style="display:flex; gap:1.5rem;">

                <div style="flex:1;">
                    <div style="margin-bottom:0.45rem;color:#8b9ab0;">
                        Modelo: <span style="color:#e8ecf2;font-weight:500;">{modelo}</span>
                    </div>

                    <div style="margin-bottom:0.45rem;color:#8b9ab0;">
                        Exactitud (ACC): <span style="color:#4a9e6b;font-weight:500;">{acc:.2%}</span>
                    </div>

                    <div style="margin-bottom:0.45rem;color:#8b9ab0;">
                        Precisión (macro): <span style="color:#4a9e6b;font-weight:500;">{prec_macro:.1%}</span>
                    </div>

                    <div style="margin-bottom:0.45rem;color:#8b9ab0;">
                        Exhaustividad (macro): <span style="color:#4a9e6b;font-weight:500;">{rec_macro:.1%}</span>
                    </div>

                    <div style="margin-bottom:0.45rem;color:#8b9ab0;">
                        Puntuación F1 (macro): <span style="color:#4a9e6b;font-weight:500;">{f1_macro:.1%}</span>
                    </div>
                </div>

                <div style="flex:1;">
                    <div style="margin-bottom:0.45rem;color:#8b9ab0;">
                        Nº características: <span style="color:#e8ecf2;font-weight:500;">{n_features}</span>
                    </div>

                    <div style="margin-bottom:0.45rem;color:#8b9ab0;">
                        Nº clases: <span style="color:#e8ecf2;font-weight:500;">{n_clases}</span>
                    </div>

                    <div style="margin-bottom:0.45rem;color:#8b9ab0;">
                        Muestras entrenamiento: <span style="color:#e8ecf2;font-weight:500;">{n_train} (80% del total)</span>
                    </div>

                    <div style="margin-bottom:0.45rem;color:#8b9ab0;">
                        Muestras test: <span style="color:#e8ecf2;font-weight:500;">{n_test} (20% del total)</span>
                    </div>
                </div>
            </div>
        </div>
        """

        html(html_modelo, height=280, scrolling=False)


if st.session_state.pantalla == "principal":
    col_tick, col_prin, col_hist = st.columns([1, 2.2, 1], gap="large")

    with col_tick:
        st.markdown("""
        <div class="nav-card">
            <p class="nav-card-label">Módulo</p>
            <p class="nav-card-title">Ticketing</p>
            <p class="nav-card-desc">Gestión de alertas pendientes de revisión por el analista.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

        pendientes = consultas.total_pendientes(db_path=DB_PATH)
        if pendientes > 0:
            st.markdown(
                f"<p style='font-family:IBM Plex Mono,monospace;font-size:0.75rem;"
                f"color:#d94f4f;margin:0'>● {pendientes} alerta{'s' if pendientes != 1 else ''} pendiente{'s' if pendientes != 1 else ''}</p>",
                unsafe_allow_html=True
            )

        if st.button("→ Ir a Ticketing", key="btn_ticketing"):
            st.session_state.pantalla = "ticketing"
            st.rerun()

    with col_hist:
        st.markdown("""
        <div class="nav-card">
            <p class="nav-card-label">Módulo</p>
            <p class="nav-card-title">Histórico</p>
            <p class="nav-card-desc">Consulta de todos los flujos y resultados analizados.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

        if st.button("→ Ir a Histórico", key="btn_historico"):
            st.session_state.pantalla = "historico"
            st.rerun()

    with col_prin:
        st.markdown("""
        <div class="upload-panel">
            <p class="upload-label">Análisis de flujos</p>
            <p class="upload-title">Analizar tráfico de red</p>
            <p class="upload-note">Selecciona un archivo para analizar, solo se admiten archivos en formato CSV o JSON</p>
        """, unsafe_allow_html=True)

        archivo = st.file_uploader(" ", type=["csv", "json"], label_visibility="collapsed")

        if st.session_state.get("mensaje_descartes"):
            st.warning(st.session_state.mensaje_descartes)
            st.session_state.mensaje_descartes = None

        if archivo is not None:
            if st.button("Analizar flujos", key="btn_analizar"):
                with st.spinner("Analizando flujos..."):
                    try:
                        df_raw = leer_archivo(archivo)
                        df_resultado, descartadas, mensaje_descartes, id_lote = ejecutar_pipeline(df_raw)

                        st.session_state.resultado_analisis = df_resultado
                        st.session_state.ultimo_lote = id_lote

                        if mensaje_descartes:
                            st.session_state.mensaje_descartes = mensaje_descartes
                        else:
                            st.session_state.mensaje_descartes = None

                        st.rerun()

                    except ValueError as e:
                        st.error(str(e))
                        st.session_state.resultado_analisis = None

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.resultado_analisis is not None:
            id_lote = st.session_state.ultimo_lote

            st.markdown(f"<p class='results-header'>Resultados — lote {id_lote}</p>", unsafe_allow_html=True)

            df_lote = consultas.obtener_resultados_lote(id_lote, db_path=DB_PATH)

            LIMITE_TABLA_PRINCIPAL = 100

            df_resultado = st.session_state.resultado_analisis
            df_mostrar = df_lote.head(LIMITE_TABLA_PRINCIPAL)

            if len(df_lote) > LIMITE_TABLA_PRINCIPAL:
                st.caption(
                    f"Mostrando los primeros {LIMITE_TABLA_PRINCIPAL} resultados de {len(df_resultado)} totales."
                    f"Consulta el histórico completo en la pantalla de Histórico."
                )

            ataques = df_lote[df_lote["prediccion"] != "BENIGN"]
            benignos = df_lote[df_lote["prediccion"] == "BENIGN"]
            altos = ataques[ataques["severidad"] == "ALTA"]
            criticos = ataques[ataques["severidad"] == "CRITICA"]

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total flujos", len(df_resultado))
            m2.metric("Ataques detectados", len(ataques))
            m3.metric("Benignos", len(benignos))
            m4.metric("Severidad ALTA", len(altos))
            m5.metric("Severidad CRÍTICA", len(criticos))

            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

            tabla_html = """
<table style="width:100%;border-collapse:collapse;font-size:0.8rem;">
<thead>
<tr style="border-bottom:1px solid #2a2d35;color:#5a6478;
        font-family:'IBM Plex Mono',monospace;font-size:0.7rem;
        letter-spacing:0.08em;text-transform:uppercase">
<th style="padding:6px 8px;text-align:left">ID Resultado</th>
<th style="padding:6px 8px;text-align:left">ID Flujo</th>
<th style="padding:6px 8px;text-align:left">Fecha análisis</th>
<th style="padding:6px 8px;text-align:left">Predicción</th>
<th style="padding:6px 8px;text-align:left">Confianza</th>
<th style="padding:6px 8px;text-align:left">¿Baja confianza?</th>
</tr>
</thead>
<tbody>
"""

            for _, fila in df_mostrar.iterrows():
                color_pred = "#d94f4f" if fila["prediccion"] != "BENIGN" else "#00f925"

                if fila["baja_confianza"] == 1:
                    estado = "<span style='color:#c9a227;font-family:IBM Plex Mono,monospace'>SÍ</span>"
                else:
                    estado = "<span style='color:#4a9e6b;font-family:IBM Plex Mono,monospace'>NO (predicción fiable)</span>"

                tabla_html += f"""
<tr style="border-bottom:1px solid #1e2128;">
<td style="padding:6px 8px;color:#5a6478;font-family:'IBM Plex Mono',monospace">{fila["id_resultado"]}</td>
<td style="padding:6px 8px;color:#5a6478;font-family:'IBM Plex Mono',monospace">{fila["id_flujo"]}</td>
<td style="padding:6px 8px;color:#8b9ab0;font-family:'IBM Plex Mono',monospace">{fila["fecha_analisis"]}</td>
<td style="padding:6px 8px;color:{color_pred}">{fila["prediccion"]}</td>
<td style="padding:6px 8px;color:#8b9ab0;font-family:'IBM Plex Mono',monospace">{fila["confianza"]:.1%}</td>
<td style="padding:6px 8px">{estado}</td>
</tr>
"""
            tabla_html += """
</tbody>
</table>
"""
            st.markdown(tabla_html, unsafe_allow_html=True)


elif st.session_state.pantalla == "historico":
    col_header, col_chart = st.columns([1.9, 1], vertical_alignment="top")

    with col_header:
        st.markdown("""
        <div class="soc-header" style="border-bottom:none;margin-bottom:1rem;">
            <p class="soc-title">Centro de Operaciones de Seguridad</p>
            <p class="soc-subtitle">Simulador SOC - HISTÓRICO</p>
            <p class="soc-status">● SISTEMA OPERATIVO</p>
        </div>
        """, unsafe_allow_html=True)

    with col_chart:
        st.markdown("""
        <div style="display:flex; justify-content:flex-end; align-items:flex-start; margin-top:0; padding-top:0;">
        """, unsafe_allow_html=True)

        historico.grafico_distribucion()

        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("← Volver"):
        st.session_state.pantalla = "principal"
        st.rerun()

    historico.render()


elif st.session_state.pantalla == "ticketing":
    col_header, col_chart = st.columns([1, 1], vertical_alignment="top")

    with col_header:
        st.markdown("""
        <div class="soc-header" style="border-bottom:none;margin-bottom:1rem;">
            <p class="soc-title">Centro de Operaciones de Seguridad</p>
            <p class="soc-subtitle">Simulador SOC - TICKETING</p>
            <p class="soc-status">● SISTEMA OPERATIVO</p>
        </div>
        """, unsafe_allow_html=True)

    with col_chart:
        st.markdown("""
        <div style="display:flex; justify-content:flex-end; align-items:flex-start; margin-top:0; padding-top:0;">
        """, unsafe_allow_html=True)

        ticketing.grafico_importancias()

        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("← Volver"):
        st.session_state.pantalla = "principal"
        st.rerun()

    ticketing.render()
