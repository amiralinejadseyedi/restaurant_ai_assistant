from app.database import SessionLocal
from app.models import Product
from app.woocommerce import get_menu_products


def sync_products():
    products = get_menu_products()

    with SessionLocal() as session:
        for item in products:
            product = session.get(Product, item["id"])

            if product is None:
                product = Product(id=item["id"])
                session.add(product)

            product.name = item["name"]
            product.price = item["price"]
            product.currency = item["currency"] or "تومان"
            product.category = item["category"]
            product.description = item["description"]
            product.is_in_stock = item["is_in_stock"]
            product.permalink = item["permalink"]

        session.commit()

    print(f"Successfully synced {len(products)} products.")


if __name__ == "__main__":
    sync_products()




