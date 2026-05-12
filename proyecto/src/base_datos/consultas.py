"""
Módulo de consultas a la base de datos SQLite del sistema SOC.
 
Organización:
    - Consultas pantalla principal (resultados de un lote recién analizado)
    - Consultas pantalla Histórico (tabla flujos + tabla resultados resumida)
    - Consultas pantalla Ticketing (ataques pendientes de revisión)
    - Consultas de métricas generales (conteos, distribuciones)
    - Operaciones de actualización (marcar como revisado, añadir notas)
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
    Devuelve los resultados de un lote recién analizado.
    Solo muestra: id_resultado, id_flujo, id_lote, fecha_analisis,
                  prediccion, confianza.
    Se usa para la tabla inmediata tras subir el archivo.
    Incluye todos los flujos del lote, también los BENIGN.
    """
    query = """
        SELECT
            id_resultado,
            id_flujo,
            id_lote,
            fecha_analisis,
            prediccion,
            confianza
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
    limite=500,
    db_path="soc.db"
):
    """
    Pantalla histórico - flujos. Devuelve flujos con solo id_flujo, id_lote y fecha_ingesta. 
    Al pinchar sobre id_flujo en la interfaz se llama a obtener_detalle_flujo()
    para mostrar las 24 características completas.
 
    Filtros opcionales: id_flujo, id_lote, fecha_desde, fecha_hasta.
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
        ORDER BY fecha_ingesta DESC
        LIMIT ?
    """
    params.append(limite)
 
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)
 
 
def obtener_detalle_flujo(id_flujo, db_path="soc.db"):
    """
    Devuelve todas las columnas de un flujo concreto (metadatos + 24 features).
    Se usa al pinchar sobre id_flujo en la tabla del Histórico.
    Devuelve un diccionario o None si no existe.
    """
    query = """
        SELECT *
        FROM flujos
        WHERE id_flujo = ?
    """
    with conectar(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=(id_flujo,))
    return df.iloc[0].to_dict() if not df.empty else None
 
 
def ultimos_n_flujos(n=10, db_path="soc.db"):
    """
    Devuelve los N flujos más recientes (id_flujo, id_lote, fecha_ingesta).
    Útil para mostrar actividad reciente en Histórico.
    """
    query = """
        SELECT id_flujo, id_lote, fecha_ingesta
        FROM flujos
        ORDER BY fecha_ingesta DESC
        LIMIT ?
    """
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(n,))
    

 
def obtener_resultados_historico(
    id_resultado=None,
    id_flujo=None,
    id_lote=None,
    fecha_desde=None,
    fecha_hasta=None,
    prediccion=None,
    revisado=None,
    limite=500,
    db_path="soc.db"
):
    """
    Pantalla histórico - resultados. Devuelve resultados en vista resumida para Histórico.
    Incluye ataques y BENIGN, revisados y pendientes.
    notas_analista solo aparece con valor cuando revisado=1 y el analista introdujo algo; en caso contrario es NULL.
 
    Filtros opcionales: id_resultado, id_flujo, id_lote, fecha_analisis,
                        prediccion, revisado.
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
            confianza,
            revisado,
            CASE WHEN revisado = 1 THEN notas_analista ELSE NULL END AS notas_analista
        FROM resultados
        {where}
        ORDER BY fecha_analisis DESC
        LIMIT ?
    """
    params.append(limite)
 
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)
 
 
def ultimos_n_resultados(n=10, db_path="soc.db"):
    """
    Devuelve los N resultados más recientes en vista resumida.
    Incluye ataques y BENIGN. Útil para mostrar actividad reciente en Histórico.
    """
    query = """
        SELECT
            id_resultado,
            id_flujo,
            id_lote,
            fecha_analisis,
            prediccion,
            confianza,
            revisado,
            CASE WHEN revisado = 1 THEN notas_analista ELSE NULL END AS notas_analista
        FROM resultados
        ORDER BY fecha_analisis DESC
        LIMIT ?
    """
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(n,))
 
 
def obtener_detalle_resultado(id_resultado, db_path="soc.db"):
    """
    Devuelve detalle de resultado.
    - Si revisado = 0 → solo columnas básicas
    - Si revisado = 1 → todas las columnas
    """
    query = """
        SELECT
            id_resultado,
            id_flujo,
            id_lote,
            fecha_analisis,
            prediccion,
            confianza,
            CASE WHEN revisado = 1 THEN baja_confianza ELSE NULL END AS baja_confianza,
            CASE WHEN revisado = 1 THEN severidad ELSE NULL END AS severidad,
            CASE WHEN revisado = 1 THEN recomendacion ELSE NULL END AS recomendacion,
            revisado,
            CASE WHEN revisado = 1 THEN notas_analista ELSE NULL END AS notas_analista
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
    baja_confianza=None,
    severidad=None,
    limite=500,
    db_path="soc.db"
):
    """
    Pantalla ticketing - resultados. Devuelve resultados pendientes de revisión que son ataques (no BENIGN).
    Condiciones base siempre aplicadas: prediccion != 'BENIGN', revisado = 0.
    Muestra las 11 columnas completas.
 
    Filtros opcionales: id_resultado, id_flujo, id_lote, fecha_analisis,
                        prediccion, baja_confianza, severidad.
    """
    condiciones = ["prediccion != 'BENIGN'", "revisado = 0"]
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
    if baja_confianza is not None:
        condiciones.append("baja_confianza = ?")
        params.append(baja_confianza)
    if severidad is not None:
        condiciones.append("severidad = ?")
        params.append(severidad)
 
    where = f"WHERE {' AND '.join(condiciones)}"
 
    query = f"""
        SELECT *
        FROM resultados
        {where}
        ORDER BY fecha_analisis DESC
        LIMIT ?
    """
    params.append(limite)
 
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)
 
 
def ultimos_n_pendientes(n=10, db_path="soc.db"):
    """
    Devuelve los N ataques pendientes más recientes.
    Útil para mostrar actividad reciente en Ticketing.
    """
    query = """
        SELECT *
        FROM resultados
        WHERE prediccion != 'BENIGN'
        AND revisado = 0
        ORDER BY fecha_analisis DESC
        LIMIT ?
    """
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(n,))
 

 
def obtener_flujos_ataques(
    id_flujo=None,
    id_lote=None,
    fecha_desde=None,
    fecha_hasta=None,
    limite=500,
    db_path="soc.db"
):
    """
    Pantalla ticketing - flujos. Devuelve los flujos originales (id_flujo, id_lote, fecha_ingesta)
    que corresponden a ataques detectados, ya estén revisados o no.
    Hace un JOIN con resultados para filtrar solo los flujos con
    prediccion != 'BENIGN'.
 
    Filtros opcionales: id_flujo, id_lote, fecha_desde, fecha_hasta.
    """
    condiciones = ["r.prediccion != 'BENIGN'"]
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
        ORDER BY f.fecha_ingesta DESC
        LIMIT ?
    """
    params.append(limite)
 
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)
 
 
def ultimos_n_flujos_ataques(n=10, db_path="soc.db"):
    """
    Devuelve los N flujos más recientes asociados a ataques.
    Útil para mostrar actividad reciente en Ticketing.
    """
    query = """
        SELECT DISTINCT f.id_flujo, f.id_lote, f.fecha_ingesta
        FROM flujos f
        INNER JOIN resultados r ON f.id_flujo = r.id_flujo
        WHERE r.prediccion != 'BENIGN'
        ORDER BY f.fecha_ingesta DESC
        LIMIT ?
    """
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(n,))
    


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
    Solo cuenta ataques (excluye BENIGN).
    Ordenado por criticidad: Critical → High → Medium → Low.
    """
    query = """
        SELECT severidad, COUNT(*) as total
        FROM resultados
        WHERE prediccion != 'BENIGN'
        GROUP BY severidad
        ORDER BY CASE severidad 
            WHEN 'Critical' THEN 1
            WHEN 'High'     THEN 2
            WHEN 'Medium'   THEN 3
            WHEN 'Low'      THEN 4
            ELSE 5
        END
    """
    with conectar(db_path) as conn:
        return pd.read_sql_query(query, conn)
 
 
def total_pendientes(db_path="soc.db"):
    """
    Devuelve el número total de ataques pendientes de revisión.
    Útil para mostrar un contador en la cabecera: '12 alertas pendientes'.
    """
    query = """
        SELECT COUNT(*) as total
        FROM resultados
        WHERE prediccion != 'BENIGN'
        AND revisado = 0
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
    Se llama desde Ticketing cuando el analista confirma la revisión.
    Una vez marcado, el flujo desaparece de Ticketing y pasa a Histórico.
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