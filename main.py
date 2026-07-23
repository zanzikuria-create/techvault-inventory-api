from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from sqlmodel import SQLModel, Session, select

from typing import List, Optional
from datetime import datetime
import logging

from database.session import engine, get_session

from models.product import (
    Product,
    ProductCreate,
    ProductUpdate,
    Category,
    CategoryCreate,
    Supplier,
    SupplierCreate,
    StockAdjustment,
)

# ==========================
# Create Database Tables
# ==========================
SQLModel.metadata.create_all(engine)

# ==========================
# FastAPI App
# ==========================
app = FastAPI(
    title="TechVault Inventory API",
    version="1.0.0",
    description="A FastAPI inventory management system for TechVault, a Nairobi-based electronics retailer specializing in computer components and gadgets."
)
# ==========================
# Logging
# ==========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================
# GLOBAL EXCEPTION HANDLERS
# ==========================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):

    logger.warning(f"HTTP Exception: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "message": exc.detail,
            "errors": [],
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    errors = []

    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "status_code": 422,
            "message": "Validation error",
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):

    logger.error(f"Integrity Error: {exc}")

    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "status_code": 409,
            "message": "Duplicate SKU or database constraint violation",
            "errors": [],
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):

    logger.error(f"Unhandled Exception: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "status_code": 500,
            "message": "An internal server error occurred",
            "errors": [],
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )

# ==========================
# Root Endpoint
# ==========================

@app.get("/")
def root():
    return {"message": "Welcome to the Product Catalog API"}

# ==========================
# Category Endpoints
# ==========================

@app.post("/categories", response_model=Category, status_code=201)
def create_category(
    category: CategoryCreate,
    session: Session = Depends(get_session)
):

    existing = session.exec(
        select(Category).where(Category.name == category.name)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Category already exists"
        )

    db_category = Category(**category.model_dump())

    session.add(db_category)
    session.commit()
    session.refresh(db_category)

    return db_category


@app.get("/categories", response_model=List[Category])
def list_categories(
    session: Session = Depends(get_session)
):

    return session.exec(select(Category)).all()

# ==========================
# Supplier Endpoints
# ==========================

@app.post("/suppliers", response_model=Supplier, status_code=201)
def create_supplier(
    supplier: SupplierCreate,
    session: Session = Depends(get_session)
):

    db_supplier = Supplier(**supplier.model_dump())

    session.add(db_supplier)
    session.commit()
    session.refresh(db_supplier)

    return db_supplier


@app.get("/suppliers", response_model=List[Supplier])
def list_suppliers(
    session: Session = Depends(get_session)
):

    return session.exec(select(Supplier)).all()

# ==========================
# Product Endpoints
# ==========================

@app.post("/products", response_model=Product, status_code=201)
def create_product(
    product: ProductCreate,
    session: Session = Depends(get_session)
):

    db_product = Product(**product.model_dump())

    session.add(db_product)
    session.commit()
    session.refresh(db_product)

    return db_product


@app.get("/products", response_model=List[Product])
def list_products(
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session)
):

    return session.exec(
        select(Product).offset(skip).limit(limit)
    ).all()


@app.get("/products/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    session: Session = Depends(get_session)
):

    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


@app.patch("/products/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    session: Session = Depends(get_session)
):

    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    updates = product_update.model_dump(exclude_unset=True)

    for key, value in updates.items():
        setattr(product, key, value)

    product.updated_at = datetime.utcnow()

    session.add(product)
    session.commit()
    session.refresh(product)

    return product


@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    session: Session = Depends(get_session)
):

    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    session.delete(product)
    session.commit()

    return {
        "message": "Product deleted successfully"
    }

@app.patch("/products/bulk-update")
def bulk_update_price(
    category: str,
    discount_percent: float,
    session: Session = Depends(get_session)
):

    if discount_percent <= 0 or discount_percent >= 100:
        raise HTTPException(
            status_code=400,
            detail="Discount must be between 0 and 100"
        )

    products = session.exec(
        select(Product).where(Product.category == category)
    ).all()

    if not products:
        raise HTTPException(
            status_code=404,
            detail="No products found in this category"
        )

    updated = []

    for product in products:

        new_price = product.price * (1 - discount_percent / 100)

        if new_price < 100:
            continue

        product.price = round(new_price, 2)
        product.updated_at = datetime.utcnow()

        session.add(product)

        updated.append({
            "product_id": product.id,
            "new_price": product.price
        })

    session.commit()

    logger.info(
        f"Applied {discount_percent}% discount to {len(updated)} products."
    )

    return {
        "message": "Bulk update completed",
        "updated_products": updated
    }
@app.patch("/products/adjust-stock")
def adjust_stock(
    adjustments: List[StockAdjustment],
    session: Session = Depends(get_session)
):

    updated = []
    failed = []

    for adjustment in adjustments:

        # Check if product exists
        product = session.get(Product, adjustment.product_id)

        if not product:
            failed.append({
                "product_id": adjustment.product_id,
                "reason": "Product not found"
            })
            continue

        # Calculate new stock
        new_stock = product.stock + adjustment.quantity_to_add

        # Validate maximum stock
        if new_stock > 5000:
            failed.append({
                "product_id": adjustment.product_id,
                "reason": "Stock cannot exceed 5000 units"
            })
            continue

        # Update stock
        product.stock = new_stock
        product.updated_at = datetime.utcnow()

        session.add(product)

        updated.append({
            "product_id": product.id,
            "new_stock": product.stock
        })

    session.commit()

    logger.info(f"Stock adjusted for {len(updated)} products.")

    return {
        "message": "Stock adjustment completed.",
        "successful_updates": updated,
        "failed_updates": failed
    }