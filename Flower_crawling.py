import requests
import json
import math
import csv

# GraphQL query static variables
GRAPHQL_URL = "https://yatesgardening.myshopify.com/api/2020-07/graphql"
GRAPHQL_QUERY_HEADERS = {
    'accept': 'application/json',
    'accept-encoding': 'gzip',
    'accept-language': '*',
    'content-type': 'application/json',
    'x-shopify-storefront-access-token': 'e2d8fc8b39ee0a09023a18fb40c705b1',
    'origin': 'https://www.yates.com.au',
    'referer': 'https://www.yates.com.au/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}
GRAPHQL_QUERY = "query GetProductByCollection ($sortKey:ProductCollectionSortKeys)  { collectionByHandle (handle: \"Flowers\") { id,products (first: 24 sortKey: $sortKey reverse: false $AFTER) { pageInfo { hasNextPage,hasPreviousPage },edges { cursor,node { id,tags,title,productType,images (first: 2) { pageInfo { hasNextPage,hasPreviousPage },edges { cursor,node { originalSrc } } },variants (first: 250) { pageInfo { hasNextPage,hasPreviousPage },edges { cursor,node { id,quantityAvailable } } },priceRange { maxVariantPrice { amount },minVariantPrice { amount } } } } } } }"

# Backend server query static variables
OFFLINE_PRODUCT_IDS_URL = "https://www.yates.com.au/umbraco/Api/Product/GetOfflineProductIds"
PRODUCTS_PAGING_URL = "https://www.yates.com.au/umbraco/Api/Product/GetProductsPaging"
BACKEND_SERVER_QUERY_HEADERS = {
    'accept': 'application/json, application/json, text/plain, */*, image/webp, image/webp',
    'accept-encoding': 'gzip',
    'accept-language': '*',
    'content-type': 'application/json; charset=UTF-8',
    'Host': 'www.yates.com.au',
    'Origin': 'https://www.yates.com.au',
    'Referer': 'https://www.yates.com.au/shop/seeds/flowers/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}
PAGE_SIZE = 24

# CSV file static variables
CSV_HEADERS = ['id', 'name', 'minPrice', 'maxPrice', 'numVariants', 'available', 'barcode', 'seedsPerPack', 'size', 'sku', 'tags']
FILENAME = 'productData.csv'

# Graphql queries
def getProductByCollection(url, lastElementCursor):
    after = ""
    if (len(lastElementCursor) > 0):
        after = 'after: \"' + lastElementCursor + '\"'
    payload = {
        'query': GRAPHQL_QUERY.replace("$AFTER", after),
        'variables': {"sortKey": "MANUAL"}
    }
    req = requests.post(url, headers=GRAPHQL_QUERY_HEADERS, json=payload)
    return json.loads(req.content)

# Backend server queries for offline products IDs
def getOfflineProductsIds(url):
    payload = {
        'criteria': [],
        'paths': ["16172"],
        'showType': "All",
        'sortingRequest': {
            'orderType': "Ascending",
            'sortBy': "Title"
        }
    }
    req = requests.post(url, headers=BACKEND_SERVER_QUERY_HEADERS, json = payload)
    return json.loads(req.content)

# Backend server queries
def getProductsPaging(url, page, pagingItems):
    payload = {
        'criteria': [],
        'paths': ["16172"],
        'showType': "All",
        'sortingRequest': {
            'orderType': "Ascending",
            'sortBy': "MANUAL"
        },
        'paging': {
            'pagingItems': pagingItems
        }
    }
    params = {
        'pageNumber': page,
        'pageSize': PAGE_SIZE
    }
    req = requests.post(url, headers=BACKEND_SERVER_QUERY_HEADERS, params=params, json = payload)
    return json.loads(req.content)

# Extract onlineProduct attributes from Graphql response
def extractAttributesFromGraphqlResponse(onlineProduct):
    return (
        onlineProduct['node']['title'].lower(),
        onlineProduct['node']['title'],
        onlineProduct['node']['priceRange']['maxVariantPrice']['amount'],
        onlineProduct['node']['priceRange']['minVariantPrice']['amount'],
        onlineProduct['node']['tags'],
        onlineProduct['node']['variants']['edges']
    )

# Extract onlineProduct attributes
def extractAttributes(onlineProduct):
    return (
        onlineProduct['title'],
        onlineProduct['quantityAvailable'], 
        onlineProduct['maxPrice'], 
        onlineProduct['minPrice'],
        onlineProduct['tags']
    )

# Generate paging items in request payload
def toPagingItem(cursor, itemType, value): 
    if itemType == 'Online':
        return {
            'cursor': cursor,
            'itemType': itemType,
            'value': value
        }
    elif itemType == 'Offline':
        return {
            'itemType': itemType,
            'value': value
        }

# Convert incomplete row
def handleIncompleteRow(data):
    rows = []
    for onlineProduct in data:
        name, available, maxPrice, minPrice, tags = extractAttributes(onlineProduct)
        numVariants = len(available)
        row = normaliseCols('', name, minPrice, maxPrice, numVariants, available, '', '', '', '', tags)
        rows.append(row)
    return rows

# Normalise Cols
def normaliseCols(id, name, minPrice, maxPrice, numVariants, available, barcode, seedsPerPack, size, sku, tags):
    return [
        id, name, minPrice, maxPrice, numVariants, 
        ','.join(available), 
        ','.join(barcode), 
        ','.join(seedsPerPack), 
        ','.join(size), 
        ','.join(sku), 
        ','.join(tags)
    ]
        
# Handle variant
def handleVariant(variant):
    barcode, seedsPerPack, size, sku = ([], [], [], [])
    barcode.append(variant['barcode']) 
    seedsPerPack.append(variant['seedsPerPack'])
    size.append(variant['size'])
    sku.append(variant['sku'])
    return barcode, seedsPerPack, size, sku

# Process online products
def processOnlineProducts(url, writer):
    lastElementCursor = ""
    hasNextPage = True
    page = 1
    while(hasNextPage):
        productGraphQlInfo = {}
        pagingItemsOnline = []
        products = getProductByCollection(GRAPHQL_URL, lastElementCursor)['data']['collectionByHandle']['products']
        (hasNextPage, lastElementCursor) = (products['pageInfo']['hasNextPage'], products['edges'][-1]['cursor'])
        for p in products['edges']:
            quantityAvailable = []
            name, title, maxPrice, minPrice, tags, variants = extractAttributesFromGraphqlResponse(p)
            pagingItemsOnline.append(toPagingItem(p['cursor'], 'Online', name))
            for v in variants:
                quantityAvailable.append(str(v['node']['quantityAvailable']))
            productGraphQlInfo[name] = {'title': title, 'quantityAvailable': quantityAvailable, 'maxPrice': maxPrice, 'minPrice': minPrice, 'tags': tags}
        onlineProducts = getProductsPaging(PRODUCTS_PAGING_URL, page, pagingItemsOnline)
        results = output(onlineProducts['items'], productGraphQlInfo)
        writer.writerows(results)
        page += 1
        
# Process offline products
def processOfflineProducts(offlineProductIds, writer):
    pagingItemsOffline = []
    for id in offlineProductIds:
        pagingItemsOffline.append(toPagingItem('', 'Offline', id))
    iter = math.ceil(len(offlineProductIds) / PAGE_SIZE)
    for i in range(0, iter):
        offlineProducts = getProductsPaging(PRODUCTS_PAGING_URL, i+1, pagingItemsOffline)
        results = output(offlineProducts['items'], None)
        writer.writerows(results)
        
# Output
def output(pagingItems, productGraphQlInfo):
    isOfflineProductList = productGraphQlInfo is None
    rows = []
    for item in pagingItems:
        row = []
        variants, id, name = (item['variants'], item['id'], item['title'])
        numVariants = len(variants)
        if isOfflineProductList:
            available, maxPrice, minPrice, tags = ('', '', '', '')
        else:
            onlineProduct = productGraphQlInfo.pop(name.lower())
            title, available, maxPrice, minPrice, tags = extractAttributes(onlineProduct)
        for variant in variants:
            barcode, seedsPerPack, size, sku = handleVariant(variant)
        row = normaliseCols(id, name, minPrice, maxPrice, numVariants, available, barcode, seedsPerPack, size, sku, tags)
        rows.append(row)

    # Handle incomplete row
    if not isOfflineProductList and len(productGraphQlInfo) > 0:
        rows = rows + handleIncompleteRow(productGraphQlInfo.values())
    return rows

def main():
    csvfile = open(FILENAME, 'w', encoding='utf-8', newline='')
    writer = csv.writer(csvfile)
    writer.writerow(CSV_HEADERS)
    
    processOnlineProducts(GRAPHQL_URL, writer)
    offlineProductIds = getOfflineProductsIds(OFFLINE_PRODUCT_IDS_URL)
    processOfflineProducts(offlineProductIds, writer)
    
    csvfile.close()
    
if __name__ == "__main__":
    main()