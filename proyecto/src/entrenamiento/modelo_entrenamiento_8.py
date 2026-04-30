import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)


df1 = pd.read_csv("data/IDS2017_definitivo.csv")
df2 = pd.read_csv("data/UNSW-NB15_definitivo.csv")
df  = pd.concat([df1, df2], ignore_index=True)


X = df.drop("Label", axis=1)
y = df["Label"]


le    = LabelEncoder()
y_enc = le.fit_transform(y)


X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc,
    test_size=0.2,
    random_state=42,
    stratify=y_enc,
)


clases, conteos = np.unique(y_train, return_counts=True)
n_total  = len(y_train)
n_clases = len(clases)
pesos_clase = {
    c: np.sqrt(n_total / (n_clases * cnt))
    for c, cnt in zip(clases, conteos) 
}
pesos_muestras = np.array([pesos_clase[c] for c in y_train])


modelo = XGBClassifier(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=6,

    subsample=0.8,
    colsample_bytree=0.8,

    reg_alpha=0.1,     
    reg_lambda=1.0,     
    gamma=0.1,

    min_child_weight=1,

    objective="multi:softprob",
    num_class=len(clases),

    eval_metric="mlogloss",
    n_jobs=-1,
    random_state=42,
    verbosity=1
)

t0 = time.time()
modelo.fit(X_train, y_train, sample_weight=pesos_muestras)
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
f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
print(f"  {f1:.4f}  ({f1*100:.2f}%)")

print("\n=== MATRIZ DE CONFUSIÓN ===")
print(confusion_matrix(y_test, y_pred))

print("\n=== REPORTE DETALLADO ===")
print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))


importancias = pd.Series(modelo.feature_importances_, index=X.columns)
importancias = importancias.sort_values(ascending=False)

print("\n=== IMPORTANCIA DE CARACTERÍSTICAS ===")
print(importancias)

plt.figure(figsize=(10, 6))
importancias.head(10).sort_values().plot(kind="barh", color="darkorange")
plt.xlabel("Importancia de las características")
plt.title("Top 10 características (XGBoost)")
plt.tight_layout()
plt.show()

print("\n Fin")