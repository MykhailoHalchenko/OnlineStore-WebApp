# app/schemas.py

from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    full_name: str

class UserCreate(UserBase):
    password: str

class ProductBase(BaseModel):
    name: str
    description: str
    price: float

class ProductCreate(ProductBase):
    pass
