import requests
import json
import numpy as np
import pandas as pd
import sqlite3
import sys


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
        matches_df = pd.read_sql_query("SELECT * FROM matches", conn)
        players_df = pd.read_sql_query("SELECT * FROM participants", conn)

    roles = {"TOP" : 0, "JUNGLE" : 1, "MIDDLE" : 2, "BOTTOM" : 3, "UTILITY" : 4}
    num_champs = len(champ_to_idx)
    X = []
    y = []

    for match in matches_df.itertuples():
        vector = np.zeros(10 * num_champs, dtype=int)
        match_id = match.match_id
        blueW = match.blueW

        participants = players_df.groupby("match_id")
        players = participants.get_group(match_id)

        for player in players.itertuples():
            team_offset = 0 if player.team_id == 100 else 5
            position_offset = roles[player.position]
            index = champ_to_idx[player.champion_id]
            vec_index = (team_offset + position_offset) * num_champs + index
            vector[vec_index] ^= 1

        X.append(vector)
        y.append(blueW)

    X = np.array(X)
    y = np.array(y)
    return X, y



