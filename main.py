import time

from selenium.common.exceptions import TimeoutException
from filesystem import serialize
from webScrapper import getProducts, fillProductInfo
from model import Product

products: [Product] = getProducts()

for p in products:
    try:
        try:
            fillProductInfo(p)
        except TimeoutException:
            print("Timeout in product " + p.name + ", waiting 20 seconds")
            time.sleep(20)
            try:
                fillProductInfo(p)
            except TimeoutException:
                print("Second timeout in product " + p.name + ", waiting 40 seconds")
                time.sleep(40)
                try:
                    fillProductInfo(p)
                except TimeoutException:
                    print("Third timeout in product " + p.name + ", skipping")
                    print(p.link)
    except Exception as e:
        print("ERROR: " + str(e))
        print(p.link)

serialize(products)