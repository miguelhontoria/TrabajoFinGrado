"""
Módulo de carga de artefactos generados durante el entrenamiento del modelo. 
Solo se cargan una vez (al iniciar la aplicación) y se reutilizan en memoria.
"""

import os
import joblib


RUTA_BASE = os.path.join(os.path.dirname(__file__), "..", "..", "info_modelo")
RUTA_BASE = os.path.abspath(RUTA_BASE)


cache = {} 
def cargar(nombre_archivo):
    """Carga un archivo pkl desde la carpeta info_modelo."""
    if nombre_archivo in cache:
        return cache[nombre_archivo]
    ruta = os.path.join(RUTA_BASE, nombre_archivo)

    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Artefacto no encontrado: {ruta}\n")
    
    obj = joblib.load(ruta)
    cache[nombre_archivo] = obj
    return obj


def ver_artefactos():
    """
    Función para imprimir por pantalla cualquiera de los artefactos, basta con cambiar el nombre del archivo.
    """
    data = cargar("umbrales_confianza.pkl")
    print(data)

if __name__ == "__main__":
    ver_artefactos()


def cargar_modelo():
    """
    Carga el modelo RandomForest entrenado. Usado por: ids.py
    """
    return cargar("modelo_random_forest.pkl")
 
def cargar_nombres_caracteristicas():
    """
    Carga la lista de 24 nombres de features en el orden exacto que espera el modelo. 
    Usado por: ids.py (para validar y reordenar columnas antes de predecir).
    """
    return cargar("nombres_caracteristicas.pkl")
 
def cargar_clases():
    """
    Carga la lista de nombres de clases en el orden interno del modelo. Posición i corresponde a la columna i de predict_proba().
    """
    return cargar("clases.pkl")
 
def cargar_umbrales_confianza():
    """
    Carga el diccionario {clase: umbral_minimo_confianza}. Usado por: ids.py (para calcular el flag baja_confianza).
    """
    return cargar("umbrales_confianza.pkl")
 
def cargar_distribucion_clases():
    """
    Carga el diccionario con la distribución de clases del dataset completo. Se usa en /interfaz/hisotrico.py para el gráfico circular.
    """
    return cargar("distribucion_clases.pkl")
 
def cargar_importancia_caracteristicas():
    """
    Carga el diccionario con la importancia de las 24 características durante el entrenamiento. 
    Se usa en /interfaz/ticketing.py para el gráfico de barras.
    """
    return cargar("importancia_caracteristicas.pkl")
 
def cargar_info_modelo():
    """
    Carga el diccionario con metadatos y métricas del entrenamiento: 
    parámetros del modelo, fecha, tiempo, exactitud, F1, número de clases, etc. Se usa en app.py en la pantalla principal.
    """
    return cargar("info_modelo.pkl")
 
def cargar_matriz_confusion():
    """
    Carga la matriz de confusión del conjunto test como array numpy.
    """
    return cargar("matriz_confusion.pkl")
 
def cargar_reporte_completo():
    """
    Carga el classification report completo como diccionario. Incluye precisión, recall y F1 por clase, macro avg y weighted avg.
    """
    return cargar("reporte_completo.pkl")
 
 
def cargar_artefactos_ids():
    """
    Carga y devuelve todos los artefactos necesarios para ids.py:
        - modelo
        - nombres_caracteristicas
        - umbrales_confianza
    Devuelve una tupla en ese orden para facilitar el desempaquetado: modelo, nombres, umbrales = cargar_artefactos_ids()
    """
    return (
        cargar_modelo(),
        cargar_nombres_caracteristicas(),
        cargar_umbrales_confianza(),
    )