# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from database import SessionLocal, engine
from models import User, Product, Cart, Order, OrderDetail
from schemas import UserCreate, ProductCreate
from typing import List
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.mount("/static", StaticFiles(directory="static"), name="static")
# Password hashing
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return password_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return password_context.verify(plain_password, hashed_password)

# OAuth2 for token-based authentication
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get the current user ID from the token
def get_user_id(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user.id

# Registration route
@app.post("/register/")
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the username is already taken
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hash the password before saving it in the database
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, password=hashed_password, full_name=user.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User registered successfully"}

# Login route
@app.post("/login/")
async def login_user(username: str, password: str, db: Session = Depends(get_db)):
    # Logic for user login
    # Verify the username and password against the database
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password):
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Main page route
@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("main_page.html", {"request": request})

# Product listing route
@app.get("/products/", response_class=HTMLResponse)
async def list_products(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return templates.TemplateResponse("product.html", {"request": request, "products": products})

# Add to cart route
@app.post("/add-to-cart/{product_id}")
async def add_to_cart(product_id: int, quantity: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    # Logic to add a product to the user's cart
    # Check if the product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if the product is already in the user's cart
    existing_cart_item = db.query(Cart).filter(Cart.user_id == user_id, Cart.product_id == product_id).first()
    if existing_cart_item:
        existing_cart_item.quantity += quantity
    else:
        new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.add(new_cart_item)

    db.commit()
    return {"message": "Product added to the cart successfully"}

# View cart route
@app.get("/cart/", response_class=HTMLResponse)
async def view_cart(request: Request, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    # Logic to retrieve and display the user's cart items
    cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()
    return templates.TemplateResponse("cart.html", {"request": request, "cart_items": cart_items})

# Checkout route
@app.post("/checkout/")
async def checkout(address: str, payment_method: str, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    # Logic for order placement
    cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()

    # Create an order and associate it with the user
    new_order = Order(user_id=user_id, address=address, payment_method=payment_method)
    db.add(new_order)
    db.commit()

    # Move cart items to the order details
    for cart_item in cart_items:
        order_detail = OrderDetail(order_id=new_order.id, product_id=cart_item.product_id, quantity=cart_item.quantity)
        db.add(order_detail)

    # Clear the user's cart
    db.query(Cart).filter(Cart.user_id == user_id).delete()

    db.commit()
    return {"message": "Order placed successfully"}
