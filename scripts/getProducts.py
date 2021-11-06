from utils import deep_get, init_mongo_client

import requests as rq

from bs4 import BeautifulSoup
import lxml
import orjson

import numpy as np
import concurrent.futures
from tqdm import tqdm


def fetch_products(page, count):
    '''
    Returns the raw Response.content from a get request to the promotions endpoint
    '''
    headers = {
        "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    params = {"page": page, "count": count}

    res = rq.request(
        "GET",
        "https://www.tesco.com/groceries/en-GB/promotions/alloffers",
        params=params,
        headers=headers,
        timeout=10)

    return res.content


def get_total_products():
    '''
    Returns the total number of products available on the offers page 
    '''
    content = fetch_products(1, 1)

    soup = BeautifulSoup(content, 'lxml')
    body = soup.find('body')
    props = body["data-props"]

    # Parse json
    data = orjson.loads(props)

    # Get the total number of products on offer
    path = ["resources", "promotionsIdOrType", "data", "totalCount"]
    n = deep_get(data, path) or 0

    return int(n)


def get_products(page, count):
    '''
    Calls fetch_products, and extracts the products info using nested deep_get
    '''
    content = fetch_products(page, count)

    # Load in to BeautifulSoup
    soup = BeautifulSoup(content, 'lxml')
    body = soup.find('body')
    props = body["data-props"]

    # Parse json
    data = orjson.loads(props)

    # Get the products data
    path = [
        "resources", "promotionsIdOrType", "data", "results", "productItems"
    ]
    products = deep_get(data, path)

    if not products: products = []

    return products


def get_products_and_upload(page, count):
    ''' 
    Wraps the get_products function and uploads returned products to MongoDB
    '''
    products = get_products(page, count)

    # db["products"].insert_many(products)

    # If we want to upsert, we have to loop
    for product in products:
        db["products"].update_one({"product.gtin": product["product"]["gtin"]},
                                  {"$set": product},
                                  upsert=True)

    return "Success" if len(products) == count else "Error"


def get_n_products(n):
    '''
    Retrieve n products in parallel (will upload to MongoDB)
    '''
    # Number of items to load per page (determined by scripts in optimize.py)
    OPTIMUM_BATCH = 256

    # Construct a list of (page, count) up the amount of products requested
    pages = np.arange(1, np.ceil(n / OPTIMUM_BATCH) + 1, dtype=int)
    counts = np.full_like(pages, OPTIMUM_BATCH)
    counts[-1] = n % OPTIMUM_BATCH or OPTIMUM_BATCH

    print(
        f"Getting {n} products (batches of {OPTIMUM_BATCH} over {len(pages)} pages)"
    )

    # Request them in parallel
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(20, len(pages))) as executor:
        results = list(
            tqdm(
                executor.map(
                    get_products_and_upload,
                    pages,
                    counts,
                ),
                total=len(pages),
            ))

    res = list(set(results))
    if len(res) == 1 and res[0] == "Success":
        print("All products fetched successfully")
    else:
        print("\nAn error occured, SUMMARY:")
        for i, result in enumerate(results):
            print(f"\t[{i+1}/{len(pages)}] (count={counts[i]}) {result}")


if __name__ == "__main__":
    client = init_mongo_client()
    db = client['test']

    n = get_total_products()
    print(f"There are {n} products on offer")
    get_n_products(n)