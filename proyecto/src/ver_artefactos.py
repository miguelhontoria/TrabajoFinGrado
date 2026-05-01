import joblib

ruta = "../info_modelo/umbrales_confianza.pkl"
data = joblib.load(ruta)
print(data)