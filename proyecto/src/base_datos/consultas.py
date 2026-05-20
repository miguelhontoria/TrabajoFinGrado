"""
Módulo de consultas a la base de datos SQLite del simulador SOC.
 
Organización:
    - Consultas pantalla principal (resultados de un lote recién analizado)
    - Consultas pantalla Histórico (tabla flujos + tabla resultados resumida)
    - Consultas pantalla Ticketing (ataques, y posibles ataques, pendientes de revisión)
    - Consultas de métricas generales (conteos, distribuciones)
    - Operación de actualización (marcar como revisado y añadir notas)
"""
 
import sqlite3
import pandas as pd


def conectar(db_path):
    """Abre conexión con claves foráneas activadas."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def obtener_resultados_lote(id_lote, db_path="soc.db"):
    """
    Devuelve los resultados (simplificados, para un primer vistazo por parte del analista) de un lote recién analizado.
    Solo muestra: id_resultado, id_flujo, id_lote, fecha_analisis, prediccion, confianza y baja_confianza. Y un resumen por severidad.
    Se usa para la tabla inmediata tras subir el archivo. Incluye todos los flujos del lote, también los BENIGN.
    """
    query = """
        SELECT
            id_resultado,
            id_flujo,
            id_lote,
            fecha_analisis,
            prediccion,
            confianza,
            baja_confianza,
            severidad
        FROM resultados
        WHERE id_lote = ?
        ORDER BY id_flujo
    """
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(id_lote,))



def obtener_flujos(
    id_flujo=None,
    id_lote=None,
    fecha_desde=None,
    fecha_hasta=None,
    limite=30,
    offset=0,
    db_path="soc.db"
):
    """
    Pantalla histórico - flujos. Devuelve flujos con solo id_flujo, id_lote y fecha_ingesta. Al pinchar sobre id_flujo en la interfaz se 
    llama a obtener_detalle_flujo() para mostrar las 24 características completas.
 
    Filtros opcionales: id_flujo, id_lote, fecha_desde, fecha_hasta (fecha_analisis).
    """
    condiciones = []
    params = []
 
    if id_flujo is not None:
        condiciones.append("id_flujo = ?")
        params.append(id_flujo)
    if id_lote is not None:
        condiciones.append("id_lote = ?")
        params.append(id_lote)
    if fecha_desde is not None:
        condiciones.append("fecha_ingesta >= ?")
        params.append(fecha_desde)
    if fecha_hasta is not None:
        condiciones.append("fecha_ingesta <= ?")
        params.append(fecha_hasta)
 
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
 
    query = f"""
        SELECT id_flujo, id_lote, fecha_ingesta
        FROM flujos
        {where}
        ORDER BY id_flujo DESC
        LIMIT ?
        OFFSET ? 
    """
    params.append(limite)
    params.append(offset)
 
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)
 
 
def obtener_detalle_flujo(id_flujo, db_path="soc.db"):
    """
    Devuelve todas las columnas de un flujo concreto (metadatos + 24 features). Devuelve un diccionario o None si no existe.
    """
    query = """
        SELECT *
        FROM flujos
        WHERE id_flujo = ?
    """
    with conectar(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=(id_flujo,))
    return df.iloc[0].to_dict() if not df.empty else None
 
 
def obtener_resultados_historico(
    id_resultado=None,
    id_flujo=None,
    id_lote=None,
    fecha_desde=None,
    fecha_hasta=None,
    prediccion=None,
    revisado=None,
    limite=30,
    offset=0,
    db_path="soc.db"
):
    """
    Pantalla histórico - resultados. Devuelve resultados en vista resumida para Histórico. Incluye ataques y BENIGN, revisados y pendientes.
 
    Filtros opcionales: id_resultado, id_flujo, id_lote, fecha_analisis, prediccion y revisado.
    """
    condiciones = []
    params = []
 
    if id_resultado is not None:
        condiciones.append("id_resultado = ?")
        params.append(id_resultado)
    if id_flujo is not None:
        condiciones.append("id_flujo = ?")
        params.append(id_flujo)
    if id_lote is not None:
        condiciones.append("id_lote = ?")
        params.append(id_lote)
    if fecha_desde is not None:
        condiciones.append("fecha_analisis >= ?")
        params.append(fecha_desde)
    if fecha_hasta is not None:
        condiciones.append("fecha_analisis <= ?")
        params.append(fecha_hasta)
    if prediccion is not None:
        condiciones.append("prediccion = ?")
        params.append(prediccion)
    if revisado is not None:
        condiciones.append("revisado = ?")
        params.append(revisado)
 
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
 
    query = f"""
        SELECT
            id_resultado,
            id_flujo,
            id_lote,
            fecha_analisis,
            prediccion,
            revisado
        FROM resultados
        {where}
        ORDER BY id_resultado DESC
        LIMIT ?
        OFFSET ?
    """
    params.append(limite)
    params.append(offset)
 
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)
 
 
def obtener_detalle_resultado(id_resultado, db_path="soc.db"):
    """
    Devuelve todas las columnas de un resultado concreto (las 11). Devuelve un diccionario o None si no existe.
    """
    query = """
        SELECT *
        FROM resultados
        WHERE id_resultado = ?
    """
    with conectar(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=(id_resultado,))
    return df.iloc[0].to_dict() if not df.empty else None


 
def obtener_pendientes_ticketing(
    id_resultado=None,
    id_flujo=None,
    id_lote=None,
    fecha_desde=None,
    fecha_hasta=None,
    prediccion=None,
    confianza=None,
    severidad=None,
    limite=30,
    offset=0,
    db_path="soc.db"
):
    """
    Pantalla ticketing - resultados. Devuelve resultados pendientes de revisión que son ataques o posibles ataques (BENIGN severidad BAJA). 
    Condición base siempre aplicada: revisado = 0. 
 
    Filtros opcionales: id_resultado, id_flujo, id_lote, fecha_analisis, prediccion, confianza y severidad.
    """
    condiciones = ["(prediccion != 'BENIGN' OR (prediccion = 'BENIGN' AND severidad = 'BAJA'))", "revisado = 0"]
    params = []
 
    if id_resultado is not None:
        condiciones.append("id_resultado = ?")
        params.append(id_resultado)
    if id_flujo is not None:
        condiciones.append("id_flujo = ?")
        params.append(id_flujo)
    if id_lote is not None:
        condiciones.append("id_lote = ?")
        params.append(id_lote)
    if fecha_desde is not None:
        condiciones.append("fecha_analisis >= ?")
        params.append(fecha_desde)
    if fecha_hasta is not None:
        condiciones.append("fecha_analisis <= ?")
        params.append(fecha_hasta)
    if prediccion is not None:
        condiciones.append("prediccion = ?")
        params.append(prediccion)
    if confianza is not None:
        conf = float(str(confianza).replace("%", "").strip())
        if conf > 1:
                conf = conf / 100
        condiciones.append("confianza BETWEEN ? AND ?")
        params.append(conf - 0.005)
        params.append(conf + 0.005)
    if severidad is not None:
        condiciones.append("severidad = ?")
        params.append(severidad)
 
    where = f"WHERE {' AND '.join(condiciones)}"
 
    query = f"""
        SELECT 
            id_resultado,
            id_flujo,
            id_lote,
            fecha_analisis,
            prediccion,
            confianza,
            severidad
        FROM resultados
        {where}
        ORDER BY id_flujo DESC
        LIMIT ?
        OFFSET ?
    """
    params.append(limite)
    params.append(offset)
 
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)
 
 
def obtener_flujos_ataques(
    id_flujo=None,
    id_lote=None,
    fecha_desde=None,
    fecha_hasta=None,
    limite=30,
    offset=0,
    db_path="soc.db"
):
    """
    Pantalla ticketing - flujos. Devuelve los flujos originales (id_flujo, id_lote, fecha_ingesta) que corresponden a ataques detectados, 
    que no estén revisados. O flujos BENIGN de severidad BAJA.
 
    Filtros opcionales: id_flujo, id_lote, fecha_desde, fecha_hasta.
    """
    condiciones = ["(r.prediccion != 'BENIGN' OR (r.prediccion = 'BENIGN' AND r.severidad = 'BAJA'))", "r.revisado = 0"]
    params = []
 
    if id_flujo is not None:
        condiciones.append("f.id_flujo = ?")
        params.append(id_flujo)
    if id_lote is not None:
        condiciones.append("f.id_lote = ?")
        params.append(id_lote)
    if fecha_desde is not None:
        condiciones.append("f.fecha_ingesta >= ?")
        params.append(fecha_desde)
    if fecha_hasta is not None:
        condiciones.append("f.fecha_ingesta <= ?")
        params.append(fecha_hasta)
 
    where = f"WHERE {' AND '.join(condiciones)}"
 
    query = f"""
        SELECT DISTINCT f.id_flujo, f.id_lote, f.fecha_ingesta
        FROM flujos f
        INNER JOIN resultados r ON f.id_flujo = r.id_flujo
        {where}
        ORDER BY f.id_flujo DESC
        LIMIT ?
        OFFSET ?
    """
    params.append(limite)
    params.append(offset)
 
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)
    


def conteo_por_prediccion(db_path="soc.db"):
    """
    Devuelve el número de resultados agrupados por tipo de predicción.
    Incluye BENIGN. Útil para gráfico de distribución de tráfico analizado.
    """
    query = """
        SELECT prediccion, COUNT(*) as total
        FROM resultados
        GROUP BY prediccion
        ORDER BY total DESC
    """
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn)
 

def conteo_por_severidad(db_path="soc.db"):
    """
    Devuelve el número de resultados agrupados por severidad.
    Ordenado por criticidad: CRITICA → ALTA → MEDIA → BAJA -> INFO
    """
    query = """
        SELECT severidad, COUNT(*) as total
        FROM resultados
        WHERE (prediccion != 'BENIGN' OR (prediccion = 'BENIGN' AND severidad = 'BAJA')) AND revisado = 0
        GROUP BY severidad
        ORDER BY CASE severidad
                WHEN 'CRITICA' THEN 5
                WHEN 'ALTA' THEN 4
                WHEN 'MEDIA' THEN 3
                WHEN 'BAJA' THEN 2
                WHEN 'INFO' THEN 1
                ELSE 0
            END DESC
    """
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn)
 
 
def total_pendientes(db_path="soc.db"):
    """
    Devuelve el número total de alertas pendientes de revisión.
    Cuenta:
      - Ataques (prediccion != 'BENIGN')
      - BENIGN sospechosos (baja_confianza = 1 <--> severidad = BAJA)
    Siempre que revisado = 0.
    """
    query = """
        SELECT COUNT(*) AS total
        FROM resultados
        WHERE revisado = 0
          AND (
                prediccion != 'BENIGN'
                OR (prediccion = 'BENIGN' AND severidad = 'BAJA')
              )
    """
    with conectar(db_path) as conn:
        resultado = conn.execute(query).fetchone()

    return resultado[0] if resultado else 0
 
 
def conteo_flujos_por_lote(db_path="soc.db"):
    """
    Devuelve el número de flujos analizados agrupados por lote, con la fecha de ingesta del primero de cada lote.
    Útil para mostrar un resumen de cargas en el histórico.
    """
    query = """
        SELECT
            id_lote,
            COUNT(*) as total_flujos,
            MIN(fecha_ingesta) as fecha
        FROM flujos
        GROUP BY id_lote
        ORDER BY fecha DESC
    """
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn)
    

 
def marcar_revisado(id_resultado, notas=None, db_path="soc.db"):
    """
    Marca un resultado como revisado (revisado = 1) y guarda opcionalmente las notas del analista.
    Se llama desde Ticketing cuando el analista confirma la revisión. Una vez marcado, flujo desaparece de Ticketing y se actualiza en Histórico.
    """
    with conectar(db_path) as conn:
        conn.execute(
            """
            UPDATE resultados
            SET revisado = 1, notas_analista = ?
            WHERE id_resultado = ?
            """,
            (notas, id_resultado)
        )
        conn.commit()