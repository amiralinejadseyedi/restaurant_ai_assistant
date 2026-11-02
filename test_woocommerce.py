import requests
from app.woocommerce import get_products

try:
    products = get_products()
    print("Number of products:", len(products))

    for product in products[:10]:
        print("\nProduct:", product["name"])
        print("Description:", product["description"])
        print("Short description:", product["short_description"])
except requests.exceptions.HTTPError as error:
    print("HTTP Status:", error.response.status_code)
    print("Server response:")
    print(error.response.text[:1500])









