from utils import init_mongo_client
import re
import json

import concurrent.futures
from tqdm import tqdm


class Patterns:
    '''
    Reused regex patterns
    '''
    price = re.compile(r"£(\d+(?:\.\d+)?)|(\d+)p")
    simple = re.compile(r"\S+ Clubcard Price")
    nforn = re.compile(r"^(\d+) for (\d+)")
    nfor = re.compile(r"^(\d+) for (\S+)")
    anyforn = re.compile(r"^Any (\d+) for (\d+)")
    anyfor = re.compile(r"^Any (\d+) for (\S+)")
    mealdeal = re.compile(r"^(.*?) Meal Deal for (\S+)")
    multitext = re.compile(r".*? - (.*$)")
    off = re.compile(r"(.*?)(\S+) OFF")
    clear = re.compile("Reduced to Clear")


def extract_price(text):
    '''
    Get the price in pounds from some text (works with pounds and pennies)
    '''
    match = re.search(Patterns.price, text)
    if match:
        if match.group(1):
            return float(match.group(1))
        elif match.group(2):
            return int(match.group(2)) / 100
        else:
            return None

    return None


def parse_deal(text, price):
    ''' 
    Parse an offerText, returning the offer's information (also uses base price)
    '''

    # Simple deal
    if re.match(Patterns.simple, text):
        deal_price = extract_price(text)
        return {
            "type": "simple",
            "dealPrice": deal_price,
            "netSave": price - deal_price,
            "percSave": (price - deal_price) / price,
        }

    # <n> for <n>
    nforn_m = re.match(Patterns.nforn, text)
    if nforn_m:
        n = int(nforn_m.group(1))
        f = extract_price(nforn_m.group(2))
        return {
            "type": "nforn",
            "n": n,
            "for": f,
            "details": re.match(Patterns.multitext, text).group(1),
            "netSave": price * (n - f) / n,
            "percSave": (n - f) / n,
        }

    # <n> for <price> (there are none of these I think)
    nfor_m = re.match(Patterns.nfor, text)
    if nfor_m:
        n = int(nfor_m.group(1))
        f = extract_price(nfor_m.group(2))
        return {
            "type": "nfor",
            "n": n,
            "for": f,
            "details": re.match(Patterns.multitext, text).group(1),
            "netSave": (n * price - f) / n,
            "percSave": (n * price - f) / (n * price),
        }

    # Any <n> for <n>
    anyforn_m = re.match(Patterns.anyforn, text)
    if anyforn_m:
        n = int(anyforn_m.group(1))
        f = int(anyforn_m.group(2))
        return {
            "type": "anyforn",
            "n": n,
            "for": f,
            "details": re.match(Patterns.multitext, text).group(1),
            "netSave": price * (n - f) / n,
            "percSave": (n - f) / n,
        }

    # Any <n> for <price>
    anyfor_m = re.match(Patterns.anyfor, text)
    if anyfor_m:
        n = int(anyfor_m.group(1))
        f = extract_price(anyfor_m.group(2))
        return {
            "type": "anyfor",
            "n": n,
            "for": f,
            "details": re.match(Patterns.multitext, text).group(1),
            "netSave": (n * price - f) / n,
            "percSave": (n * price - f) / (n * price),
        }

    # Meal Deal for <price>
    mealdeal_m = re.match(Patterns.mealdeal, text)
    if mealdeal_m:
        return {
            "type": "mealdeal",
            "dealClass": mealdeal_m.group(1),
            "dealPrice": extract_price(mealdeal_m.group(2)),
            "details": re.match(Patterns.multitext, text).group(1),
        }

    # <price> OFF
    off_m = re.match(Patterns.off, text)
    if off_m:
        off = extract_price(off_m.group(2))
        return {
            "type": "off",
            "dealClass": off_m.group(1),
            "off": off,
            "netSave": off,
            "percSave": (price - off) / price,
        }

    # Reduced to Clear
    clear_m = re.match(Patterns.clear, text)
    if clear_m:
        return {
            "type": "clear",
        }

    return {"type": "unrecognised"}


def parse_and_update_product(product):
    ''' 
    Parse and update a single document's offerText on mongoDB
    '''
    # Get deals
    deals = [
        parse_deal(d['offerText'], product["price"])
        for d in product['promotions']
    ]

    # Update document
    client["test"]["products"].update_one(
        {"_id": product["_id"]}, {"$set": {
            "parsedPromotions": deals
        }})


def parse_and_update_collection():
    '''
    Parse each document's offerText on the DB, and update doc with info
    This is done in parallel using concurrent.futures
    '''
    # Fetch all products from DB
    db = client["test"]
    products = db["products"].find({}, {
        "promotions.offerText": 1,
        "price": "$product.price"
    })
    n = db["products"].count_documents({})

    print(f"Going to parse and update {n} products")

    # Update documents in parallel
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(30, n)) as executor:
        results = list(
            tqdm(executor.map(parse_and_update_product, products), total=n))


def fetch_and_update_one(t="simple"):
    '''
    Fetch and update a product with a particular deal type (for debugging)
    '''
    db = client["test"]
    product = db["products"].find_one({"parsedPromotions.type": t}, {
        "promotions.offerText": 1,
        "price": "$product.price"
    })

    print(f"Updating one of {t} type")
    print(product)

    parse_and_update_product(product)


def test_all_offerText():
    '''
    Fetch all unique offer texts from DB and parse them (for debugging)
    '''
    # Get a list of all promotion texts
    texts = list(client["test"]["products"].aggregate([{
        '$unwind': {
            'path': '$promotions'
        }
    }, {
        '$group': {
            '_id': '$promotions.offerText'
        }
    }, {
        '$group': {
            '_id': '1',
            'offerTexts': {
                '$push': '$_id'
            }
        }
    }]))[0]['offerTexts']

    deals = []
    for text in texts:
        print(text)
        deal = parse_deal(text, 1)
        deals += [deal]
        print(json.dumps(deal, indent=2))
        print("")

    print("UNRECOGNISED:")
    for deal in deals:
        if deal["type"] == "unrecognised":
            print(json.dumps(deal, indent=2))


if __name__ == "__main__":
    client = init_mongo_client()

    parse_and_update_collection()

    # test_all_offerText()
    # fetch_and_update_one("off")