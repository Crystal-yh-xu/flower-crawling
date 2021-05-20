# flower-crawling

## Table of contents
* [General Info](#general-info)
* [Task](#task)
* [Step 1 Inspect](#step-1-inspect)
* [Step 2 Observe query data process](#step-2-observe-query-data-process)
* [Step 3 Build scraper](#step-3-build-scraper)
* [Step 4 Extract and integrate data](#step-4-extract-and-integrate-data)
* [Note](#note)

## General Info
* There are two kind doc which have the same code (.ipynb and .py). Please view the Flower_crawling.py doc if you are facing the problem of viewing the Flower_crawling.ipynb doc.
* productData.csv is the product data output

## Task
Use Python to scrape all product data(name, price, variant, availability) under this category: https://www.yates.com.au/shop/seeds/flowers/
    
## Step 1 Inspect
* As the website is a dynamic website (asynchronously loading), the product info will not be showed in the HTML code.
* The website is built by using Javascript, React, deployed on the Microsoft Azure cloud, tracked and managed by Google Analytics and Google Tag Manager.
    
## Step 2 Observe query data process
* Select all, scroll down, load all data of product, and observe the query process.
* The Graphql shows there are 79 online products.
* The Backend server shows there are 21 offline products (Offline products IDs list).
* Query 24 online products data once from both the Graphql and the Backend server.
* After all online products data is queried, it will query offline products data from only the Backend server.

## Step 3 Build scraper
* Using Python to build scraper to simulate a web browser to send requests to the Graphql and the Bankend server
* Graphql query includes Graphql URL, Graphql query Headers and Payload (update last cursor every time). It will response online products data by Json format.
* Offline product IDs list query includes Offline products IDs list URL, Backend server query Headers and Payload. It will response a Offline product IDs list.
* Backend server query includes Product paging URL, Backend server query Headers and Payload (update paging items every time). It will response both online and offline products data by Json format.

## Step 4 Extract and integrate data
* Extract useful data in the Graphql: Title, maxPrice, minPrice, tags, quantityAvaliable.
* Extract useful data in the Backend Server: Title, id, variants (barcode, seedsPerPack, size, sku).
* Integrate data in both the Graphql and the Backend Server Online products.
* Offline products only have data in the Backend Server.

## Note
* Produc name is case sensitive.
* Missing an online product in the Backend server query.
* Variants may have several list item, which including quantityAvaliable, barcode, seedsPerPack, size and sku.
