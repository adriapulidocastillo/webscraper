import time
from datetime import datetime

from selenium.common.exceptions import JavascriptException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from filesystem import getPatterns
from model import Pattern, Product, Price

DRIVER_PATH = r"C:\Users\pulidoa.AUTH\Documents\chromedriver.exe"

driver: webdriver = None

def _getDriver() -> webdriver:
    # singleton pattern
    global driver

    if driver is None:
        print("creating driver")
        userAgent = r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
        options = Options()
        options.headless = True
        options.add_argument("--window-size=1920,1200")
        options.add_argument(f'user-agent={userAgent}')
        driver = webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
    return driver

def getProducts() -> [Product]:
    products: dict[str, Product] = dict()
    driver = _getDriver()

    searchQuery = "https://www.amazon.es/s?k="

    for pattern in getPatterns():
        driver.get(searchQuery + pattern.include)
        productContainers = driver.find_elements_by_css_selector("div[data-asin]")

        for productContainer in productContainers:
            try:
                if productContainer.get_attribute("data-asin") != "":
                    productId = productContainer.get_attribute("data-asin")
                    productHref = productContainer.find_element_by_css_selector("div.a-section h2 a").get_attribute("href")
                    productHref = productHref.split("?")[0]
                    productName = productContainer.find_element_by_css_selector("div.a-section h2 span").text

                    if pattern.validProductName(productName) and productId not in products:
                        products[productId] = Product(productId, productName, productHref, pattern.include)
            except:
                pass

    return list(products.values())

def _fillProductValorationInfo(product: Product, driver):
    valoration: WebElement = WebDriverWait(driver, 15, poll_frequency=2).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span#acrPopover")))

    product.valoration = float(valoration.get_attribute("title").split(" ")[0].replace(",", "."))

    product.valorations = int(
        driver.find_element_by_css_selector("span#acrCustomerReviewText").text.split(" ")[0].replace(",", "."))

def _fillProductPinnedOfferInfo(product: Product, driver):
    # open price modal
    js = """
       links = document.querySelectorAll('[data-action="show-all-offers-display"] a');
       // no all elements make appear the pop up
       links.forEach( e => {try { e.click() } catch(e) {} })
       """
    driver.execute_script(js)

    modal: WebElement = WebDriverWait(driver, 15, poll_frequency=2).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "div#aod-pinned-offer")))

    # open show more info div with the seller info
    js = """
          moreInfo = document.getElementById('aod-pinned-offer-show-more-link');
          moreInfo.click()
          """
    try:
        driver.execute_script(js)
    except JavascriptException:
        # if the javascript fails is because there are no stock in the pinned seller of the product.
        return

    price = driver.find_element_by_css_selector(
        "div#aod-pinned-offer div#pinned-de-id div#pinned-offer-top-id span.a-price-whole").text
    decimals = driver.find_element_by_css_selector(
        "div#aod-pinned-offer div#pinned-de-id div#pinned-offer-top-id span.a-price-fraction").text

    # removing thousands separator
    price = price.replace(".", "")
    price = float(price + "." + decimals)

    # the html of the page may change. Trying one way and if it crashes doing in the other way
    try:
        shippingCostText = driver.find_element_by_css_selector(
            "div#aod-pinned-offer div#pinned-de-id div#pinned-offer-top-id div#mir-layout-DELIVERY_BLOCK div#mir-layout-DELIVERY_BLOCK-slot-DELIVERY_MESSAGE")\
            .get_attribute('innerText')
    except:
        shippingCostText = driver.find_element_by_css_selector(
            "div#aod-pinned-offer div#pinned-de-id div#pinned-offer-top-id div#mir-layout-DELIVERY_BLOCK span[data-csa-c-delivery-price]")\
            .get_attribute('data-csa-c-delivery-price')

    # removing thousands separator
    shippingCostText = shippingCostText.replace(".", "")
    shippingCostText = shippingCostText.replace(",", ".")

    # removing non breaking space
    shippingCostText = shippingCostText.replace("\xa0", " ")

    shippingCost = 0
    for s in shippingCostText.split(" "):
        try:
            shippingCost = float(s)
        except ValueError:
            pass

    try:
        seller = driver.find_element_by_css_selector("div#aod-pinned-offer div#aod-offer-soldBy a").text
    except NoSuchElementException:
        # if the seller is amazon there is no a tag <a>
        seller = driver.find_element_by_css_selector("div#aod-pinned-offer div#aod-offer-soldBy span[aria-label]").text

    product.prices.append(Price(price, shippingCost, seller))

def _fillProductOtherOfferInfo(product: Product, driver):
    offerContainers = driver.find_elements_by_css_selector("div#aod-offer-list div#aod-offer")
    for offerContainer in offerContainers:
        price = offerContainer.find_element_by_css_selector("div#aod-offer-price div[id^='aod-price-'] span.a-price-whole").text
        decimals = offerContainer.find_element_by_css_selector("div#aod-offer-price div[id^='aod-price-'] span.a-price-fraction").text

        # removing thousands separator
        price = price.replace(".", "")
        price = float(price + "." + decimals)

        # the html of the page may change. Trying one way and if it crashes doing in the other way
        try:
            shippingCostText = offerContainer.find_element_by_css_selector("div#aod-offer-price span[data-csa-c-delivery-price]") \
                .get_attribute('data-csa-c-delivery-price')
        except:
            try:
                shippingCostText = offerContainer.find_element_by_css_selector(
                    "div#aod-offer-price div#mir-layout-DELIVERY_BLOCK div#mir-layout-DELIVERY_BLOCK-slot-DELIVERY_MESSAGE") \
                    .get_attribute('innerText')
            except:
                shippingCostText = offerContainer.find_element_by_css_selector(
                    "div#aod-offer-price div#aod_ship_charge_row span") \
                    .get_attribute('innerText')

        # removing thousands separator
        shippingCostText = shippingCostText.replace(".", "")
        shippingCostText = shippingCostText.replace(",", ".")
        # removing non breaking space
        shippingCostText = shippingCostText.replace("\xa0", " ")

        shippingCost = 0
        for s in shippingCostText.split(" "):
            try:
                shippingCost = float(s)
            except ValueError:
                pass

        try:
            seller = offerContainer.find_element_by_css_selector("div#aod-offer-soldBy a").text
        except NoSuchElementException:
            # if the seller is amazon there is no a tag <a>
            seller = driver.find_element_by_css_selector("div#aod-offer-soldBy span[aria-label]").text

        product.prices.append(Price(price, shippingCost, seller))

def fillProductInfo(product: Product):
    driver = _getDriver()
    driver.get(product.link)

    print("Searching " + product.name)
    product.date = datetime.now()
    _fillProductValorationInfo(product, driver)
    _fillProductPinnedOfferInfo(product, driver)
    _fillProductOtherOfferInfo(product, driver)