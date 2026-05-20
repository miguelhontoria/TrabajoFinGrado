"""
Módulo Security Analytics — IDS basado en aprendizaje automático.

Recibe el DataFrame limpio generado por tablas.parsear_flujos() y devuelve un DataFrame con la predicción, la confianza y el flag de baja 
confianza para cada flujo, listo para ser enriquecido por siem.py.
"""

import pandas as pd
from utilidades import cargar_artefactos


modelo, nombres_caracteristicas, umbrales_confianza = (cargar_artefactos.cargar_artefactos_ids())


def analizar_flujos(df_limpio, id_lote, ids_flujo):
    """
    Analiza un DataFrame de flujos limpios y devuelve las predicciones.

    Parámetros:
        df_limpio -> DataFrame con las 24 columnas en el orden correcto, ya normalizado por tablas.parsear_flujos()
        id_lote -> identificador del lote al que pertenecen los flujos
        ids_flujo -> lista de id_flujo asignados por la BD tras insertar en flujos

    Proceso:
        1.Valida si el lote está vacío, que las columnas coincidan con las esperadas por el modelo, control de dimensiones y reordena en el 
        orden exacto que espera el modelo. Los ValueError no se lanzan nunca, pero sirven para aportar robustez a la aplicación y que no dé 
        error por determinados casos.
        2.Predice la clase de cada flujo con modelo.predict()
        3.Obtiene la probabilidad de cada clase con modelo.predict_proba()
        4.Extrae la confianza como la probabilidad máxima de cada fila
        5.Compara la confianza con el umbral de la clase predicha para determinar el flag baja_confianza

    Devuelve:
        DataFrame con columnas:
            id_flujo -> id asignado por la BD
            id_lote -> identificador del lote
            prediccion -> nombre de la clase predicha
            confianza -> probabilidad máxima asignada por el modelo (0-100 con dos decimales)
            baja_confianza -> 1 si confianza < umbral de la clase, 0 si no
    """

    if df_limpio is None or len(df_limpio) == 0:
        raise ValueError("El lote está vacío: no hay flujos para analizar")

    faltantes = [col for col in nombres_caracteristicas if col not in df_limpio.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas obligatorias: {faltantes}")

    if len(ids_flujo) != len(df_limpio):
        raise ValueError("ids_flujo no coincide con número de filas")

    X = df_limpio[nombres_caracteristicas].astype(float)

    predicciones = modelo.predict(X)        

    MAPEO_CLASES = {
        "Web Attack � Brute Force": "Web Attack Brute Force",
        "Web Attack � Sql Injection": "Web Attack Sql Injection",
        "Web Attack � XSS": "Web Attack XSS",
    }

    predicciones = [
        MAPEO_CLASES.get(p, p)  
        for p in predicciones
    ]

    probabilidades = modelo.predict_proba(X)  

    confianzas = probabilidades.max(axis=1)    

    baja_confianza = []
    for pred, conf in zip(predicciones, confianzas):
        umbral = umbrales_confianza.get(pred, 0.50) 
        baja_confianza.append(1 if conf < umbral else 0)

    df_predicciones = pd.DataFrame({
        "id_flujo": ids_flujo,
        "id_lote": id_lote,
        "prediccion": predicciones,
        "confianza": confianzas.round(4),
        "baja_confianza": baja_confianza,
    })

    return df_predicciones