import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv(override=True)

WOOCOMMERCE_URL = os.getenv("WOOCOMMERCE_URL")
CONSUMER_KEY = os.getenv("WOOCOMMERCE_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("WOOCOMMERCE_CONSUMER_SECRET")


def get_products():
    if not WOOCOMMERCE_URL:
        raise ValueError("WOOCOMMERCE_URL is missing")

    base = WOOCOMMERCE_URL.strip().rstrip("/")
    products = []
    page = 1

    while True:
        response = requests.get(
                f"{base}/",
            params={"rest_route": "/wc/store/v1/products", "per_page": 100, "page": page},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Accept": "application/json",
            },
            timeout=20,
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    return products


def get_menu_products():
    raw_products = get_products()

    menu = []

    for product in raw_products:
        prices = product.get("prices") or {}

        description = product.get("description") or ""

        description = BeautifulSoup(
            description, "html.parser"
        ).get_text(" ", strip=True)

        item = {
            "id": product.get("id"),
            "name": product.get("name"),
            "price": int(prices.get("price") or 0),
            "currency": prices.get("currency_symbol"),
            "category": ", ".join(
            category.get("name", "")
                 for category in product.get("categories", [])
                ),
            "is_in_stock": product.get("is_in_stock"),
            "description": description,
            "permalink": product.get("permalink"),
        }

        menu.append(item)

    return menu





