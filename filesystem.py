import json

from model import Pattern, Product
from pathlib import Path

# gets a list of patterns from patterns.json. Each pattern have the search query in www.amazon.es/s?k=<query>
def getPatterns() -> [Pattern]:
    patterns = []

    f = open('patterns.json')
    data = json.load(f)
    f.close()

    for p in data:
        assert "include" in p, "invalid include pattern in patterns.json. " + str(p)
        assert "exclude" in p, "invalid exclude pattern in patterns.json. " + str(p)

        patterns.append(Pattern(p["include"], p["exclude"]))

    return patterns

# serialize a list of products into products.csv. If the file doesn't exists it will be created and will be added the csv header.
def serialize(products: [Product]):
    file = Path("products.csv")
    fileExists = file.exists()
    with open('products.csv', 'a+') as f:
        if not fileExists and len(products) > 0:
            f.write(products[0].getCSVHeader())
            f.write("\n")

        for p in products:
            f.write(p.toCSV())
            f.write("\n")

        f.close()
