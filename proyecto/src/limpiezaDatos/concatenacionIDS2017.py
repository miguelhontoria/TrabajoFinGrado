import pandas as pd
import glob
import os

ruta = "../../datos/originales"   

archivos = glob.glob(os.path.join(ruta, "*ISCX.csv"))

print("Archivos encontrados:")
for a in archivos:
    print(" -", os.path.basename(a))

dfs = []

for archivo in archivos:
    df = pd.read_csv(
        archivo,
        dtype=str,               
        keep_default_na=False,  
        na_values=[]           
    )
    
    df.columns = df.columns.str.strip()
    dfs.append(df)

df_total = pd.concat(dfs, axis=0, ignore_index=True)

print("\nNúmero total de filas concatenadas:", len(df_total))
print("Número total de columnas:", len(df_total.columns))

df_total.to_csv("../../datos/procesados/IDS2017_concatenado.csv", index=False)