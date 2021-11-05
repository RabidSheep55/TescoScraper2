# Tesco Scraper V2
--- 

This is a new and updated version (hopefully faster too) of the first [Tesco Scraper](https://github.com/RabidSheep55/Tesco-Scraper). It aims to give a better idea of the best deals available on the [Tesco](https://www.tesco.com/groceries/en-GB/promotions/all) grocery website.

## Notes
Product data is actually in the html of the requested page, in the `data-redux-state` (and `data-props`) field (in the `<body />`), as pure HTML encoded json. *Note*: It's better to use the `data-props` field as it is smaller.

Asking for larger and larger amounts of products from the endpoints significantly increases load time. Find the most efficient request (plot a `n` vs `s/product` plot)

Apparently, the `orjson` library is faster than the default `json`.

Content is in:
```python
["resources", "promotionsIdOrType", "data", "results", "productItems"]
```

### Script outline
- First fetch retrieves the number of products 
- Async fetch and parse all the data
	- Async function does both (for memory saving)
	- Use `concurrent.futures` package for parallel execution
- Push to MongoDB (for better query)	