from datetime import datetime

class Pattern:
    include: str
    exclude: [str]

    def __init__(self, include, exclude):
        self.include = include
        self.exclude = exclude

    def validProductName(self, name: str):
        name_ = name.lower()

        valid = self.include.lower() in name_

        for exclude in self.exclude:
            if exclude.lower() in name_:
                valid = False

        return valid

class Price:
    price: int
    shippingCosts: int
    seller: str

    def __init__(self, price, shippingCosts, seller):
        self.price = price
        self.shippingCosts = shippingCosts
        self.seller = seller

    def __str__(self):
        return str(self.__dict__)

class Product:
    id: str = ""
    name: str = ""
    link: str = ""
    model: str = ""
    valoration: int = 0
    valorations: int = 0
    prices: [Price] = []
    date: datetime = datetime(1970,1,1)

    def __init__(self, id, name, link, model):
        self.id = id
        self.name = name
        self.link = link
        self.model = model

    # returns the csv header
    def getCSVHeader(self) -> str:
        return "id,name,link,model,valoration,valorations,price,shippingCosts,seller,date"

    # returns the csv corresponding to the product
    def toCSV(self) -> str:
        ret = ""
        for p in self.prices:
            ret += self.id + "#_#" + self.name + "#_#" + self.link + "#_#" + self.model + "#_#" + \
                   str(self.valoration) + "#_#" + str(self.valorations) + "#_#" + str(p.price) + "#_#" + str(p.shippingCosts) + "#_#" + \
                   str(p.seller) + "#_#" + self.date.strftime("%d/%m/%Y %H:%M:%S") + "\n"

        # removing possible commas in the product name or whatever
        ret = ret.replace(",", " -")
        ret = ret.replace("#_#", ",")
        return ret[:-1]

    def __str__(self):
        prices = "["
        for p in self.prices:
            prices += str(p) + ", "

        prices += "]"

        return str(self.__dict__)[:-1] + ", prices: " + prices + "}"