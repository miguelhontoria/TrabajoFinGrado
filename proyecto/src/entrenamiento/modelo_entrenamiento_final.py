import time, joblib, os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
 
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)


df1 = pd.read_csv("../../datos/procesados/UNSW-NB15_definitivo.csv")
df2 = pd.read_csv("../../datos/procesados/IDS2017_definitivo.csv")
df  = pd.concat([df1, df2], ignore_index=True)


X = df.drop("Label", axis=1)
y = df["Label"]


X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2,
    random_state=42,
    stratify=y, 
)

modelo = RandomForestClassifier(
    n_estimators=200,
    criterion="entropy",
    max_depth=None,        
    min_samples_split=5,
    min_samples_leaf=2,
    max_features=0.5,
    class_weight="balanced",  
    n_jobs=-1,
    random_state=42,
    verbose=2
)

t0 = time.time()
modelo.fit(X_train, y_train)
t1 = time.time()


print(f"\n Entrenamiento completado en {(t1 - t0):.1f} segundos\n")


y_pred  = modelo.predict(X_test)
y_proba = modelo.predict_proba(X_test)


print("\n=== EXACTITUD (ACCURACY) ===")
exactitud = accuracy_score(y_test, y_pred)
print(f"  {exactitud:.4f}  ({exactitud*100:.2f}%)")

print("\n=== PRECISIÓN (PPV) ===")
precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
print(f"  {precision:.4f}  ({precision*100:.2f}%)")

print("\n=== EXHAUSTIVIDAD (RECALL / PD) ===")
exhaustividad = recall_score(y_test, y_pred, average="weighted", zero_division=0)
print(f"  {exhaustividad:.4f}  ({exhaustividad*100:.2f}%)")

print("\n=== PUNTUACIÓN F1 ===")
f1 = f1_score(y_test, y_pred, average="weighted")
print(f"  {f1:.4f}  ({f1*100:.2f}%)")

print("\n=== MATRIZ DE CONFUSIÓN ===")
print(confusion_matrix(y_test, y_pred))

print("\n=== REPORTE DETALLADO ===")
print(classification_report(y_test, y_pred))

importancias = pd.Series(modelo.feature_importances_, index=X.columns)
importancias = importancias.sort_values(ascending=False)
 
print("\n=== IMPORTANCIA DE CARACTERÍSTICAS ===")
print(importancias)
 
plt.figure(figsize=(10, 6))
importancias.head(10).sort_values().plot(kind="barh", color="steelblue")
plt.xlabel("Importancia de las características")
plt.title("Top 10 características (Random Forest)")
plt.tight_layout()
plt.show()


print("\nFIN entrenamiento")


RUTA_MODELOS = "../../info_modelo"
clases = modelo.classes_
umbrales_confianza = {}

for i, clase in enumerate(clases):
    mask_real     = (y_test.values == clase)
    mask_correcto = mask_real & (y_pred == clase)
    n_aciertos    = mask_correcto.sum()

    if n_aciertos < 50:
        umbral = 0.50
    else:
        probas_correctas = y_proba[mask_correcto, i]
        if 50 <= n_aciertos < 500:
            p = 10
        elif 500 <= n_aciertos < 5000:
            p = 15
        elif 5000 <= n_aciertos < 50000:
            p = 20
        else:
            p = 25
        umbral = float(np.percentile(probas_correctas, p))

    umbrales_confianza[clase] = round(umbral, 4)

print("\n=== UMBRALES DE CONFIANZA POR CLASE ===")
for clase, umbral in sorted(umbrales_confianza.items()):
    print(f"  {clase:<35} {umbral:.4f}")

joblib.dump(modelo, os.path.join(RUTA_MODELOS, "modelo_random_forest.pkl"))
print("\n Modelo entrenado guardado")

joblib.dump(list(X.columns), os.path.join(RUTA_MODELOS, "nombres_caracteristicas.pkl"))
print(f"\n {len(X.columns)} Nombres de las características en orden guardados")

joblib.dump(list(clases), os.path.join(RUTA_MODELOS, "clases.pkl"))
print(f"\n {len(clases)} clases: {list(clases)} guardadas")

joblib.dump(umbrales_confianza, os.path.join(RUTA_MODELOS, "umbrales_confianza.pkl"))
print("\n Umbrales de confianza por clase guardados")

joblib.dump(importancias.to_dict(), os.path.join(RUTA_MODELOS, "importancia_caracteristicas.pkl"))
print("\n Importancia de variables guardada")

joblib.dump(y.value_counts().to_dict(), os.path.join(RUTA_MODELOS, "distribucion_clases.pkl"))
print("\n Distribución por clases guardada")

joblib.dump(confusion_matrix(y_test, y_pred), os.path.join(RUTA_MODELOS, "matriz_confusion.pkl"))
print("\n Matriz de confusión guardada")

reporte_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
joblib.dump(reporte_dict, os.path.join(RUTA_MODELOS, "reporte_completo.pkl"))
print("\n Reporte detallado completo guardado")

macro_precision = reporte_dict["macro avg"]["precision"]
macro_recall    = reporte_dict["macro avg"]["recall"]
macro_f1        = reporte_dict["macro avg"]["f1-score"]

info_modelo = {
    "modelo": "RandomForest",
    "n_estimators": 200,
    "criterion":"entropy",
    "max_depth":None,        
    "min_samples_split":5,
    "min_samples_leaf":2,
    "max_features":0.5,
    "class_weight":"balanced",  
    "n_jobs":-1,
    "random_state":42,
    "verbose":2,
    "Fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
    "Entrenado en (segs)": round(t1 - t0, 2),
    "Exactitud(ACC)":round(exactitud, 6),
    "Precisión(PPV)":round(precision, 6),
    "Exhaustividad(RECALL / PD)":round(exhaustividad, 6),
    "Puntuación F1":round(f1, 6),
    "Precisión(macro avg)":round(macro_precision, 6),
    "Exhaustividad(macro avg)":round(macro_recall, 6),
    "Puntuación F1(macro avg)":round(macro_f1, 6),
    "Número de atributos":len(X.columns),
    "Número de clases":len(clases),
    "Número de muestras conjunto entrenamiento":len(X_train),
    "Número de muestras conjunto test":len(X_test),
    "Umbral_confianza_min": min(umbrales_confianza.values()),
    "Umbral_confianza_max": max(umbrales_confianza.values())
}

joblib.dump(info_modelo, os.path.join(RUTA_MODELOS, "info_modelo.pkl"))
print("\n Información del modelo y métricas guardados")

print("\nFIN")



