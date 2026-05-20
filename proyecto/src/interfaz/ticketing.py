"""
Pantalla de Ticketing del simulador SOC.
Muestra:
  - Gráfico de barras de importancia de características del modelo (arriba derecha)
  - Tabla de alertas pendientes de revisión (con detalle de cada alerta)
  - Tabla de flujos correspondientes a esas alertas (con detalle de cada flujo)
  - Distribución de ataques por severidad
"""

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from base_datos import consultas
from utilidades.cargar_artefactos import cargar_importancia_caracteristicas

DB_PATH = "soc.db"


def grafico_importancias():
    """Genera un gráfico de barras horizontal con las características más importantes."""
    imp = cargar_importancia_caracteristicas()

    df = pd.DataFrame(list(imp.items()), columns=["caracteristica", "importancia"])
    df = df.sort_values("importancia", ascending=True).tail(10)  

    st.markdown(
        '<p style="font-family:IBM Plex Mono,monospace;font-size:0.73rem; letter-spacing:0.1em;color:#5a6478;text-transform:uppercase;'
        'margin-bottom:0.1rem;margin-top:0.2rem"> Importancia de características del modelo durante el entrenamiento</p>', unsafe_allow_html=True
    )

    fig, ax = plt.subplots(figsize=(8, 3.4), facecolor="#161921")
    ax.set_facecolor("#161921")

    ax.barh(df["caracteristica"], df["importancia"], color="#4a9e6b")
    ax.set_xlabel("Importancia", color="#aeb8c7")
    ax.set_ylabel("Nombre característica", color="#aeb8c7")
    ax.tick_params(axis="x", colors="#aeb8c7")
    ax.tick_params(axis="y", colors="#c8cdd8")
    ax.grid(axis="x", linestyle="--", alpha=0.2)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def mostrar_detalle_flujo(id_flujo):
    """
    Muestra todas las variables de un flujo, los 3 metadatos y las 24 características del flujo divididas en 2 columnas de 12.
    """
    detalle = consultas.obtener_detalle_flujo(int(id_flujo), db_path=DB_PATH)
    if not detalle:
        st.warning(f"No se encontró el flujo con id {id_flujo}.")
        return
 
    st.markdown(
        f'<p style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;'
        f'color:#4a9e6b;margin-bottom:0.4rem">Flujo #{id_flujo} — Lote {detalle.get("id_lote", "—")} — {detalle.get("fecha_ingesta", "—")}</p>',
        unsafe_allow_html=True
    )
 
    caracteristicas = {k: v for k, v in detalle.items() if k not in ("id_flujo", "id_lote", "fecha_ingesta")}
    items = list(caracteristicas.items())
    mitad = len(items) // 2
    dc1, dc2 = st.columns(2)
    with dc1:
        for k, v in items[:mitad]:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between; font-size:0.78rem;padding:2px 0;border-bottom:1px solid #1e2128">'
                f'<span style="color:#5a6478;font-family:IBM Plex Mono,monospace">{k}</span>'
                f'<span style="color:#c8cdd8">{round(float(v), 4) if v is not None else "—"}</span> </div>', unsafe_allow_html=True
            )
    with dc2:
        for k, v in items[mitad:]:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between; font-size:0.78rem;padding:2px 0;border-bottom:1px solid #1e2128">'
                f'<span style="color:#5a6478;font-family:IBM Plex Mono,monospace">{k}</span>'
                f'<span style="color:#c8cdd8">{round(float(v), 4) if v is not None else "—"}</span></div>', unsafe_allow_html=True
            )

def mostrar_detalle_resultado(id_resultado):
    """
    Muestra de la alerta seleccionada sus metadatos además de su prediccion, severidad, confianza, baja_confianza y la recomendación.
    Debajo de esos datos se muestra el recuadro para escribir las notas y marcar como revisada la alerta.
    """
    detalle = consultas.obtener_detalle_resultado(int(id_resultado), db_path=DB_PATH)

    if not detalle:
        st.warning(f"No se encontró el resultado con id {id_resultado}.")
        return

    st.markdown(
        f'<p style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;color:#4a9e6b;margin-bottom:0.6rem">'
        f'Resultado #{detalle.get("id_resultado", "—")} — Flujo #{detalle.get("id_flujo", "—")} — '
        f'Lote {detalle.get("id_lote", "—")} — {detalle.get("fecha_analisis", "—")}</p>', unsafe_allow_html=True
    )

    c1, c4 = st.columns([2.5, 2])

    with c1:
        st.metric("Predicción", detalle.get("prediccion", "—"))
        
    with c4:
        st.metric("Severidad", detalle.get("severidad", "-"))

    c2, c3 = st.columns([2.5,2])

    with c2:
        st.metric("Confianza", f"{float(detalle.get('confianza', 0)):.1%}")

    with c3:
        baja = detalle.get("baja_confianza")
        texto_baja = "Sí" if baja == 1 else "No (predicción fiable)"
        st.metric("Baja confianza", texto_baja)

    recomendacion = detalle.get("recomendacion")
    st.markdown(
        f'<div style="margin-top:1rem"> <span style="font-family:IBM Plex Mono,monospace;'
        f'font-size:0.72rem;color:#5a6478;letter-spacing:0.08em; text-transform:uppercase">Recomendación</span>'
        f'<div style="margin-top:0.35rem;font-size:0.82rem; color:#c8cdd8;padding:0.7rem 0.9rem;'
        f'background:#161921;border:1px solid #2a2d35; border-radius:4px">{recomendacion if recomendacion else "—"}</div>'
        f'</div>', unsafe_allow_html=True
    )

    st.markdown(
        '<div style="margin-top:0.8rem"><span style="font-family:IBM Plex Mono,monospace;'
        'font-size:0.72rem;color:#5a6478;letter-spacing:0.08em;text-transform:uppercase"> Notas analista</span></div>', unsafe_allow_html=True
    )
 
    notas_key = f"notas_{id_resultado}"
    notas_actuales = detalle.get("notas_analista") or ""
 
    MAX_NOTAS = 5000

    notas_input = st.text_area(
        label="notas_analista", value=notas_actuales, placeholder="Escribe aquí las observaciones sobre este incidente (máximo 5000 caracteres)",
        height=100, label_visibility="collapsed", key=notas_key,
    )

    if len(notas_input) > MAX_NOTAS:
        st.warning(f"Has superado el límite de {MAX_NOTAS} caracteres.")
        notas_input = notas_input[:MAX_NOTAS]

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
 
    btn_key = f"marcar_revisado_{id_resultado}"
 
    if st.button("Marcar como revisado", key=btn_key, type="primary"):
        notas_guardar = notas_input.strip() if notas_input.strip() else None
        consultas.marcar_revisado(id_resultado=int(id_resultado), notas=notas_guardar, db_path=DB_PATH,)
        st.session_state.tabla_ticketing_version += 1
        st.success(f"Resultado #{id_resultado} marcado como revisado. Ya no aparecerá en Ticketing.")
        st.rerun()


def render():
    """
    Función principal que maneja las tablas, las secciones con los detalles y la distribución por severidad.
    """
    st.markdown("<hr>", unsafe_allow_html=True)

    col_flujos, col_resultados = st.columns([1.3, 2])

    with col_flujos:
        st.markdown(
            '<p style="font-family:IBM Plex Mono,monospace;font-size:0.7rem; letter-spacing:0.12em;color:#5a6478;text-transform:uppercase;'
            'margin-bottom:0.6rem">Flujos correspondientes a los ataques pendientes de revisión</p>', unsafe_allow_html=True
        )

        with st.expander("Filtros de flujos", expanded=False):
            fc1, fc2, fc3, fc4 = st.columns(4)

            f_id_flujo = fc1.number_input("ID flujo", min_value=1, step=1, value=None, placeholder="ID", key="tk_id_flujo")
            f_id_lote = fc2.text_input("ID lote", key="tk_id_lote")
            f_fecha_desde = fc3.text_input("Desde (YYYY-MM-DD HH:MM:SS)", key="tk_desde")
            f_fecha_hasta = fc4.text_input("Hasta (YYYY-MM-DD HH:MM:SS)", key="tk_hasta")

            filtros_actuales = (f_id_flujo, f_id_lote, f_fecha_desde, f_fecha_hasta)

            if "ticketing_filtros_previos" not in st.session_state:
                st.session_state.ticketing_filtros_previos = filtros_actuales

            if filtros_actuales != st.session_state.ticketing_filtros_previos:
                st.session_state.pag_ticketing = 1
                st.session_state.ticketing_filtros_previos = filtros_actuales

        pagina = st.number_input("Página", min_value=1, value=1, step=1, key="pag_ticketing")
        offset = (pagina - 1) * 30

        df_flujos = consultas.obtener_flujos_ataques(
            id_flujo=f_id_flujo, id_lote=f_id_lote.strip() if f_id_lote.strip() else None,
            fecha_desde=f_fecha_desde.strip() if f_fecha_desde.strip() else None,
            fecha_hasta=f_fecha_hasta.strip() if f_fecha_hasta.strip() else None, offset=offset, db_path=DB_PATH,
        )

        st.caption(f"Página {pagina} — {len(df_flujos)} ataque(s) mostrado(s)")

        if df_flujos.empty:
            st.caption("No hay ataques pendientes de revisión.")

        else:
            evento_flujo = st.dataframe(
                df_flujos[["id_flujo", "id_lote", "fecha_ingesta"]], use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row", key="tabla_ticketing_flujos",
                column_config={
                    "id_flujo": st.column_config.NumberColumn("ID flujo"),
                    "id_lote": st.column_config.TextColumn("ID lote"),
                    "fecha_ingesta": st.column_config.TextColumn("Fecha ingesta"),
                }
            )

            st.caption( f"{len(df_flujos)} ataque(s) mostrado(s) — máximo 30 por página")

            filas_sel = evento_flujo.selection.rows
            if filas_sel:
                fila = filas_sel[0]
                id_flujo_sel = df_flujos.iloc[fila]["id_flujo"]
                st.markdown("<hr style='margin:0.6rem 0'>", unsafe_allow_html=True)
                mostrar_detalle_flujo(id_flujo_sel)

            st.markdown("<hr>", unsafe_allow_html=True)

    with col_resultados:
        st.markdown(
            '<p style="font-family:IBM Plex Mono,monospace;font-size:0.7rem; letter-spacing:0.12em;color:#5a6478;text-transform:uppercase;'
            'margin-bottom:0.6rem">Resultados pendientes de revisión</p>', unsafe_allow_html=True
        )

        with st.expander("Filtros de resultados", expanded=False):
            rc1, rc2, rc3, rc4 = st.columns(4)
            r_id_res = rc1.number_input("ID resultado", min_value=1, step=1, value=None, placeholder="ID", key="tk_res_id")
            r_id_flujo = rc2.number_input("ID flujo", min_value=1, step=1, value=None, placeholder="ID", key="tk_res_flujo")
            r_id_lote = rc3.text_input("ID lote", key="tk_res_lote")
            r_prediccion = rc4.text_input("Predicción", key="tk_res_pred")
            
            rc5, rc6, rc7, rc8 = st.columns(4)
            r_desde = rc5.text_input("Desde (YYYY-MM-DD HH:MM:SS)", key="tk_res_desde")
            r_hasta = rc6.text_input("Hasta (YYYY-MM-DD HH:MM:SS)", key="tk_res_hasta")
            r_confianza = rc7.number_input("Confianza", min_value=0.0, max_value=100.0, step=0.5, value=None, placeholder="0 - 100 %",
                key="tk_res_conf")
            r_severidad = rc8.selectbox("Severidad", ["Todas", "Info", "Baja", "Media", "Alta", "Crítica"], key="tk_res_sev")

            filtros_actuales_res = (r_id_res, r_id_flujo, r_id_lote, r_prediccion, r_desde, r_hasta, r_confianza, r_severidad)

            if "ticketing_resultados_previos" not in st.session_state:
                st.session_state.ticketing_resultados_previos = filtros_actuales_res

            if filtros_actuales_res != st.session_state.ticketing_resultados_previos:
                st.session_state.pag_ticketing_res = 1
                st.session_state.ticketing_resultados_previos = filtros_actuales_res

        map_sev = {"Info": "INFO", "Baja": "BAJA", "Media": "MEDIA", "Alta": "ALTA", "Crítica": "CRITICA",}

        severidad_val = None
        if r_severidad != "Todas":
            severidad_val = map_sev[r_severidad]

        confianza_val = None

        if r_confianza is not None:
            confianza_val = (
                r_confianza / 100
                if r_confianza > 1
                else r_confianza
            )

        pagina = st.number_input("Página", min_value=1, value=1, step=1, key="pag_ticketing_res")
        offset = (pagina - 1) * 30

        df_res = consultas.obtener_pendientes_ticketing(
            id_resultado=r_id_res, id_flujo=r_id_flujo, id_lote=r_id_lote.strip() if r_id_lote.strip() else None,
            fecha_desde=r_desde.strip() if r_desde.strip() else None, fecha_hasta=r_hasta.strip() if r_hasta.strip() else None,
            prediccion=r_prediccion.strip() if r_prediccion.strip() else None,
            confianza=confianza_val, severidad=severidad_val, offset=offset, db_path=DB_PATH,
        )

        st.caption(f"Página {pagina} — {len(df_res)} resultado(s) mostrado(s)")

        if df_res.empty:
            st.caption("No hay resultados pendientes de revisión.")

        else:
            df_vista = df_res.copy()
            df_vista["confianza"] = df_vista["confianza"].apply(lambda v: (f"{float(v):.1%}" if pd.notna(v) else "—"))
            
            if "tabla_ticketing_version" not in st.session_state:
                st.session_state.tabla_ticketing_version = 0
            
            evento_res = st.dataframe(
                df_vista[["id_resultado","id_flujo","id_lote","fecha_analisis","prediccion","confianza","severidad"]],
                use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row",
                key=f"tabla_ticketing_resultados_{st.session_state.tabla_ticketing_version}",
                column_config={
                    "id_resultado": st.column_config.NumberColumn("ID resultado"),
                    "id_flujo": st.column_config.NumberColumn("ID flujo"),
                    "id_lote": st.column_config.TextColumn("ID lote"),
                    "fecha_analisis": st.column_config.TextColumn("Fecha análisis"),
                    "prediccion": st.column_config.TextColumn("Predicción"),
                    "confianza": st.column_config.TextColumn("Confianza",width="small"),
                    "severidad": st.column_config.TextColumn("Severidad",width="small"),
                }
            )

            st.caption(f"{len(df_res)} resultado(s) mostrado(s) — máximo 30 por página")

            filas_res_sel = evento_res.selection.rows

            if filas_res_sel:
                fila = filas_res_sel[0]
                id_res_sel = df_res.iloc[fila]["id_resultado"]
                st.markdown("<hr style='margin:0.6rem 0'>", unsafe_allow_html=True)
                mostrar_detalle_resultado(id_res_sel)

            st.markdown("<hr>", unsafe_allow_html=True)

            st.markdown(
                '<p style="font-family:IBM Plex Mono,monospace;font-size:0.68rem; letter-spacing:0.12em;color:#5a6478;text-transform:uppercase;'
                'margin-bottom:0.5rem">Distribución de ataques por severidad</p>', unsafe_allow_html=True
            )

            df_sev = consultas.conteo_por_severidad(db_path=DB_PATH)

            if not df_sev.empty:
                total_global = int(df_sev["total"].sum())

                html_sev = """
                <div style="display:flex; flex-wrap:wrap; gap:0.55rem; max-height:220px; overflow-y:auto; padding-right:4px;">
                """

                colores = {"CRITICA":"#ff3b3b", "ALTA":"#ff7b00", "MEDIA":"#e0c200", "BAJA":"#4a9e6b", "INFO":"#00f925"}

                for _, row in df_sev.iterrows():
                    sev = str(row["severidad"])
                    total = int(row["total"])
                    pct = (total / total_global) * 100

                    color = colores.get(sev.upper(), "#c8cdd8")

                    html_sev += (
                        '<div style="background:#161921; border:1px solid #2a2d35; border-radius:4px; padding:0.55rem 0.75rem; min-width:170px; '
                        'flex:1 1 170px; max-width:220px;">'

                        f'<div style="color:{color}; font-size:0.78rem; font-weight:600; margin-bottom:0.22rem; word-break:break-word;">{sev}</div>'
                        f'<div style="color:#c8cdd8; font-size:0.84rem;">{total} flujo(s)</div>'
                        f'<div style="color:#5a6478; font-size:0.69rem; margin-top:0.15rem;"> {pct:.1f}% del total</div>'

                        '</div>'
                    )

                html_sev += "</div>"

                st.markdown(html_sev, unsafe_allow_html=True)
                st.caption(f"{total_global} flujo(s) analizado(s) pendiente(s)")

            else:
                st.caption("No hay flujos registrados.")

