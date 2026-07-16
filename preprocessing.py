import requests
import json
import numpy as np
import pandas as pd
import sqlite3


def get_champs_data():
    url = "https://ddragon.leagueoflegends.com/cdn/16.14.1/data/en_US/champion.json"

    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(response.status_code)
        print("Something went wrong")

def create_mapping(champ_data):
    champ_to_idx = {}

    for idx, champ in enumerate(champ_data["data"].values()):
        champ_id = int(champ["key"])
        champ_to_idx[champ_id] = idx
    
    with open("champ_mapping.json", "w") as f:
        json.dump(champ_to_idx, f, indent=4)

def load_mapping():
    with open("champ_mapping.json", "r") as f:
        champ_to_idx = json.load(f)

    # turns keys back into ints
    champ_to_idx = {int(k): v for k, v in champ_to_idx.items()}
    return champ_to_idx

def preprocess():
    champ_to_idx = load_mapping()

    with sqlite3.connect("matches.db") as conn:
        df = pd.read_sql_query("SELECT * FROM matches", conn)

    cols = 2 * len(champ_to_idx)
    X = []
    for _, row in df.iterrows():
        vector = np.zeros(cols)
        
        blue_champs = row[["blue1", "blue2", "blue3", "blue4", "blue5"]]
        red_champs = row[["red1", "red2", "red3", "red4", "red5"]]

        for champ in blue_champs:
            vector[champ_to_idx[champ]] = 1
        
        for champ in red_champs:
            vector[len(champ_to_idx) + champ_to_idx[champ]] = 1
        
        X.append(vector)
    X = np.array(X)
    y = df["blueW"].values

