import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


datos = pd.read_csv("../../datos/originales/Data.csv")
etiquetas = pd.read_csv("../../datos/originales/Label.csv")

datos["Label"] = etiquetas.iloc[:, 0]

X = datos.drop("Label", axis=1)
y = datos["Label"]


for columna in X.columns:
    limite_inferior = X[columna].quantile(0.001)
    limite_superior = X[columna].quantile(0.999)
    X[columna] = X[columna].clip(limite_inferior, limite_superior)


porcentaje_ceros = (X == 0).sum() / len(X)
columnas_ceros = porcentaje_ceros[porcentaje_ceros > 0.95].index
X = X.drop(columns=columnas_ceros)

print("Columnas eliminadas por exceso de ceros:")
print(list(columnas_ceros))


muestra = X.sample(n=5000, random_state=42)

matriz_corr = muestra.corr(method="spearman").abs()
triangular_superior = matriz_corr.where(np.triu(np.ones(matriz_corr.shape), k=1).astype(bool))

umbral = 0.95
columnas_correlacionadas = []

for columna in triangular_superior.columns:
    correlaciones_altas = triangular_superior[columna][triangular_superior[columna] > umbral]
    if len(correlaciones_altas) > 0:
        columnas_correlacionadas.append(columna)

print("\nColumnas eliminadas por alta correlación:")
print(columnas_correlacionadas)

X_final = X.drop(columns=columnas_correlacionadas)


datos_finales = pd.concat([X_final, y.reset_index(drop=True)], axis=1)

print("\n=== INFORMACIÓN FINAL ===")
print(datos_finales.info())

print("\n=== ESTADÍSTICAS DESCRIPTIVAS ===")
print(datos_finales.describe())

plt.figure()
sns.countplot(x="Label", data=datos_finales)
plt.title("Distribución de clases")
plt.xticks(rotation=45)
plt.show()

plt.figure(figsize=(10,8))
sns.heatmap(muestra.corr(method="spearman"), cmap="coolwarm", linewidths=0.5)
plt.title("Mapa de correlación (muestra)")
plt.show()


datos_finales.to_csv("../../datos/procesados/UNSW-NB15_limpio.csv", index=False)