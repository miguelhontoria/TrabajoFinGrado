import time
import pandas as pd
import matplotlib.pyplot as plt
 
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
    n_estimators=100,
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

print("\nFIN")
