import time

from selenium.common.exceptions import TimeoutException
from filesystem import serialize
from webScrapper import getProducts, fillProductInfo, changeUserAgent
from model import Product

# getting a list of all products
products: [Product] = getProducts()

# filling the products with the amazon info
for p in products:
    try:
        try:
            t0 = time.time()
            fillProductInfo(p)
        except TimeoutException:
            # waiting 4 times the response delay
            response_delay = time.time() - t0
            print("Timeout, waiting " + str(response_delay * 4) + " seconds in product " + p.name)
            time.sleep(response_delay * 4)

            # changing user agent
            changeUserAgent()

            # second attempt
            try:
                fillProductInfo(p)
            except TimeoutException:
                print("Second timeout in product " + p.name + ", skipping")
                print(p.link)
                # changing user agent
                changeUserAgent()

    except Exception as e:
        print("ERROR: " + str(e))
        print(p.link)

# serializing the new products into the products.csv
serialize(products)