# dat-fastapi
![alt text](https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png)
Documentation: https://fastapi.tiangolo.com

Source Code: https://github.com/tiangolo/fastapi

'''pip install "fastapi[all]"'''

'''pip install "uvicorn[standard]"'''

'''
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}
'''
Copy that to a file main.py.


'''uvicorn main:app --reload'''

Open your browser at http://127.0.0.1:8000.
