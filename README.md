# Web Scrapper

this is a free project for web scrapping of any site and collecting information of products.

| Requirements OS       | Version            |
|-----------------------|--------------------|
| Python                | 3.9                |
| Google Chrome browser | \>= 126.0.6478.126 |

# Setup

1. Install Google Chrome (INSTRUCTION TO INSTALL GOOGLE CHROME)
    -
    wget https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_126.0.6478.114-1_amd64.deb
    - apt install ./google-chrome-stable_126.0.6478.114-1_amd64.deb
    - google-chrome --version
2. Install Chromedriver (INSTRUCTION TO INSTALL CHROMEDRIVER)
    - wget https://storage.googleapis.com/chrome-for-testing-public/126.0.6478.114/linux64/chromedriver-linux64.zip
    - unzip chromedriver-linux64.zip
    - mv chromedriver-linux64/chromedriver /usr/local/bin/
    - chmod +x /usr/local/bin/chromedriver
3. Run into your terminal `pip install requirements.txt`

# Project Structure

The folder `src` contains all the [scrapy](https://scrapy.org/) project and some extras like utils and data_structure.
The `utils` has some methods and enums to help us to manipulate the data and `data_structure` contains some classes to
understand
the flow of the application.

# How to use

The scrapy project contains a `spiders` folder where we're going to find the spider class to scan urls and collect
information. At this moment, we have the following spiders:

- product_info_collector_spider

IMPORTANT! each class inside the `spiders` folder has the attribute name. The attribute name is important to know it.
Because we use this name inside the following syntax: `scrapy crawl spider_name -a request='JSON STRING'`


example using the `product_info_collector_spider`:
```
scrapy crawl product_info_collector_spider -a request='{"identifier": {"type": "xpath", "value": "//td[contains(text(), \"VIN\")]/following-sibling::td"}, "msrp": {"type": "xpath", "value": "//p[contains(text(), \"MSRP\")]/following-sibling::p"}, "price": {"type": "xpath", "value": "//p[contains(text(),\"Buy\")]/following-sibling::p"}, "stock_number": {"type": "xpath", "value": "//td[contains(text(), \"Stock Number\")]/following-sibling::td"}, "year": {"type": "xpath", "value": "//a[contains(@href, \"yr=\")]/span[@itemprop=\"name\"]"}, "list_product_url": ["PRODUCT_URL_TO_SCAN"], "webhook_domain": "http://127.0.0.1:8000"}'
```
