"""
Pantalla de Histórico del simulador SOC.
Muestra:
  - Gráfico circular de distribución de clases del modelo (arriba derecha)
  - Tabla de flujos analizados (con detalle de cada flujo)
  - Tabla de resultados resumida (con detalle de cada resultado)
  - Detalle contextual del resultado seleccionado
  - Resumen de flujos por lotes
  - Distribución de clases por predicción
"""

import streamlit as st
import matplotlib.pyplot as plt
from base_datos import consultas
from utilidades.cargar_artefactos import cargar_distribucion_clases

DB_PATH = "soc.db"


def grafico_distribucion():
    """Genera el gráfico circular de distribución de clases del modelo."""
    distribucion = cargar_distribucion_clases()

    etiquetas = list(distribucion.keys())
    valores = list(distribucion.values())
    total = sum(valores)

    umbral = total * 0.005

    etiq_plot = []
    val_plot  = []
    otros_val = 0

    for e, v in zip(etiquetas, valores):
        if v >= umbral:
            etiq_plot.append(e)
            val_plot.append(v)
        else:
            otros_val += v

    if otros_val > 0:
        etiq_plot.append("Otros")
        val_plot.append(otros_val)

    n = len(etiq_plot)
    cmap = plt.cm.get_cmap("tab20", n)
    colores = [cmap(i) for i in range(n)]

    st.markdown(
        '<p style="font-family:IBM Plex Mono,monospace;font-size:0.73rem;'
        'letter-spacing:0.1em;color:#5a6478; text-transform:uppercase; margin-bottom:0.1rem;margin-top:0.2rem">'
        'Distribución de clases del modelo (24 en la práctica) </p>', unsafe_allow_html=True
    )

    col_leyenda, col_grafico = st.columns([1, 1.8])

    with col_leyenda:
        items = []
        for e, v, c in zip(etiq_plot, val_plot, colores):
            hex_c = "#{:02x}{:02x}{:02x}".format(int(c[0]*255), int(c[1]*255), int(c[2]*255))
            pct = v / total * 100
            items.append(
                f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:2.5px">'
                f'<span style="width:10px;height:10px;border-radius:50%;background:{hex_c}"></span>'
                f'<span style="font-size:0.78rem;color:#aeb8c7"> {e} <span style="color:#5a6478">({pct:.1f}%)</span> </span> </div>'
            )

        st.markdown(f'<div style="max-height:180px;overflow-y:auto;padding-right:6px">' + "".join(items) + '</div>', unsafe_allow_html=True)

    with col_grafico:
        fig, ax = plt.subplots(figsize=(3, 3), facecolor="#161921")

        ax.set_facecolor("#161921")
        ax.pie(val_plot, colors=colores, startangle=90, wedgeprops={"linewidth": 0.4, "edgecolor": "#0f1117"}, radius=1.0)
        ax.add_patch(plt.Circle((0, 0), 0.58, color="#161921"))
        ax.text(0, 0.1, "Clases", ha="center", va="center", fontsize=15.8, color="#5a6478", fontfamily="monospace")
        ax.text(0, -0.15, f"{len(etiq_plot)}", ha="center", va="center", fontsize=20, fontweight="bold", color="#c8cdd8")

        fig.tight_layout(pad=0.15)
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
    Muestra del resultado seleccionado sus metadatos y su recomendacion solamente o prediccion, severidad, confianza, baja_confianza, 
    recomendación y notas del analista, en función de si ya se ha revisado o no.
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

    if detalle.get("revisado") == 0:
        st.markdown("""
        <style>
        [data-testid="stMetricValue"] {font-size: 1.5rem !important; word-break: break-word !important; white-space: normal !important;}
        </style>
        """, unsafe_allow_html=True)    
        recomendacion = detalle.get("recomendacion")
        colores = {"CRITICA":"#ff3b3b", "ALTA":"#ff7b00", "MEDIA":"#e0c200", "BAJA":"#4a9e6b"}
        severidad = detalle.get("severidad", "INFO")    
        
        texto_subtitulo = ""
        texto_caja = "—"

        if recomendacion:
            if " - " in recomendacion:
                partes = recomendacion.split(" - ", 1)
                texto_caja = partes[0].strip()
                texto_subtitulo = partes[1].strip()
            else:
                texto_caja = recomendacion.strip()

        color_subtitulo = colores.get(severidad, "#c8cdd8")

        html_subtitulo = ""
        if texto_subtitulo:
            html_subtitulo = f' <span style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:{color_subtitulo};margin-left:0.8rem;text-transform:none;">— {texto_subtitulo}</span>'

        st.markdown(
            f'<div style="margin-top:1rem">'
            f'  <div style="display:flex; align-items:center;">'
            f'    <span style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:#5a6478;letter-spacing:0.08em;text-transform:uppercase">Recomendación</span>'
            f'    {html_subtitulo}'
            f'  </div>'
            f'  <div style="margin-top:0.35rem;font-size:0.82rem;color:#c8cdd8;padding:0.7rem 0.9rem;background:#161921;border:1px solid #2a2d35;border-radius:4px">{texto_caja}</div>'
            f'</div>', unsafe_allow_html=True
        )

    else:
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
        colores = {"CRITICA":"#ff3b3b", "ALTA":"#ff7b00", "MEDIA":"#e0c200", "BAJA":"#4a9e6b"}
        severidad = detalle.get("severidad", "INFO")    
        
        texto_subtitulo = ""
        texto_caja = "—"

        if recomendacion:
            if " - " in recomendacion:
                partes = recomendacion.split(" - ", 1)
                texto_caja = partes[0].strip()
                texto_subtitulo = partes[1].strip()
            else:
                texto_caja = recomendacion.strip()

        color_subtitulo = colores.get(severidad, "#c8cdd8")

        html_subtitulo = ""
        if texto_subtitulo:
            html_subtitulo = f' <span style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:{color_subtitulo};margin-left:0.8rem;text-transform:none;">— {texto_subtitulo}</span>'

        st.markdown(
            f'<div style="margin-top:1rem">'
            f'  <div style="display:flex; align-items:center;">'
            f'    <span style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:#5a6478;letter-spacing:0.08em;text-transform:uppercase">Recomendación</span>'
            f'    {html_subtitulo}'
            f'  </div>'
            f'  <div style="margin-top:0.35rem;font-size:0.82rem;color:#c8cdd8;padding:0.7rem 0.9rem;background:#161921;border:1px solid #2a2d35;border-radius:4px">{texto_caja}</div>'
            f'</div>', unsafe_allow_html=True
        )

        notas = detalle.get("notas_analista")

        st.markdown(
            f'<div style="margin-top:0.8rem"> <span style="font-family:IBM Plex Mono,monospace;'
            f'font-size:0.72rem;color:#5a6478;letter-spacing:0.08em; text-transform:uppercase">'
            f'Notas analista </span> <div style="margin-top:0.35rem;font-size:0.82rem;'
            f'color:#c8cdd8;padding:0.7rem 0.9rem; background:#161921;border:1px solid #2a2d35;'
            f'border-radius:4px"> {notas if notas else "El analista no añadió ninguna nota."} </div> </div>', unsafe_allow_html=True
        )


def render():
    """
    Función principal que maneja las tablas, las secciones con los detalles, el resumen por lotes y la distribución de clases por predicción.
    """
    st.markdown("<hr>", unsafe_allow_html=True)

    col_flujos, col_resultados = st.columns([1.3, 2])

    with col_flujos:
        st.markdown(
            '<p style="font-family:IBM Plex Mono,monospace;font-size:0.7rem; letter-spacing:0.12em;color:#5a6478;text-transform:uppercase;'
            'margin-bottom:0.6rem">Flujos analizados</p>', unsafe_allow_html=True
        )

        with st.expander("Filtros de flujos", expanded=False):
            fc1, fc2 = st.columns(2)
            f_id_flujo = fc1.number_input("ID flujo", min_value=1, step=1, value=None, placeholder="ID", key="hf_id_flujo")
            f_id_lote = fc2.text_input("ID lote", key="hf_id_lote")

            fc3, fc4 = st.columns(2)
            f_fecha_desde = fc3.text_input("Desde (YYYY-MM-DD HH:MM:SS)", key="hf_desde")
            f_fecha_hasta = fc4.text_input("Hasta (YYYY-MM-DD HH:MM:SS)", key="hf_hasta")

            filtros_actuales = (f_id_flujo, f_id_lote, f_fecha_desde, f_fecha_hasta)

            if "filtros_flujos_previos" not in st.session_state:
                st.session_state.filtros_flujos_previos = filtros_actuales

            if filtros_actuales != st.session_state.filtros_flujos_previos:
                st.session_state.pag_flujos = 1
                st.session_state.filtros_flujos_previos = filtros_actuales

        pagina = st.number_input("Página", min_value=1, value=1, step=1, key="pag_flujos")
        offset = (pagina - 1) * 30

        df_flujos = consultas.obtener_flujos(
            id_flujo=f_id_flujo, id_lote=f_id_lote.strip() if f_id_lote.strip() else None,
            fecha_desde=f_fecha_desde.strip() if f_fecha_desde.strip() else None, 
            fecha_hasta=f_fecha_hasta.strip() if f_fecha_hasta.strip() else None,
            offset=offset, db_path=DB_PATH,
        )

        st.caption(f"Página {pagina} — {len(df_flujos)} flujo(s) mostrado(s)")

        if df_flujos.empty:
            st.caption("No hay flujos que mostrar.")

        else:
            evento_flujo = st.dataframe(
                df_flujos[["id_flujo", "id_lote", "fecha_ingesta"]], use_container_width=True, hide_index=True, on_select="rerun",
                selection_mode="single-row", key="tabla_flujos",
                column_config={
                    "id_flujo": st.column_config.NumberColumn("ID flujo"),
                    "id_lote": st.column_config.TextColumn("ID lote"),
                    "fecha_ingesta": st.column_config.TextColumn("Fecha ingesta"),
                }
            )

            st.caption(f"{len(df_flujos)} flujo(s) mostrado(s) — máximo 30 más recientes")

            filas_sel = evento_flujo.selection.rows

            if filas_sel:
                fila = filas_sel[0]
                id_flujo_sel = df_flujos.iloc[fila]["id_flujo"]
                st.markdown("<hr style='margin:0.6rem 0'>",unsafe_allow_html=True)
                mostrar_detalle_flujo(id_flujo_sel)

            st.markdown("<hr>", unsafe_allow_html=True)

            st.markdown(
                '<p style="font-family:IBM Plex Mono,monospace;font-size:0.68rem; letter-spacing:0.12em;color:#5a6478;text-transform:uppercase;'
                'margin-bottom:0.5rem">Resumen de flujos por lotes</p>', unsafe_allow_html=True
            )

            df_lotes = consultas.conteo_flujos_por_lote(db_path=DB_PATH)

            if not df_lotes.empty:
                html_lotes = """
                <div style="max-height:328px; overflow-y:auto; border:1px solid #2a2d35; border-radius:4px; 
                background:#161921; padding:0.4rem 0.6rem; ">
                """

                for _, row in df_lotes.iterrows():
                    html_lotes += (
                        '<div style=" display:flex; justify-content:space-between; align-items:center; padding:0.45rem 0;'
                        'border-bottom:1px solid #1e2128; font-size:0.78rem; ">'
                        '<div>'

                        f'<span style=" color:#4a9e6b; font-family:\'IBM Plex Mono\', monospace; "> {row["id_lote"]} </span>'
                        f'<span style=" color:#5a6478; margin-left:0.6rem; font-size:0.72rem; "> {row["fecha"]} </span>'

                        '</div>'
                        f'<div style=" color:#c8cdd8; font-weight:600; "> {row["total_flujos"]} flujos </div>'
                        '</div>'
                    )

                html_lotes += "</div>"

                st.markdown(html_lotes, unsafe_allow_html=True)
                st.caption(f"{len(df_lotes)} lote(s) registrados actualmente")

            else:
                st.caption("No hay lotes registrados.")

    with col_resultados:
        st.markdown(
            '<p style="font-family:IBM Plex Mono,monospace;font-size:0.7rem; letter-spacing:0.12em;color:#5a6478;text-transform:uppercase;'
            'margin-bottom:0.6rem">Resultados del análisis</p>', unsafe_allow_html=True
        )

        with st.expander("Filtros de resultados", expanded=False):
            rc1, rc2, rc3, rc4 = st.columns(4)
            r_id_res = rc1.number_input("ID resultado", min_value=1, step=1, value=None, placeholder="ID", key="hr_id_res")
            r_id_flujo = rc2.number_input("ID flujo", min_value=1, step=1, value=None, placeholder="ID", key="hr_id_flujo")
            r_id_lote = rc3.text_input("ID lote", key="hr_id_lote")
            r_prediccion = rc4.text_input("Predicción", key="hr_pred")

            rc5, rc6, rc7 = st.columns([1, 1, 0.8])
            r_desde = rc5.text_input("Desde (YYYY-MM-DD HH:MM:SS)", key="hr_desde")
            r_hasta = rc6.text_input("Hasta (YYYY-MM-DD HH:MM:SS)", key="hr_hasta")
            r_revisado = rc7.selectbox("Revisado", ["Todos", "Pendiente (0)", "Revisado (1)"], key="hr_rev")

            filtros_actuales_res = (r_id_res, r_id_flujo, r_id_lote, r_prediccion, r_desde, r_hasta, r_revisado)

            if "filtros_resultados_previos" not in st.session_state:
                st.session_state.filtros_resultados_previos = filtros_actuales_res

            if filtros_actuales_res != st.session_state.filtros_resultados_previos:
                st.session_state.pag_resultados = 1
                st.session_state.filtros_resultados_previos = filtros_actuales_res

        revisado_val = None
        if r_revisado == "Pendiente (0)":
            revisado_val = 0
        elif r_revisado == "Revisado (1)":
            revisado_val = 1

        pagina = st.number_input("Página", min_value=1, value=1, step=1, key="pag_resultados")
        offset = (pagina - 1) * 30

        df_res = consultas.obtener_resultados_historico(
            id_resultado=r_id_res, id_flujo=r_id_flujo, id_lote=r_id_lote.strip() if r_id_lote.strip() else None,
            prediccion=r_prediccion.strip() if r_prediccion.strip() else None,
            fecha_desde=r_desde.strip() if r_desde.strip() else None, fecha_hasta=r_hasta.strip() if r_hasta.strip() else None,
            revisado=revisado_val, offset=offset, db_path=DB_PATH,
        )

        st.caption(f"Página {pagina} — {len(df_res)} resultado(s) mostrado(s)")

        if df_res.empty:
            st.caption("No hay resultados que mostrar.")
        else:
            df_vista = df_res.copy()

            df_vista["revisado"] = df_vista["revisado"].apply(lambda v: "Sí" if int(v) == 1 else "No")

            evento_res = st.dataframe(
                df_vista[["id_resultado", "id_flujo", "id_lote", "fecha_analisis", "prediccion", "revisado"]],
                use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_resultados",

                column_config={
                    "id_resultado": st.column_config.NumberColumn("ID resultado"),
                    "id_flujo": st.column_config.NumberColumn("ID flujo"),
                    "id_lote": st.column_config.TextColumn("ID lote"),
                    "fecha_analisis": st.column_config.TextColumn("Fecha análisis"),
                    "prediccion": st.column_config.TextColumn("Predicción"),
                    "revisado": st.column_config.TextColumn("Revisado"),
                }
            )

            st.caption(f"{len(df_res)} resultado(s) mostrado(s) — máximo 30 más recientes")

            filas_res_sel = evento_res.selection.rows

            if filas_res_sel:
                fila = filas_res_sel[0]
                id_res_sel = df_res.iloc[fila]["id_resultado"]
                st.markdown("<hr style='margin:0.6rem 0'>", unsafe_allow_html=True)
                mostrar_detalle_resultado(id_res_sel)

            st.markdown("<hr>", unsafe_allow_html=True)

            st.markdown(
                '<p style="font-family:IBM Plex Mono,monospace;font-size:0.68rem; letter-spacing:0.12em;color:#5a6478;text-transform:uppercase;'
                'margin-bottom:0.5rem">Distribución de clases por predicción de los flujos analizados</p>', unsafe_allow_html=True
            )

            df_pred = consultas.conteo_por_prediccion(db_path=DB_PATH)

            if not df_pred.empty:
                total_global = int(df_pred["total"].sum())

                html_pred = """
                <div style="display:grid; grid-template-columns:repeat(8, 1fr); gap:0.3rem;">
                """

                for _, row in df_pred.iterrows():
                    pred = str(row["prediccion"])
                    total = int(row["total"])

                    color = "#00f925" if pred.upper() == "BENIGN" else "#d94f4f"
                    pct = (total / total_global) * 100

                    html_pred += (
                        '<div style="background:#161921;border:1px solid #2a2d35;border-radius:4px;'
                        'padding:0.55rem 0.75rem;min-width:0;">'
                        f'<div style="color:{color};font-size:0.72rem;font-weight:600;margin-bottom:0.22rem;'
                        f'word-break:break-word;">{pred}</div>'
                        f'<div style="color:#c8cdd8;font-size:0.78rem;">{total} resultado(s)</div>'
                        f'<div style="color:#5a6478;font-size:0.65rem;margin-top:0.15rem;">{pct:.1f}% del total</div>'
                        '</div>'
                    )

                html_pred += "</div>"

                st.markdown(html_pred, unsafe_allow_html=True)
                st.caption(f"{total_global} resultado(s) acumulado(s)")

            else:
                st.caption("No hay resultados registrados.")