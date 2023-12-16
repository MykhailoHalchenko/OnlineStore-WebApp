from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str

class ProductCreate(BaseModel):
    name: str
    description: str
    price: int
