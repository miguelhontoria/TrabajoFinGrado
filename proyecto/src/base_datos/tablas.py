"""
Módulo de gestión de la base de datos del simulador SOC.

Incluye las operaciones necesarias para preparar y alimentar las tablas
principales del sistema: flujos (datos originales normalizados) y resultados
(predicciones generadas por el IDS y enriquecidas por el SIEM).

Funciones principales:
    - parsear_flujos(): valida y normaliza los flujos de red antes del análisis.
    - crear_tablas(): crea la estructura de la base de datos (flujos y resultados).
    - insertar_flujos(): inserta los flujos procesados y devuelve sus id_flujo.
    - insertar_resultados(): almacena las predicciones y metadatos del análisis.
    - generar_id_lote(): genera identificadores únicos para cada lote procesado.

Este módulo actúa como capa de persistencia del sistema, garantizando que los
datos se almacenan de forma consistente y que pueden ser consultados por los
módulos de análisis, histórico y ticketing.
"""

import sqlite3
import time
import numpy as np


COLUMNAS_MODELO = [
    "Total Fwd Packet",
    "Total Bwd packets",
    "Flow Bytes/s",
    "Bwd Packets/s",
    "FWD Init Win Bytes",
    "Bwd Init Win Bytes",
    "Flow Duration",
    "Flow IAT Min",
    "Fwd IAT Min",
    "Fwd IAT Total",
    "Bwd IAT Min",
    "Bwd IAT Std",
    "Bwd IAT Total",
    "Total Length of Fwd Packet",
    "Total Length of Bwd Packet",
    "Fwd Packet Length Min",
    "Fwd Packet Length Std",
    "Bwd Packet Length Min",
    "Bwd Packet Length Std",
    "Packet Length Max",
    "Fwd Seg Size Min",
    "PSH Flag Count",
    "Down/Up Ratio",
    "Fwd Header Length",
]

COLUMNAS_SQL = [
    col.strip().replace(" ", "_").replace("/", "_")
    for col in COLUMNAS_MODELO
]

def parsear_flujos(df_entrada):
    """
    Parsea y normaliza un DataFrame de flujos de red.
 
    Pasos:
        1. Elimina espacios en nombres de columnas
        2. Comprueba que existen las 24 columnas obligatorias
        3. Selecciona y reordena solo esas 24 columnas
        4. Elimina filas con NaN o valores infinitos
        5. Aplica recorte de valores atípicos (percentiles 0.1% y 99.9%)
           igual que en la fase de limpieza del entrenamiento
 
    Returns:
        df_limpio   → DataFrame listo para el modelo
        filas_descartadas → lista de índices eliminados con motivo
 
    Raises:
        ValueError si faltan columnas obligatorias
    """
 
    df = df_entrada.copy()
 
    df.columns = df.columns.str.strip()
 
    faltantes = [col for col in COLUMNAS_MODELO if col not in df.columns]
    if faltantes:
        raise ValueError(
            f"El archivo no contiene todas las características requeridas. Faltan las siguientes columnas: {faltantes}"
        )
 
    df = df[COLUMNAS_MODELO].copy()

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    filas_antes = len(df)
    mask_nan = df.isna().any(axis=1)
    indices_descartados = df[mask_nan].index.tolist()
    df = df[~mask_nan].copy()
    df.reset_index(drop=True, inplace=True)
    filas_despues = len(df)
 
    filas_descartadas = indices_descartados
    mensaje_descartes = None
    if indices_descartados:
        mensaje_descartes = (
            f"Se descartaron {filas_antes - filas_despues} fila(s) por contener valores NaN o infinitos.\n"
            f"Filas descartadas: {indices_descartados}"
        )

    for col in df.columns:
        lim_inf = df[col].quantile(0.001)
        lim_sup = df[col].quantile(0.999)
        df[col] = df[col].clip(lim_inf, lim_sup)
 
    return df, filas_descartadas, mensaje_descartes

def generar_id_lote():
    """
    No se llama dentro de tablas.py. Se llama desde app.py, el resultado se pasa como parámetro. Flujo en app.py sería:
    id_lote = tablas.generar_id_lote() #genera "lote_20250503_142301"       ids_flujo = tablas.insertar_flujos(df_limpio, id_lote)
    tablas.insertar_resultados(df_resultados, id_lote)  # mismo id_lote para enlazar
    """
    return f"lote_{time.strftime('%d%m%Y_%H%M%S')}"


def conectar(db_path):
    """Abre conexión con claves foráneas activadas."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def crear_tablas(db_path="soc.db"):
    """Crea las tablas flujos y resultados si no existen."""
    with conectar(db_path) as conn:
        cursor = conn.cursor()
 
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS flujos (
            id_flujo      INTEGER PRIMARY KEY AUTOINCREMENT,
            id_lote       TEXT    NOT NULL,
            fecha_ingesta TEXT    NOT NULL,
            {", ".join(f"{col} REAL" for col in COLUMNAS_SQL)}
        )
        """)
 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultados (
            id_resultado    INTEGER PRIMARY KEY AUTOINCREMENT,
            id_flujo        INTEGER NOT NULL,
            id_lote         TEXT    NOT NULL,
            fecha_analisis  TEXT    NOT NULL,
            prediccion      TEXT    NOT NULL,
            confianza       REAL    NOT NULL,
            baja_confianza  INTEGER DEFAULT 0, 
            severidad       TEXT    NOT NULL,
            recomendacion   TEXT    NOT NULL,
            revisado        INTEGER DEFAULT 0,
            notas_analista  TEXT,
            FOREIGN KEY (id_flujo) REFERENCES flujos(id_flujo)
        )
        """)

        cursor.execute(""" 
            CREATE INDEX IF NOT EXISTS idx_resultados_lote
            ON resultados (id_lote)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resultados_flujo
            ON resultados (id_flujo)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resultados_ticketing
            ON resultados (revisado, prediccion)          
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resultados_severidad
            ON resultados (severidad)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resultados_fecha
            ON resultados (fecha_analisis)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flujos_lote
            ON flujos (id_lote)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flujos_fecha
            ON flujos (fecha_ingesta)
        """)

        conn.commit()


def insertar_flujos(df_limpio, id_lote, db_path="soc.db"):
    """
    Inserta el DataFrame de flujos ya normalizados en la tabla flujos.
    Devuelve la lista de id_flujo generados para enlazarlos con resultados.
    """
    crear_tablas(db_path)
 
    df_sql = df_limpio.copy()
 
    df_sql.columns = [
        col.strip().replace(" ", "_").replace("/", "_")
        for col in df_sql.columns
    ]
 
    df_sql.insert(0, "id_lote", id_lote)
    df_sql.insert(1, "fecha_ingesta", time.strftime("%Y-%m-%d %H:%M:%S"))
 
    with conectar(db_path) as conn:
        df_sql.to_sql("flujos", conn, if_exists="append", index=False)
 
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_flujo FROM flujos WHERE id_lote = ? ORDER BY id_flujo",
            (id_lote,)
        )
        ids_flujo = [row[0] for row in cursor.fetchall()]
        conn.commit()
 
    return ids_flujo
 

def insertar_resultados(df_resultados, db_path="soc.db"):
    """
    Inserta los resultados completos del análisis en la tabla resultados.
 
    df_resultados debe contener las columnas:
        id_flujo, id_lote, prediccion, confianza, baja_confianza,
        severidad, recomendacion
    """
    crear_tablas(db_path)
 
    df_sql = df_resultados.copy()
    df_sql["fecha_analisis"] = time.strftime("%Y-%m-%d %H:%M:%S")
    df_sql["revisado"]       = 0
    df_sql["notas_analista"] = None
 
    columnas = [
        "id_flujo", "id_lote", "fecha_analisis",
        "prediccion", "confianza", "baja_confianza",
        "severidad", "recomendacion",
        "revisado", "notas_analista",
    ]
 
    df_sql = df_sql[columnas]
 
    with conectar(db_path) as conn:
        df_sql.to_sql("resultados", conn, if_exists="append", index=False)
        conn.commit()