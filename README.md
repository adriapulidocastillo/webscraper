# Amazon Webscraper
Amazon price tracking webscraper

# Requeriments

to install python requirements execute:
```` 
pip install -r requirements.txt
```` 

Install a chrome driver, the one who supports your browser version.

The chrome driver can be download from: https://chromedriver.chromium.org/downloads


Then change the path of the chromedriver application in webScrapper.py DRIVER_PATH variable:

```` 
DRIVER_PATH = r"C:\Users\pulidoa.AUTH\Documents\chromedriver.exe"
````

# Execute Scraper

When all the requirements are satisfied execute the main.py script

```` 
python main.py
````  

# Files

#### Patterns.json

In patterns.json are stored the patterns that will be used for doing queris in amazon.es.

```` 
[
  {
    "include": "rtx 3060",
    "exclude": ["rtx 3060 ti", "pc gaming"]
  },
  {
    "include": "rtx 3060 ti",
    "exclude": ["pc gaming"]
  }
]
````

In the previous patterns.json are defined 2 patterns, the first will find the rtx 3060 products in amazon, 
excluding the full computers and the rtx 3060 ti video cards. With the second pattern, the scraper will find the 
rtx 3060 ti products, also exluding the full computers.

#### products.csv

In the products.csv will be stored the results of the scrapping. You can find more information of it in:

https://zenodo.org/record/5617682