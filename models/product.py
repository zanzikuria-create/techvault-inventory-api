from sqlmodel import SQLModel, Field, Relationship
from pydantic import field_validator
from datetime import datetime
from typing import Optional, List
import re


# ==========================
# CATEGORY
# ==========================
class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(unique=True, index=True)

    description: Optional[str] = None

    products: List["Product"] = Relationship(back_populates="category_rel")


# ==========================
# SUPPLIER
# ==========================
class Supplier(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(unique=True)

    contact_person: str

    email: str = Field(unique=True)

    phone: str

    is_active: bool = True

    products: List["Product"] = Relationship(back_populates="supplier")


# ==========================
# PRODUCT
# ==========================
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(index=True)

    description: str

    brand: str = Field(index=True)

    category: str = Field(index=True)

    price: float = Field(gt=0)

    stock: int = Field(ge=0)

    warranty_months: int = Field(ge=0)

    sku: str = Field(unique=True, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    updated_at: datetime = Field(default_factory=datetime.utcnow)

    category_id: Optional[int] = Field(
        default=None,
        foreign_key="category.id"
    )

    supplier_id: Optional[int] = Field(
        default=None,
        foreign_key="supplier.id"
    )

    category_rel: Optional[Category] = Relationship(back_populates="products")

    supplier: Optional[Supplier] = Relationship(back_populates="products")


# ==========================
# PRODUCT CREATE
# ==========================
class ProductCreate(SQLModel):

    name: str = Field(min_length=2, max_length=100)

    description: str = Field(min_length=10, max_length=500)

    brand: str

    category: str

    price: float = Field(gt=0, le=1000000)

    stock: int = Field(ge=0, le=10000)

    warranty_months: int = Field(ge=0)

    sku: str

    category_id: Optional[int] = None

    supplier_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v[0].isupper():
            raise ValueError("Name must start with a capital letter")

        if re.search(r"[^a-zA-Z0-9\s-]", v):
            raise ValueError("Name cannot contain special characters")

        if len(v.split()) < 1:
            raise ValueError("Name must contain at least one word")

        return v

    @field_validator("brand")
    @classmethod
    def validate_brand(cls, v):

        allowed = [
            "HP",
            "Dell",
            "Lenovo",
            "Apple",
            "Samsung",
            "Intel",
            "AMD",
            "Corsair",
            "Logitech",
            "Other"
        ]

        for brand in allowed:
            if v.lower() == brand.lower():
                return brand

        raise ValueError("Invalid brand")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):

        allowed = [
            "Laptops",
            "Monitors",
            "Storage",
            "Processors",
            "Memory",
            "Keyboards",
            "Mice",
            "Accessories"
        ]

        for category in allowed:
            if v.lower() == category.lower():
                return category

        raise ValueError("Invalid category")

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):

        if round(v, 2) != v:
            raise ValueError("Price must have at most 2 decimal places")

        if v < 100:
            raise ValueError("Minimum price is 100 KSh")

        if v > 500000:
            raise ValueError("Maximum price is 500000 KSh")

        return round(v, 2)

    @field_validator("stock")
    @classmethod
    def validate_stock(cls, v):

        if v < 0:
            raise ValueError("Stock cannot be negative")

        return v

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v):

        pattern = r"^[A-Z]{3,4}-[A-Z]{2,4}-[0-9]{4}$"

        if not re.match(pattern, v):
            raise ValueError("SKU must follow CAT-BRAND-XXXX format")

        allowed_prefixes = [
            "LAP",
            "MON",
            "STO",
            "PRO",
            "MEM",
            "KEY",
            "MOU",
            "ACC"
        ]

        prefix = v.split("-")[0]

        if prefix not in allowed_prefixes:
            raise ValueError("Invalid category abbreviation")

        return v

    @field_validator("warranty_months")
    @classmethod
    def validate_warranty(cls, v):

        if v < 0 or v > 36:
            raise ValueError("Warranty must be between 0 and 36 months")

        return v


# ==========================
# PRODUCT UPDATE
# ==========================
class ProductUpdate(SQLModel):

    name: Optional[str] = None

    description: Optional[str] = None

    brand: Optional[str] = None

    category: Optional[str] = None

    price: Optional[float] = None

    stock: Optional[int] = None

    warranty_months: Optional[int] = None

    sku: Optional[str] = None


# ==========================
# CATEGORY CREATE
# ==========================
class CategoryCreate(SQLModel):

    name: str

    description: Optional[str] = None


# ==========================
# SUPPLIER CREATE
# ==========================
class SupplierCreate(SQLModel):

    name: str

    contact_person: str

    email: str

    phone: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):

        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("Invalid email address")

        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):

        if not re.match(r"^\+?[0-9]{10,15}$", v):
            raise ValueError("Invalid phone number")

        return v


# ==========================
# STOCK ADJUSTMENT
# ==========================
class StockAdjustment(SQLModel):

    product_id: int

    quantity_to_add: int = Field(gt=0)