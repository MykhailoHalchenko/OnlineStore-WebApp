# main.py
import logging
from fastapi import FastAPI, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from database import save_user, save_product, save_cart, save_order, users_db, products_db, cart_db
from models import User, Product, Token, CartItem, OrderDetails, Order

app = FastAPI()
templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_user(db, username: str, password: str):
    user = db.get(username)
    if user and user.password == password:
        return user

# Function to verify the token
def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = verify_token_from_database(token)
    if user is None:
        raise credentials_exception

    return user

def verify_token_from_database(token: str):
    user = users_db.get(token)
    return user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = verify_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = form_data.username + "_token"
    users_db[token] = user

    return {"access_token": token, "token_type": "bearer"}

@app.get("/login", response_class=HTMLResponse)
async def login(request: HTMLResponse):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register(request: HTMLResponse):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
async def register(username: str = Form(...), password: str = Form(...)):
    if username in users_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    user = User(username=username, password=password)
    save_user(user)
    return {"message": "User registered successfully"}

@app.get("/", response_class=HTMLResponse, dependencies=[Depends(verify_token)])
async def read_root(current_user: User = Depends(verify_token)):
    products = list(products_db.values())
    return templates.TemplateResponse("index.html", {"request": current_user.username, "products": products})

@app.post("/add_to_cart/{product_id}", dependencies=[Depends(verify_token)])
async def add_to_cart(product_id: int, quantity: int = 1, current_user: User = Depends(verify_token)):
    user_cart = cart_db.get(current_user.username, {})
    user_cart[product_id] = user_cart.get(product_id, 0) + quantity
    save_cart(current_user.username, user_cart)
    return {"message": "Product added to cart successfully"}

@app.get("/cart", response_class=HTMLResponse, dependencies=[Depends(verify_token)])
async def view_cart(current_user: User = Depends(verify_token)):
    user_cart = cart_db.get(current_user.username, {})
    cart_items = []
    total_price = 0
    for product_id, quantity in user_cart.items():
        product = products_db.get(product_id)
        if product:
            item_total = quantity * product.price
            total_price += item_total
            cart_items.append({"product": product, "quantity": quantity, "item_total": item_total})

    return templates.TemplateResponse("cart.html", {"request": current_user.username, "cart_items": cart_items, "total_price": total_price})

@app.post("/checkout", dependencies=[Depends(verify_token)])
async def checkout(address: str, payment_mode: str, current_user: User = Depends(verify_token)):
    user_cart = cart_db.get(current_user.username, {})
    if not user_cart:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty. Add products before checking out.")

    total_price = 0
    order_details = {}

    for product_id, quantity in user_cart.items():
        product = products_db.get(product_id)
        if product:
            item_total = quantity * product.price
            total_price += item_total
            order_details[product_id] = {"product": product, "quantity": quantity, "item_total": item_total}

    order = Order(user=User(username=current_user.username), order_details=order_details, total_price=total_price, address=address, payment_mode=payment_mode)
    save_order(order)

    cart_db[current_user.username] = {}  # Clear the user's cart after checkout

    # Log the order saved to the database
    logger.info(f"Order saved to database: {order}")

    # Return a confirmation message
    return {"message": "Order placed successfully", "order_details": order_details, "total_price": total_price}

# Run the app if the file is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
