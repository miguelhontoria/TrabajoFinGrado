"""
Estilos CSS globales del simulador SOC. Se importa desde app.py mediante inyectar_estilos().
"""

import streamlit as st

def inyectar_estilos():
    st.markdown("""
    <style>
        /* Fuentes */
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'IBM Plex Sans', sans-serif;
        }

        /* Fondo general */
        .stApp {
            background-color: #0b1020;
            color: #c8cdd8;
        }
                    
        /* Cabecera principal */
        .soc-header {
            border-bottom: 1px solid #2a2d35;
            padding: 2rem 0 1.5rem 0;
            margin-bottom: 2.5rem;
        }

        .soc-title {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.1rem;
            font-weight: 600;
            letter-spacing: 0.15em;
            color: #8b9ab0;
            text-transform: uppercase;
            margin: 0;
        }

        .soc-subtitle {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 2rem;
            font-weight: 600;
            color: #e8ecf2;
            margin: 0.2rem 0 0 0;
            letter-spacing: -0.02em;
        }

        .soc-status {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.75rem;
            color: #4a9e6b;
            letter-spacing: 0.1em;
            margin-top: 0.4rem;
        }
                
        /* Ocultar barra superior de Streamlit */
        header[data-testid="stHeader"] {
            background-color: transparent;
        }

        /* Tarjetas de navegación */
        .nav-card {
            background-color: #161921;
            border: 1px solid #2a2d35;
            border-radius: 4px;
            padding: 1.8rem 1.5rem;
            height: 100%;
            transition: border-color 0.2s ease;
            cursor: pointer;
        }

        .nav-card:hover {
            border-color: #4a6fa5;
        }

        .nav-card-label {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.7rem;
            letter-spacing: 0.15em;
            color: #5a6478;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        .nav-card-title {
            font-size: 1.15rem;
            font-weight: 500;
            color: #c8cdd8;
            margin-bottom: 0.4rem;
        }

        .nav-card-desc {
            font-size: 0.82rem;
            color: #5a6478;
            line-height: 1.5;
        }

        /* Panel central de análisis */
        .upload-panel {
            background-color: #161921;
            border: 1px solid #2a2d35;
            border-radius: 4px;
            padding: 2.5rem 2rem;
        }

        .upload-label {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.7rem;
            letter-spacing: 0.15em;
            color: #5a6478;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        .upload-title {
            font-size: 1.3rem;
            font-weight: 500;
            color: #e8ecf2;
            margin-bottom: 0.3rem;
        }

        .upload-note {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.75rem;
            color: #4a5568;
            margin-bottom: 1.8rem;
            padding: 0.5rem 0.8rem;
            background: #0f1117;
            border-left: 2px solid #2a2d35;
            border-radius: 2px;
        }

        /* Tabla de resultados */
        .results-header {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.7rem;
            letter-spacing: 0.15em;
            color: #5a6478;
            text-transform: uppercase;
            margin: 2rem 0 0.8rem 0;
            padding-top: 1.5rem;
            border-top: 1px solid #2a2d35;
        }

        /* Botones Streamlit */
        .stButton > button {
            background-color: #161921 !important;
            color: #c8cdd8 !important;
            border: 1px solid #2a2d35 !important;
            border-radius: 3px !important;
            font-family: 'IBM Plex Sans', sans-serif !important;
            font-size: 0.85rem !important;
            padding: 0.5rem 1.2rem !important;
            width: 100% !important;
            transition: all 0.15s ease !important;
        }

        .stButton > button:hover {
            border-color: #4a6fa5 !important;
            color: #e8ecf2 !important;
            background-color: #1c2030 !important;
        }

        /* Mensajes de estado */
        .stAlert {
            border-radius: 3px !important;
            font-family: 'IBM Plex Mono', monospace !important;
            font-size: 0.8rem !important;
        }
                
        [data-testid="stFileUploader"] {
            background: #0f1117 !important;
            border: 1px dashed #2a2d35 !important;
            border-radius: 3px !important;
        }

        /* Upload -> Subir */
        [data-testid="stFileUploader"] button p {
            visibility: hidden;
            position: relative;
        }

        [data-testid="stFileUploader"] button p::after {
            content: "Subir";
            visibility: visible;
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.9rem;
            color: #c8cdd8;
        }
    </style>
    """, unsafe_allow_html=True)