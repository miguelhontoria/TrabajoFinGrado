import pandas as pd

unsw = pd.read_csv("../../datos/procesados/UNSW-NB15_limpio.csv")
ids = pd.read_csv("../../datos/procesados/IDS2017_limpio.csv")


label_map_unsw = {
    0: "BENIGN",
    1: "Analysis",
    2: "Backdoor",
    3: "DoS",
    4: "Exploits",
    5: "Fuzzers",
    6: "Generic",
    7: "Reconnaissance",
    8: "Shellcode",
    9: "Worms"
}

unsw["Label"] = unsw["Label"].map(label_map_unsw)


ids = ids.rename(columns={
    "Total Fwd Packets": "Total Fwd Packet",
    "Total Backward Packets": "Total Bwd packets",
    "Total Length of Fwd Packets": "Total Length of Fwd Packet",
    "Total Length of Bwd Packets": "Total Length of Bwd Packet",
    "Max Packet Length": "Packet Length Max",
    "Init_Win_bytes_forward": "FWD Init Win Bytes",
    "Init_Win_bytes_backward": "Bwd Init Win Bytes",
    "act_data_pkt_fwd": "Fwd Act Data Pkts",
    "min_seg_size_forward": "Fwd Seg Size Min"
})


features_comunes = [
    "Total Fwd Packet",
    "Total Bwd packets",
    "Flow Bytes/s",
    "Bwd Packets/s",
    "FWD Init Win Bytes",
    "Bwd Init Win Bytes",

    "Flow Duration",
    "Flow IAT Min",
    "Fwd IAT Min",
    "Fwd IAT Total",
    "Bwd IAT Min",
    "Bwd IAT Std",
    "Bwd IAT Total",

    "Total Length of Fwd Packet",
    "Total Length of Bwd Packet",
    "Fwd Packet Length Min",
    "Fwd Packet Length Std",
    "Bwd Packet Length Min",
    "Bwd Packet Length Std",
    "Packet Length Max",
    "Fwd Seg Size Min",

    "PSH Flag Count",

    "Down/Up Ratio",
    "Fwd Header Length"
]


unsw_final = unsw[features_comunes + ["Label"]]
ids_final = ids[features_comunes + ["Label"]]


dataset_final = pd.concat([unsw_final, ids_final], axis=0)

dataset_final.reset_index(drop=True, inplace=True)


unsw_final.to_csv("../../datos/procesados/UNSW-NB15_definitivo.csv", index=False)
ids_final.to_csv("../../datos/procesados/IDS2017_definitivo.csv", index=False)

print(dataset_final["Label"].value_counts())
print(dataset_final.info())