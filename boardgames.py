#!/usr/bin/env python3

import random
import requests
import sys
import time
from tqdm import tqdm
import xml.etree.ElementTree as ET

random.seed()

API = "https://www.boardgamegeek.com/xmlapi2/"

GID = 1
VID = 1
PUBLISHER_NAMES = dict()
PUBLISHER_VERSIONS = dict()
DESIGNER_NAMES = dict()
DESIGNER_GAMES = dict()
ARTIST_NAMES = dict()
ARTIST_GAMES = dict()
LANGUAGES = dict()
PROCESSED_IDS = set()
# WAIT = 8
PBAR = tqdm()


def log(s):
    with open("log", "a") as log_file:
        log_file.write(s + "\n")


def add_statement(statement):
    with open("dbvul.txt", "a") as out_file:
        out_file.write(statement + "\n")


def add_game_data(item_id, expands):
    if int(item_id) in PROCESSED_IDS:
        return
    else:
        PROCESSED_IDS.add(int(item_id))

    url = API + "thing?id=" + item_id + "&stats=1&versions=1"
    global WAIT
    time.sleep(2)
    log("Requesting: " + url)
    data = requests.get(url)
    log(str(data))
    while data.status_code == 429:
        time.sleep(32)
        # WAIT *= 2
        log("Requesting: " + url)
        data = requests.get(url)
        log(str(data))
    item = ET.fromstring(data.content)[0]

    global GID
    gid = GID

    game = {
        "gid": str(gid),
        "name": item.find("./name[@type='primary']").attrib["value"],
        "year": item.find("yearpublished").attrib["value"],
        "minplayers": item.find("minplayers").attrib["value"],
        "maxplayers": item.find("maxplayers").attrib["value"],
        "minage": item.find("minage").attrib["value"],
        "rating": item.find("./statistics/ratings/average").attrib["value"],
        "expands": str(expands) if expands else "NULL",
    }

    all_versions = item.findall("./versions/item[@type='boardgameversion']")

    if game["minplayers"] == "0" or not all_versions:
        return  # Not a game or no version exists
    if game["maxplayers"] == "0":
        game["maxplayers"] = "NULL"

    add_statement(
        "INSERT INTO Game VALUES ("
        + game["gid"]
        + ", '"
        + game["name"].replace("'", "''")
        + "', "
        + game["year"]
        + ", "
        + game["minplayers"]
        + ", "
        + game["maxplayers"]
        + ", "
        + game["minage"]
        + ", "
        + game["rating"]
        + ", "
        + game["expands"]
        + ");"
    )
    GID += 1

    global VID
    k = random.randint(0, len(all_versions) - 1)
    versions = [all_versions[0]] + random.sample(all_versions[1:], k)
    for version in versions:
        name = version.find("./name[@type='primary']").attrib["value"]
        add_statement(
            "INSERT INTO Version VALUES ("
            + str(VID)
            + ", '"
            + name.replace("'", "''")
            + "', "
            + str(gid)
            + ");"
        )
        for lang in version.findall("./link[@type='language']"):
            add_statement(
                "INSERT INTO InLanguage VALUES ("
                + lang.attrib["id"]
                + ", "
                + str(VID)
                + ");"
            )
            LANGUAGES[lang.attrib["id"]] = lang.attrib["value"]

        publishers = version.findall("./link[@type='boardgamepublisher']")
        for publisher in publishers:
            id = publisher.attrib["id"]
            if not id in PUBLISHER_NAMES:
                PUBLISHER_NAMES[id] = publisher.attrib["value"]
                PUBLISHER_VERSIONS[id] = [VID]
            else:
                PUBLISHER_VERSIONS[id].append(VID)

        VID += 1

    designers = item.findall("./link[@type='boardgamedesigner']")
    for designer in designers:
        id = designer.attrib["id"]
        if not id in DESIGNER_GAMES:
            DESIGNER_NAMES[id] = designer.attrib["value"]
            DESIGNER_GAMES[id] = [gid]
        else:
            DESIGNER_GAMES[id].append(gid)

    artists = item.findall("./link[@type='boardgameartist']")
    for artist in artists:
        id = artist.attrib["id"]
        if not id in ARTIST_GAMES:
            ARTIST_NAMES[id] = artist.attrib["value"]
            ARTIST_GAMES[id] = [gid]
        else:
            ARTIST_GAMES[id].append(gid)

    all_expansions = item.findall("./link[@type='boardgameexpansion']")
    inbound = item.findall("./link[@type='boardgameexpansion'][@inbound]")
    real_expansions = set(all_expansions) - set(inbound)
    k = random.randint(0, len(real_expansions))
    expansions = random.sample(real_expansions, k)
    PBAR.total += len(expansions)
    PBAR.update(0)
    for expansion in expansions:
        add_game_data(expansion.attrib["id"], gid)
        PBAR.update(1)


def main():
    PBAR.total = len(sys.argv[1:])
    PBAR.update(0)
    for arg in sys.argv[1:]:
        add_game_data(arg, None)
        PBAR.update(1)

    pubid = 1
    for id, name in PUBLISHER_NAMES.items():
        add_statement(
            "INSERT INTO Publisher VALUES ("
            + str(pubid)
            + ", '"
            + name.replace("'", "''")
            + "');"
        )
        for version in PUBLISHER_VERSIONS[id]:
            add_statement(
                "INSERT INTO Publishes VALUES ("
                + str(pubid)
                + ", "
                + str(version)
                + ");"
            )
        pubid += 1

    perid = 1
    for id, name in DESIGNER_NAMES.items():
        add_statement("INSERT INTO Person VALUES (" + str(perid) + ", '" + name + "');")
        for game in DESIGNER_GAMES[id]:
            add_statement(
                "INSERT INTO Job VALUES ("
                + str(game)
                + ", "
                + str(perid)
                + ", 'Design');"
            )
        perid += 1
    for id, name in ARTIST_NAMES.items():
        add_statement("INSERT INTO Person VALUES (" + str(perid) + ", '" + name + "');")
        for game in ARTIST_GAMES[id]:
            add_statement(
                "INSERT INTO Job VALUES (" + str(game) + ", " + str(perid) + ", 'Art');"
            )
        perid += 1

    add_statement(
        "-- Move these to the top, also replace the numbers by two-letter codes"
    )
    for id, name in LANGUAGES.items():
        add_statement("INSERT INTO Language VALUES (" + id + ", '" + name + "');")


if __name__ == "__main__":
    main()
