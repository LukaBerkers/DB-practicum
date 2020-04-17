#!/usr/bin/env python3

import random
import sys

random.seed()

OUT_FILE = "sellers.txt"

MAX_VERSION_ID = 2565
ONLINE_SELLERS = {
    "Amazon.com": "www.amazon.com",
    "Amazon.nl": "www.amazon.nl",
    "bol.com": "www.bol.com",
    "Goedkopegezelschapsspellen.nl": "www.goedkopegezelschapsspellen.nl",
    "Intertoys Online": "www.intertoys.nl",
}
OFFLINE_SELLERS = {
    "Intertoys Eindhoven-Woensel": "Woensel 109 5625 AG Eindhoven",
    "Intertoys Eindhoven Heuvel Galerie": "Heuvel Galerie 241 5611 DK Eindhoven",
    "Intertoys Utrecht-Overvecht": "Roelantdreef 240 3562 KH Utrecht",
    "Intertoys Utrecht Hoog Catharijne": "Godebaldkwartier 335 3511 DS Utrecht",
    "Eppo": "Kleine Berg 33 5611 JS Eindhoven",
}


def add_statement(statement):
    with open(OUT_FILE, "a") as out_file:
        out_file.write(statement + "\n")


def add_sellers():
    sid = 1
    for name, address in {**ONLINE_SELLERS, **OFFLINE_SELLERS}.items():
        on_off = "On" if name in ONLINE_SELLERS else "Off"
        add_statement(
            "INSERT INTO "
            + on_off
            + "lineSeller VALUES ("
            + str(sid)
            + ", '"
            + name
            + "', '"
            + address
            + "');"
        )
        sid += 1

    return sid - 1


def add_sales(max_seller_id):
    for _ in range(int(sys.argv[1])):
        sid = random.randint(1, max_seller_id)
        vid = random.randint(1, MAX_VERSION_ID)
        price = int(random.gauss(3000, 1000))
        while price <= 0:
            price = int(random.gauss(3000, 1000))
        price = 5 * round(price / 5)  # Round to nearest 5
        add_statement(
            "INSERT INTO Sale VALUES ("
            + str(sid)
            + ", "
            + str(vid)
            + ", "
            + str(price)
            + ");"
        )


def main():
    max_seller_id = add_sellers()
    add_sales(max_seller_id)


if __name__ == "__main__":
    main()
