# main.py
# main.py
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import get_db
from models import User, Order

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Dummy data for products
products = [
    {"id": 1, "name": "Product 1", "price": 19.99, "description": "Lorem ipsum..."},
    {"id": 2, "name": "Product 2", "price": 29.99, "description": "Lorem ipsum..."},
    # Add more products as needed
]

# Dummy data for users and orders
users = {}
orders = {}

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Check if the username is already taken
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hash the password before storing it
    hashed_password = "hash_function_of_your_choice"  # Use a proper password hashing library
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()

    return RedirectResponse(url="/")

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.hashed_password != "hash_function_of_your_choice":  # Check the password using the proper library
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return RedirectResponse(url="/")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "products": products})

@app.get("/product/{product_id}", response_class=HTMLResponse)
async def product_details(request: Request, product_id: int):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return templates.TemplateResponse("product.html", {"request": request, "product": product})

# ... (other route handlers)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
