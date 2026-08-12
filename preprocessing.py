import requests
import json
import numpy as np
import pandas as pd
import sqlite3
import sys
from sklearn.model_selection import train_test_split

TEST_SIZE = 0.2

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

def calculate_winrates(matches_df, players_df):
    stats = {}

    #turns df into dict where match_id is key and blueW is value
    match_results = matches_df.set_index("match_id")["blueW"].to_dict()
    for match_id, players in players_df.groupby("match_id"):

        blue_won = match_results[match_id]

        for player in players.itertuples():
            champ = player.champion_id

            if player.team_id == 100:
                won = blue_won
            else:
                won = 1 - blue_won

            if champ not in stats:
                # wins, games
                stats[champ] = [0, 0]

            stats[champ][1] += 1
            stats[champ][0] += won
            
    return {
        champ: wins / games
        for champ, (wins, games) in stats.items()
    }


def preprocess():
    
    champ_to_idx = load_mapping()

    with sqlite3.connect("matches.db") as conn:
        matches_df = pd.read_sql_query("SELECT * FROM matches", conn)
        players_df = pd.read_sql_query("SELECT * FROM participants", conn)


    print("preprocessing")
    roles = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]

    # makes sure that every match has 10 players and 2 players for each role
    valid_matches = (
            players_df
            .groupby("match_id")
            .filter(lambda x: len(x) == 10 and x["position"].isin(roles).all())
        )
    
    valid_ids = valid_matches["match_id"].unique()
    matches_df = matches_df[matches_df["match_id"].isin(valid_ids)]

    # split data
    training_matches, testing_matches = train_test_split(matches_df, test_size=TEST_SIZE, stratify=matches_df["blueW"])

    training_ids = set(training_matches["match_id"])
    testing_ids = set(testing_matches["match_id"])
    training_players = players_df[players_df["match_id"].isin(training_ids)]
    testing_players = players_df[players_df["match_id"].isin(testing_ids)]
    
    winrates = calculate_winrates(training_matches, training_players)

    num_champs = len(champ_to_idx)
    participants = players_df.groupby("match_id")
    X = []
    y = []

    # making multi-hot encoded vector
    for match in matches_df.itertuples():
        vector = np.zeros(2 * num_champs + 3, dtype=int)
        match_id = match.match_id
        blueW = match.blueW

        players = participants.get_group(match_id)

        blueWR = 0
        redWR = 0

        for player in players.itertuples():
            team_offset = 0 if player.team_id == 100 else 1
            index = champ_to_idx[player.champion_id]
            vec_index = team_offset * num_champs + index
            vector[vec_index] ^= 1

            if team_offset == 0:
                blueWR += winrates.get(player.champion_id, 0.5)
            else:
                redWR += winrates.get(player.champion_id, 0.5)
            
        vector[-3] = blueWR
        vector[-2] = redWR
        vector[-1] = blueWR - redWR
        X.append(vector)
        y.append(blueW)

    X = np.array(X)
    y = np.array(y)
    np.save('X.npy', X)
    np.save('y.npy', y)
    print("done")

if __name__ == "__main__":
    preprocess()



