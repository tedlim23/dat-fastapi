from fastapi import Depends, FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import json
from app import create_price
from models import PriceCreate

app = FastAPI()
motor_client = AsyncIOMotorClient(
    "mongodb://localhost:27017"
)  # Connection to the whole server
database = motor_client["mongo0"]  # Single database instance


def post_price(t, p):  
    price_data.ticker = t
    content = json.loads(price_data.content)
    content.append(int(p))
    price_data.content = json.dumps(content)
    price_db = create_price(price_data, database)
    return content[-1]


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

