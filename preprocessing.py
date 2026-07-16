import requests
import json


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

def 
