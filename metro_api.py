import os
import time
import json
import httpx
import base64
import requests
import urllib.request
from fastapi import FastAPI

from src.config_loader import ConfigLoader
url = "https://api.metrolisboa.pt:8243/estadoServicoML/1.0.1/infoEstacao/todos"

config = ConfigLoader()
app = FastAPI()

_token = None
_token_expires = 0

def get_access_token():
    global _token, _token_expires

    if _token and time.time() < _token_expires:
        return _token

    consumer_key = config.get("CONSUMER_KEY")
    consumer_secret = config.get("CONSUMER_SECRET")
    token_url = config.get('METRO')['METRO_URL']
    auth = base64.b64encode(
        f"{consumer_key}:{consumer_secret}".encode()
    ).decode()

    response = requests.post(
        token_url,
        data={"grant_type": "client_credentials"},
        headers={
            "Authorization: Bearer {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        verify=False,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    _token = data["access_token"]
    _token_expires = (
        time.time()
        + int(data.get("expires_in", 3600))
        - 60
    )

    return _token


@app.get("/stations")
async def read_stations():
    async with httpx.AsyncClient() as client:
        token = get_access_token()

        response = await client.get(
            config.get("METRO")["METRO_URL"],
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )

        response.raise_for_status()
        return response.json()

@app.get("/")
def read_root():
    return {"Wrapper da API https://api.metrolisboa.pt/store"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "metro_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )