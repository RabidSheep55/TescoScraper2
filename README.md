# Tesco Scraper V2
--- 

This is a new and updated version (hopefully faster too) of the first [Tesco Scraper](https://github.com/RabidSheep55/Tesco-Scraper). It aims to give a better idea of the best deals available on the [Tesco](https://www.tesco.com/groceries/en-GB/promotions/all) grocery website.

## App name ideas
 - Bestco
 - 


## TODO 
 - [x] Fix getProducts (fails after 6-7 concurrent executions, probably due to rate limiting)
   - Yeah it was because the splitting of pages was totally wrong
 - [x] Write a robust deal text parser
   - Fetch all deal-texts and work through them one by one until all are recognised 
   - Use flags like `multiproduct`, `buy1getn`, ...
 - [ ] Figure out a fix for the randomization of items in page
   - Going to a page and refreshing with the same `count` and `page` url params will sometimes yield different results :(


## Index
---
### `scripts`
#### `getProducts.py` 
Contains utilities that scrape for product informations on the alloffers promitions page. Utilises `concurrent.futures` for parallel execution. 

#### `optimize.py` 
Contains utilities which are used to tune the parameters used in `getProducts.py` for improving load times or memory. For example, requesting a batch of 60 products from each page yields the most adequate $\frac{\mathrm{batchsize}}{\mathrm{loadtime}}$

#### `utils.py`
Contains utilities used by other scripts
- `deep_get` performs a recursive fetch for a value in a deeply nested dict 



## Notes
---
Product data is actually in the html of the requested page, in the `data-redux-state` (and `data-props`) field (in the `<body />`), as pure HTML encoded json. *Note*: It's better to use the `data-props` field as it is smaller.

Asking for larger and larger amounts of products from the endpoints significantly increases load time. Find the most efficient request (plot a `n` vs `s/product` plot)

Apparently, the `orjson` library is faster than the default `json`.

Content is in:
```python
["resources", "promotionsIdOrType", "data", "results", "productItems"]
```

### Pipelines 

<details>
<summary>Pipeline for duplicate promotionId documents:</summary>

```python
[
    {
        '$group': {
            '_id': '$promotions.promotionId', 
            'ids': {
                '$push': '$product.title'
            }, 
            'totalIds': {
                '$sum': 1
            }
        }
    }, {
        '$match': {
            'totalIds': {
                '$gt': 1
            }
        }
    }, {
        '$project': {
            '_id': False, 
            'documentsThatHaveDuplicatedValue': '$ids'
        }
    }
]
```

</details>

### Product fetching Script outline
- First fetch retrieves the number of products 
- Async fetch and parse all the data
	- Async function does both (for memory saving)
	- Use `concurrent.futures` package for parallel execution
- Push to MongoDB (for better query)	


## Data exploration
---
Some sorting and filtering tools that would be useful on the dataset of products:

### Sorts:

 - Net reduction in price
 - % reduction in price 
 - Deal expiry date 
 - Sort by calories/pound
 - Sort by units of alcohol/pound

### Filters:
  
 - Deal time range
   - Using promotion `startDate` and `endDate`
   - Including restrictions (`product.restrictions)
 - Deal type 
   - Multiproduct deal (deal applies if multiple products are purchased from one category)
   - Clubcard reduction 
   - Buy multiple of item to get reduction (or free item)
 - Product categories
 - Product brand
 - Does promotion require clubcard (`promotions.attributes` has `CLUBCARD_PRICING`)
 - New products 
   - Using the `isNew` flag
   - Using the promotion `startDate`
 - Filter vegetarian options

### Visualisations

 - N top reduction products for each category (`superDepartmentId` or `departmentId`)
 - Average reduction for each product category (bar chart)
 - 