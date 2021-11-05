from getProducts import get_products

import json

import concurrent.futures
from itertools import repeat
import numpy as np

from time import time

import matplotlib.pyplot as plt


def timed_get_products(count):
    '''
    Timed version of the get_products function 
    '''

    start = time()
    products = get_products(1, count)
    end = time()

    if len(products) == count:
        return end - start
    else:
        return 0


def evaluate_best_params():
    ''' 
    Figures out the optimum amout of products to fetch each time 
    '''

    items = np.power(2, np.arange(1, 12))

    # Make it so it repeats each a few times (for averaging)
    _, items = np.meshgrid(range(10), items)
    items = items.flatten()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(timed_get_products, items)

    with open("perfs.json", 'wb') as file:
        json.dump({
            "items": [int(i) for i in items],
            "times": list(results)
        }, file)


def plot_perfs():
    '''
    Plot performances yielded from the evaluate_best_params function 
    '''
    with open("perfs.json", 'r') as file:
        data = json.load(file)

    items = np.array(data['items'])
    times = np.array(data['times'])

    # Filter out 0 (error) values
    items = items[times != 0]
    times = times[times != 0]

    unique_items = np.array(sorted(list(set(items))))
    averages = np.array([np.average(times[items == i]) for i in unique_items])

    plt.scatter(items, times / items, c='k', alpha=0.5, marker="x")
    plt.plot(unique_items, averages / unique_items, c='r')
    plt.xscale('log')
    plt.ylabel("Seconds per product")
    plt.xlabel("Product batch size")
    plt.show()
