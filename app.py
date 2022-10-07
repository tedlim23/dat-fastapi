from typing import List, Tuple
import uvicorn
from bson import ObjectId, errors
from fastapi import Depends, FastAPI, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import json

from models import (
    PriceDB,
    PriceCreate,
    PricePartialUpdate,
)

app = FastAPI()
motor_client = AsyncIOMotorClient(
    "mongodb://localhost:27017"
)  # Connection to the whole server
database = motor_client["mongo0"]  # Single database instance


def get_database() -> AsyncIOMotorDatabase:
    return database


async def pagination(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=0),
) -> Tuple[int, int]:
    capped_limit = min(100, limit)
    return (skip, capped_limit)


async def get_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except (errors.InvalidId, TypeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


async def get_or_404(
    id: ObjectId = Depends(get_object_id),
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> PriceDB:
    raw_price = await database["prices"].find_one({"_id": id})

    if raw_price is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return PriceDB(**raw_price)


@app.get("/prices")
async def list_prices(
    pagination: Tuple[int, int] = Depends(pagination),
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> List[PriceDB]:
    skip, limit = pagination
    query = database["prices"].find({}, skip=skip, limit=limit)

    results = [PriceDB(**raw_price) async for raw_price in query]

    return results


@app.get("/prices/{id}", response_model=PriceDB)
async def get_price(price: PriceDB = Depends(get_or_404)) -> PriceDB:
    return price


@app.post("/prices", response_model=PriceDB, status_code=status.HTTP_201_CREATED)
async def create_price(
    price: PriceCreate, database: AsyncIOMotorDatabase = Depends(get_database)
) -> PriceDB:
    price_db = PriceDB(**price.dict())
    await database["prices"].insert_one(price_db.dict(by_alias=True))

    price_db = await get_or_404(price_db.id, database)

    return price_db


@app.patch("/prices/{id}", response_model=PriceDB)
async def update_price(
    price_update: PricePartialUpdate,
    price: PriceDB = Depends(get_or_404),
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> PriceDB:
    await database["prices"].update_one(
        {"_id": price.id}, {"$set": price_update.dict(exclude_unset=True)}
    )

    price_db = await get_or_404(price.id, database)

    return price_db


@app.delete("/prices/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price(
    price: PriceDB = Depends(get_or_404),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    await database["prices"].delete_one({"_id": price.id})

def post_price(t, p):  
    price_data.ticker = t
    content = json.loads(price_data.content)
    content.append(int(p))
    price_data.content = json.dumps(content)
    price_db = create_price(price_data, database)
    return content[-1]


if __name__=="__main__":
    uvicorn.run(app, host = "0.0.0.0", port = 8800)
    print("passed")
    from bybit import BybitApi
    price_data = PriceCreate(ticker="BTC", content="[]")
    with open("./mybit.json", 'r') as f:
        apis = json.load(f)
        f.close()
    k = apis["KEY"]
    sr = k = apis["SECRET"]
    bybit = BybitApi(k, sr)
    cp = bybit.get_current_price()
    done = post_price("BTC", cp)
    print(done)
    
    