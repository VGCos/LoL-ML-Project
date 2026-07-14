from dotenv import load_dotenv
import sqlite3
import os
import requests
import sys
import time


load_dotenv()
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
REGION = "na1"
DB_NAME = "matches.db"
def initialize_database():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                    match_id TEXT PRIMARY KEY,
                    blue1 INTEGER,
                    blue2 INTEGER,
                    blue3 INTEGER,
                    blue4 INTEGER,
                    blue5 INTEGER,
                    red1 INTEGER,
                    red2 INTEGER,
                    red3 INTEGER,
                    red4 INTEGER,
                    red5 INTEGER,
                    blueW INTEGER
                )
        """)

        conn.commit()

def get_puuids():
    url = f"https://{REGION}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        print("OK")
        data = response.json()['entries']
        
        puuids = []
        for entry in data:
            puuids.append(entry["puuid"])

        return puuids
    
    else:
        # handles getting rate limited
        if response.status_code == 429:
            seconds = response.headers.get("Retry-After")
            print(f"retrying after {seconds} seconds")
            time.sleep(int(seconds))
        else:
            print(response.status_code)
            print(response.text)
            print("something went wrong getting puuids")
            sys.exit()


def get_match_ids(puuid):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        # handles getting rate limited
        if response.status_code == 429:
            seconds = response.headers.get("Retry-After")
            print(f"retrying after {seconds} seconds")
            time.sleep(int(seconds))
            return []
        else:
            print(response.status_code)
            print(response.text)
            print("something went wrong getting matches")
            sys.exit()


def match_exists(cursor, match_id):
    cursor.execute(
        "SELECT 1 FROM matches where match_id = ?",
        (match_id,)
    )
    return cursor.fetchone() is not None


def get_match_data(match_id):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    time.sleep(0.1)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        # handles getting rate limited
        if response.status_code == 429:
            seconds = response.headers.get("Retry-After")
            print(f"retrying after {seconds} seconds")
            time.sleep(int(seconds))
        else:
            print(response.status_code)
            print(response.text)
            print("something went wrong getting match data")
            sys.exit()


def insert_match_data(cursor, match_data):
    match_id = match_data["metadata"]["matchId"]
    participants = match_data["info"]["participants"]
    teams = match_data["info"]["teams"]

    # restricts to only ranked solo/duo
    if match_data["info"]["queueId"] != 420:
        return
    
    blue = []
    red = []
    for player in participants:
        champ = player["championId"]
        if player["teamId"] == 100:
            blue.append(champ)
        else:
            red.append(champ)
    
    for team in teams:
        if team["teamId"] == 100:
            if team["win"] == True:
                blue_won = 1
            else:
                blue_won = 0
    
    cursor.execute("""INSERT OR IGNORE INTO matches (
                match_id,
                blue1, blue2, blue3, blue4, blue5,
                red1, red2, red3, red4, red5,
                blueW
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    match_id,
                    *blue,
                    *red,
                    blue_won
                ))


#to do: test more and collect data
if __name__ == "__main__":
    
    initialize_database()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        i = 0
        print("getting puuids")
        puuids = get_puuids()
        print("got puuids")

        for puuid in puuids:
            print("getting match ids")
            match_ids = get_match_ids(puuid)
            print("got match ids")

            for match_id in match_ids:
                if not match_exists(cursor, match_id):
                    match_data = get_match_data(match_id)
                    # if we get rate limited
                    if match_data is None:
                        continue
                    print(f"inserting {i}")
                    insert_match_data(cursor, match_data)
                    print(f"inserted {i}")

                    i += 1
                    if i % 50 == 0:
                        conn.commit()
        




