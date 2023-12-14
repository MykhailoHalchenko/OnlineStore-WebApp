# models.py
from typing import Dict

from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str

class Product(BaseModel):
    id: int
    name: str
    price: float
    image_url: str

class Token(BaseModel):
    access_token: str
    token_type: str

class CartItem(BaseModel):
    product: Product
    quantity: int
    item_total: float

class OrderDetails(BaseModel):
    product: Product
    quantity: int
    item_total: float

class Order(BaseModel):
    user: User
    order_details: Dict[int, OrderDetails]
    total_price: float
    address: str
    payment_mode: str
