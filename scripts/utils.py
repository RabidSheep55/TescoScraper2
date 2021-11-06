from dotenv import load_dotenv
import os
from pymongo import MongoClient


def deep_get(data, params):
    '''
    Recursive function fetches a deeply nested param in a dict
    '''

    # If the value we are looking for is in this last dict, return it
    if len(params) == 1:
        return data.get(params[0])

    key = params.pop(0)
    new_data = data.get(key)

    # If the dict value at that key existed, keep nesting
    if isinstance(new_data, dict):
        return deep_get(new_data, params)

    else:
        return None


def init_mongo_client():
    '''
    Initialise MongoDB client (this is reused multiple times, might as well separate it)
    '''
    # Init DB
    load_dotenv("../.env")
    CONNECTION_STRING = f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_SERVER')}/"
    client = MongoClient(CONNECTION_STRING, connect=False)

    return client
