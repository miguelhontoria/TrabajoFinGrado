import pandas as pd
import numpy as np

def generar_flujos_sinteticos(ruta_entrada, ruta_salida, seed=42):
    np.random.seed(seed)
    
    print("Cargando archivo original...")
    df = pd.read_csv(ruta_entrada)
    
    if 'Label' in df.columns:
        df = df.drop('Label', axis=1)
        
    print(f"Procesando {len(df)} filas...")

    ruido_paquetes = np.random.choice([-1, 0, 1], size=len(df), p=[0.25, 0.50, 0.25])
    df['Total Fwd Packet'] = df['Total Fwd Packet'] + ruido_paquetes
    df['Total Fwd Packet'] = df['Total Fwd Packet'].clip(lower=1).astype(int)

    ruido_bytes = np.random.normal(loc=1.0, scale=0.05, size=len(df))
    df['Flow Bytes/s'] = df['Flow Bytes/s'] * ruido_bytes
    df['Flow Bytes/s'] = df['Flow Bytes/s'].clip(lower=0.0).round(4)

    ruido_iat = np.random.normal(loc=1.0, scale=0.10, size=len(df))
    df['Flow IAT Min'] = df['Flow IAT Min'] * ruido_iat
    df['Flow IAT Min'] = df['Flow IAT Min'].clip(lower=0.0).round(4)

    df.to_csv(ruta_salida, index=False)
    print(f"FIN. Archivo sintético guardado en: {ruta_salida}")

ARCHIVO_ENTRADA = "../ArchivosPruebas/CSV-5MB.csv" 
ARCHIVO_SINTETICO = "../ArchivosPruebas/FlujosSintéticos/CSV-5MB_sintéticos.csv"

if __name__ == "__main__":
    generar_flujos_sinteticos(ARCHIVO_ENTRADA, ARCHIVO_SINTETICO)