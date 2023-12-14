# database.py
from typing import Dict

from models import User, Product, Order

users_db: Dict[str, User] = {}
products_db: Dict[int, Product] = {}
cart_db: Dict[str, Dict[int, int]] = {}  # {username: {product_id: quantity}}
orders_db: Dict[int, Order] = {}  # {order_id: Order}

def save_user(user: User):
    users_db[user.username] = user

def save_product(product: Product):
    products_db[product.id] = product

def save_cart(username: str, cart: Dict[int, int]):
    cart_db[username] = cart

def save_order(order: Order):
    order_id = len(orders_db) + 1
    orders_db[order_id] = order
