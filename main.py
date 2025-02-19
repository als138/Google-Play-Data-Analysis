
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import databases
import sqlalchemy

# تنظیمات اتصال به پایگاه داده PostgreSQL
DATABASE_URL = "postgresql://postgres:1237@localhost:5433/googleplay"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# تعریف جدول categories
categories = sqlalchemy.Table(
    "categories", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(100), nullable=False, unique=True)
)

# تعریف جدول developers
developers = sqlalchemy.Table(
    "developers", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("developer_identifier", sqlalchemy.String(100), nullable=False, unique=True),
    sqlalchemy.Column("website", sqlalchemy.String(255)),
    sqlalchemy.Column("email", sqlalchemy.String(255))
)

# تعریف جدول apps
apps = sqlalchemy.Table(
    "apps", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("app_name", sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column("app_id", sqlalchemy.String(255), nullable=False, unique=True),
    sqlalchemy.Column("category_id", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("rating", sqlalchemy.Numeric(3,2)),
    sqlalchemy.Column("rating_count", sqlalchemy.Integer),
    sqlalchemy.Column("installs", sqlalchemy.Integer),
    sqlalchemy.Column("minimum_installs", sqlalchemy.Integer),
    sqlalchemy.Column("maximum_installs", sqlalchemy.Integer),
    sqlalchemy.Column("free", sqlalchemy.Boolean),
    sqlalchemy.Column("price", sqlalchemy.Numeric(10,2)),
    sqlalchemy.Column("currency", sqlalchemy.String(10)),
    sqlalchemy.Column("size", sqlalchemy.Numeric(10,2)),
    sqlalchemy.Column("minimum_android", sqlalchemy.String(50)),
    sqlalchemy.Column("released", sqlalchemy.Date, nullable=False),
    sqlalchemy.Column("privacy_policy", sqlalchemy.String(255)),
    sqlalchemy.Column("last_updated", sqlalchemy.Date),
    sqlalchemy.Column("content_rating", sqlalchemy.String(50)),
    sqlalchemy.Column("ad_supported", sqlalchemy.Boolean),
    sqlalchemy.Column("in_app_purchases", sqlalchemy.Boolean),
    sqlalchemy.Column("editor_choice", sqlalchemy.Boolean),
    sqlalchemy.Column("developer_id", sqlalchemy.Integer, nullable=False)
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()

# مدل Pydantic برای اعتبارسنجی ورودی‌ها
class AppIn(BaseModel):
    app_name: str
    app_id: str
    category_id: int
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    installs: Optional[int] = None
    minimum_installs: Optional[int] = None
    maximum_installs: Optional[int] = None
    free: Optional[bool] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    size: Optional[float] = None
    minimum_android: Optional[str] = None
    released: str  # فرمت تاریخ: "YYYY-MM-DD"
    privacy_policy: Optional[str] = None
    last_updated: Optional[str] = None
    content_rating: Optional[str] = None
    ad_supported: Optional[bool] = None
    in_app_purchases: Optional[bool] = None
    editor_choice: Optional[bool] = None
    developer_id: int

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Endpoint برای ایجاد یک برنامه جدید
@app.post("/apps/", response_model=dict)
async def create_app(app_in: AppIn):
    query = apps.insert().values(**app_in.dict())
    last_record_id = await database.execute(query)
    return {**app_in.dict(), "id": last_record_id}

# Endpoint برای فیلتر اپلیکیشن‌ها بدون استفاده از کش
@app.get("/apps/filter", response_model=List[dict])
async def filter_apps(
    category: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(0.0),
    free: Optional[bool] = Query(None)
):
    query = apps.select()
    if category and category.lower() != "all":
        # تبدیل نام دسته به شناسه آن
        category_query = sqlalchemy.select([categories.c.id]).where(categories.c.name == category)
        category_id_result = await database.fetch_one(category_query)
        if category_id_result:
            query = query.where(apps.c.category_id == category_id_result["id"])
    if min_rating is not None:
        query = query.where(apps.c.rating >= min_rating)
    if free is not None:
        query = query.where(apps.c.free == free)
    
    rows = await database.fetch_all(query)
    return [dict(row) for row in rows]

# Endpoint برای محاسبه میانگین امتیاز هر دسته بدون کش
@app.get("/apps/average_rating", response_model=List[dict])
async def average_rating():
    query = """
    SELECT c.name as category, AVG(a.rating) as average_rating
    FROM apps a
    JOIN categories c ON a.category_id = c.id
    GROUP BY c.name;
    """
    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]

@app.get("/categories", response_model=List[dict])
async def get_categories():
    query = categories.select()
    rows = await database.fetch_all(query)
    return [{"id": row["id"], "name": row["name"]} for row in rows]
@app.get("/apps/filter", response_model=List[dict])
async def filter_apps(
    category_id: Optional[int] = Query(None),  # استفاده از category_id به جای نام دسته‌بندی
    min_rating: Optional[float] = Query(0.0),
    free: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, le=5000)
):
    offset = (page - 1) * page_size

    query = apps.select().limit(page_size).offset(offset)

    if category_id:
        query = query.where(apps.c.category_id == category_id)

    if min_rating is not None:
        query = query.where(apps.c.rating >= min_rating)

    if free is not None:
        query = query.where(apps.c.free == free)

    rows = await database.fetch_all(query)
    return [dict(row) for row in rows]
@app.get("/")
async def root():
    return {"message": "سلام، خوش آمدید!"}
