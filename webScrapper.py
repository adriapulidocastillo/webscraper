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

userAgents = [  r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36", # windows browser user agent
                r"Mozilla/5.0 (Linux; Android 8.0.0; SM-G960F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36", # Samsung Galaxy S9 user agent
                r"Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1", #Apple iPhone X user agent
                r"Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/69.0.3497.105 Mobile/15E148 Safari/605.1", # Apple iPhone XS (Chrome) user agent
                r"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1", # Linux-based PC using a Firefox browser user agent
                r"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9" # Mac OS X-based computer using a Safari browser user agent
                r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246" # Windows 10-based PC using Edge browser user agent
             ]
userAgentIndex = 0

# function to retrieve the driver. It uses a global driver variable so it will only be created one,
# the rest of time will return the static variable, similar to a singleton pattern.
def _getDriver() -> webdriver:
    global driver
    global userAgentIndex

    if driver is None:
        print("creating driver")
        userAgent = userAgents[userAgentIndex]
        options = Options()
        options.headless = True
        options.add_argument("--window-size=1920,1200")
        options.add_argument(f'user-agent={userAgent}')
        driver = webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
    return driver

# change the userAgent that will be used to build up the driver
def changeUserAgent():
    global userAgentIndex
    global driver

    if driver is not None:
        userAgentIndex += 1
        if userAgentIndex >= len(userAgents):
            userAgentIndex = 0
        driver.quit()
        driver = None

# get a list of products from www.amazon.es/s?k=<product name> using the patterns in patterns.json
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

# fill the product with valorations info
def _fillProductValorationInfo(product: Product, driver):
    WebDriverWait(driver, 10, poll_frequency=2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span#productTitle")))

    try:
        product.valoration = float(driver.find_element_by_css_selector("span#acrPopover").get_attribute("title").split(" ")[0].replace(",", "."))

        product.valorations = int(
            driver.find_element_by_css_selector("span#acrCustomerReviewText").text.split(" ")[0].replace(",", "."))
    except:
        # the product may not have valorations
        product.valoration = 0
        product.valorations = 0

# fill the product with the pinned offer.
def _fillProductPinnedOfferInfo(product: Product, driver):
    # open price modal
    js = """
       links = document.querySelectorAll('[data-action="show-all-offers-display"] a');
       if(links.length == 0)
       {
            throw "No offers";
       }
       // no all elements make appear the pop up
       links.forEach( e => {try { e.click() } catch(e) {} })
       """
    try:
        driver.execute_script(js)
    except JavascriptException:
        # if the product have no stock it won't have offers link, so the links array will be empty
        raise Exception("No offers")

    WebDriverWait(driver, 10, poll_frequency=2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div#aod-pinned-offer")))

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
        try:
            shippingCostText = driver.find_element_by_css_selector(
                "div#aod-pinned-offer div#pinned-de-id div#pinned-offer-top-id div#mir-layout-DELIVERY_BLOCK span[data-csa-c-delivery-price]")\
                .get_attribute('data-csa-c-delivery-price')
        except:
            shippingCostText = driver.find_element_by_css_selector(
                "div#aod-pinned-offer div#pinned-de-id div#pinned-offer-top-id div#mir-layout-DELIVERY_BLOCK a[target='AmazonHelp']").text

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

# fill the product with the non pinned offers
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

# fill the product with the https://www.amazon.es/<product name>/dp/<product id> page info.
def fillProductInfo(product: Product):
    driver = _getDriver()
    print("Searching " + product.name)
    driver.get(product.link)

    product.date = datetime.now()
    _fillProductValorationInfo(product, driver)
    _fillProductPinnedOfferInfo(product, driver)
    _fillProductOtherOfferInfo(product, driver)