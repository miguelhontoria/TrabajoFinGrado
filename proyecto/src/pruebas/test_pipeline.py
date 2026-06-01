"""
Pruebas del pipeline: tablas.py → ids.py -> siem.py
Cubre: creación de BD, parseo, inserción, predicción y análisis (resultado final).

Ejecutar desde /src/:
    python -m pruebas.test_pipeline
"""

import os
import sqlite3
import numpy as np
import pandas as pd

from base_datos import tablas
from analisis import ids
from correlacion import siem

from utilidades.cargar_artefactos import cargar_nombres_caracteristicas

nombres = cargar_nombres_caracteristicas()
DB_PATH = "prueba.db"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def separador(titulo):
    print(f"\n{'='*60}")
    print(f"{titulo}")
    print('='*60)

def ok(msg): print(f"OK {msg}")
def error(msg): print(f"KO ERROR inesperado: {msg}")
def esperado(msg): print(f"OK Excepción esperada: {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. CREAR BASE DE DATOS Y TABLAS
# ─────────────────────────────────────────────────────────────────────────────
separador("1. CREAR BASE DE DATOS")
tablas.crear_tablas(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cols = conn.execute("PRAGMA table_info(flujos)").fetchall()
conn.close()
ok(f"Tabla flujos creada con {len(cols)} columnas (3 metadatos + 24 features)")


# ─────────────────────────────────────────────────────────────────────────────
# 2. PARSEO DE FLUJOS — tablas.parsear_flujos()
# ─────────────────────────────────────────────────────────────────────────────
separador("2. PARSEO - NaN e infinitos")
df_nan_inf = pd.DataFrame({col: [1.0, np.nan, np.inf] for col in nombres})
df_limpio, descartadas, mensaje_descartes = tablas.parsear_flujos(df_nan_inf)
ok(f"Filas descartadas: {len(descartadas)} | Filas válidas: {len(df_limpio)}")
for d in descartadas:
    print(f"     fila {d}: descartada por NaN/inf")


separador("2. PARSEO - Columnas faltantes -> debe fallar")
nombres_sin_flow = [c for c in nombres if c != "Flow Duration"]
df_incompleto = pd.DataFrame({col: [0.1] for col in nombres_sin_flow})
try:
    tablas.parsear_flujos(df_incompleto)
    error("No lanzó excepción")
except ValueError as e:
    esperado(e)


separador("2. PARSEO - Columnas extra -> se descartan silenciosamente")
df_extra = pd.DataFrame({col: [1.0] for col in nombres})
df_extra["columna_extra"] = 999.0
df_limpio_extra, _, _ = tablas.parsear_flujos(df_extra)
ok(f"Columnas tras parseo: {list(df_limpio_extra.columns)}")


separador("2. PARSEO - Columnas desordenadas -> se reordenan silenciosamente")
df_desordenado = pd.DataFrame({col: [1.0] for col in nombres[::-1]})
df_limpio_orden, _, _ = tablas.parsear_flujos(df_desordenado)
ok(f"Primeras columnas tras parseo: {list(df_limpio_orden.columns[:3])}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. INSERCIÓN EN BD — tablas.insertar_flujos()
# ─────────────────────────────────────────────────────────────────────────────
separador("3. INSERCIÓN - Lote normal (3 flujos)")
df_base = pd.DataFrame({col: [0.1, 5000.0, 0.0001] for col in nombres})
ids_flujo = tablas.insertar_flujos(df_base, "lote_001", db_path=DB_PATH)
ok(f"IDs generados: {ids_flujo}")


separador("3. INSERCIÓN - Lote grande (150 flujos)")
df_big = pd.concat([df_base] * 50, ignore_index=True)
ids_big = tablas.insertar_flujos(df_big, "lote_big", db_path=DB_PATH)
ok(f"Flujos insertados: {len(ids_big)} | IDs: {ids_big[0]}...{ids_big[-1]}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. PREDICCIÓN — ids.analizar_flujos()
# ─────────────────────────────────────────────────────────────────────────────
separador("4. IDS - Lote normal")
df_pred = ids.analizar_flujos(df_base, "lote_001", ids_flujo)
print(df_pred.to_string(index=False))


separador("4. IDS - Lote desordenado -> se reordena y predice")
ids_orden = tablas.insertar_flujos(df_desordenado, "lote_orden", db_path=DB_PATH)
df_pred_orden = ids.analizar_flujos(df_desordenado, "lote_orden", ids_orden)
ok(f"Predicciones: {list(df_pred_orden['prediccion'])}")


separador("4. IDS - Strings como datos -> se convierten a float y predice")
df_str = df_base.astype(str)
ids_str = tablas.insertar_flujos(df_str, "lote_str", db_path=DB_PATH)
df_pred_str = ids.analizar_flujos(df_str, "lote_str", ids_str)
ok(f"Predicciones: {list(df_pred_str['prediccion'])}")


separador("4. IDS - ids_flujo con longitud incorrecta -> debe fallar")
try:
    ids.analizar_flujos(df_base, "lote_001", [1, 2])
    error("No lanzó excepción")
except ValueError as e:
    esperado(e)


separador("4. IDS - Columnas faltantes -> debe fallar")
df_sin_col = df_base.drop(columns=["Flow Duration"])
try:
    ids.analizar_flujos(df_sin_col, "lote_001", ids_flujo)
    error("No lanzó excepción")
except ValueError as e:
    esperado(e)


separador("4. IDS - Lote vacío -> debe fallar")
df_vacio = pd.DataFrame(columns=nombres)
try:
    ids.analizar_flujos(df_vacio, "lote_vacio", [])
    error("No lanzó excepción")
except ValueError as e:
    esperado(e)


separador("4. IDS - Lote grande (150 flujos)")
df_pred_big = ids.analizar_flujos(df_big, "lote_big", ids_big)
ok(f"Flujos predichos: {len(df_pred_big)}")
print(df_pred_big.head(3).to_string(index=False))
print("  ...")


# ─────────────────────────────────────────────────────────────────────────────
# 5. DATOS REALES
# ─────────────────────────────────────────────────────────────────────────────
separador("5. DATOS REALES - 7 flujos etiquetados")

ETIQUETAS_REALES = ["BENIGN", "DDoS", "SSH-Patator", "BENIGN", "Web Attack XSS", "Bot", "Web Attack Sql Injection"]

datos_reales = [
    [2,0,4000000.0,0.0,33,-1,3.0,3,3,3,0,0.0,0,12.0,0.0,6,0.0,0,0.0,6,20,0,0,40.0],
    [4,0,5.42816703,0.0,256,-1,4421382.0,340,340,4421382,0,0.0,0,24.0,0.0,6,0.0,0,0.0,6,20,0,0,80.0],
    [2,0,0.0,0.0,259,-1,404.0,404,404,404,0,0.0,0,0.0,0.0,0,0.0,0,0.0,0,32,0,0,64.0],
    [1,2,0.0,1632.65306122449,11584,8688,1225.0,1.0,0.0,0.0,1.0,0.0,1.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,32,0,2.0,32],
    [16,12,2592.21345,1.9752706,29200,286,6075117.0,4,4,1070788,69,1497550.392,6075016,2615.0,13133.0,0,199.0490622,0,1985.141601,7240,32,1,0,520.0],
    [9,9,9.600907867,0.149495105,29200,110,60202640.0,47,234,51200000,637,4645137.318,60200000,322.0,256.0,0,107.3333333,0,85.33333333,322,32,1,1,296.0],
    [2,1,0.0,1968.503937,237,235,508.0,35,508,508,0,0.0,0,0.0,0.0,0,0.0,0,0.0,0,32,0,0,64.0]
]

df_real = pd.DataFrame(datos_reales, columns=nombres)
ids_real = tablas.insertar_flujos(df_real, "lote_real", db_path=DB_PATH)
df_pred_real = ids.analizar_flujos(df_real, "lote_real", ids_real)

df_pred_real["etiqueta_real"] = ETIQUETAS_REALES
df_pred_real["correcto"] = df_pred_real["prediccion"] == df_pred_real["etiqueta_real"]

print(df_pred_real[["id_flujo", "prediccion", "etiqueta_real", "correcto", "confianza", "baja_confianza"]].to_string(index=False))

aciertos = df_pred_real["correcto"].sum()
ok(f"Aciertos: {aciertos}/{len(df_pred_real)}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. SIEM 
# ─────────────────────────────────────────────────────────────────────────────
separador("6. Correlación SIEM para los DATOS REALES - 7 flujos etiquetados")

df_pred_siem = df_pred_real[["id_flujo", "id_lote", "prediccion", "confianza", "baja_confianza"]].copy()

df_resultado = siem.correlacionar_alertas(df_pred_siem, df_real)

print(f"  {'ID':>4}  {'Predicción':<25} {'Severidad':<8}  Recomendación (primeros 60 chars)")

for _, fila in df_resultado.iterrows():
    rec = fila["recomendacion"][:60] + "..."
    print(f"  {fila['id_flujo']:>4}  {fila['prediccion']:<25} {fila['severidad']:<8}  {rec}")

tablas.insertar_resultados(df_resultado, db_path=DB_PATH)

ok("Resultados insertados correctamente en SQLite")


# ─────────────────────────────────────────────────────────────────────────────
# 7. COMPROBACIÓN DE TABLAS SQLITE
# ─────────────────────────────────────────────────────────────────────────────
separador("7. COMPROBACIÓN SQLITE")

import sqlite3

with sqlite3.connect(DB_PATH) as conn:

    print("\nTABLA FLUJOS (solo se imprime el id de cada flujo y su PSH_Flag Count)\n")

    df_flujos_sql = pd.read_sql_query(
        """
        SELECT id_flujo, PSH_Flag_Count
        FROM flujos
        ORDER BY id_flujo
        """,
        conn
    )

    print(df_flujos_sql.to_string(index=False))

    print("\nTABLA RESULTADOS\n")

    df_resultados_sql = pd.read_sql_query(
        """
        SELECT *
        FROM resultados
        ORDER BY id_resultado
        """,
        conn
    )

    print(df_resultados_sql.to_string(index=False))

print("\nFIN DE PRUEBAS")