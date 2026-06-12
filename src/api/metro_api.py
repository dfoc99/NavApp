import os
import sys
import time
import json
import httpx
import base64
import requests
import subprocess
import urllib.request
from pathlib import Path
from fastapi import FastAPI


from src.config.config_loader import ConfigLoader


config = ConfigLoader()
app = FastAPI()

def get_access_token() -> str:

    consumer_key = config.get("CONSUMER_KEY")
    consumer_secret = config.get("CONSUMER_SECRET")
    token_url = config.get('METRO')['METRO_URL']
    
    credentials = f"{consumer_key}:{consumer_secret}"
    basic_auth = base64.b64encode(credentials.encode()).decode()

    response = requests.post(
        token_url,
        headers={
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials"
        },
        verify=False,
        timeout=30
    )

    response.raise_for_status()
    payload = response.json()
    return payload["access_token"]


@app.get("/infoEstacao/todos")
async def read_infoEstacao_todos():
    async with httpx.AsyncClient() as client:
        
        token = get_access_token()
        response = requests.get(
            "https://api.metrolisboa.pt:8243/estadoServicoML/1.0.1/infoEstacao/todos",
            headers={
                "accept": "application/json",
                "Authorization": f"Bearer {token}"
            },
            verify=False,
            timeout=30
        )

        response.raise_for_status()
        return response.json()


@app.get("/stations")
async def read_stations():
    async with httpx.AsyncClient() as client:
        
        token = get_access_token()
        response = requests.get(
            "https://api.metrolisboa.pt:8243/estadoServicoML/1.0.1/tempoEspera/Estacao/todos",
            headers={
                "accept": "application/json",
                "Authorization": f"Bearer {token}"
            },
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

@app.get("/destinos")
async def read_destinos():
    async with httpx.AsyncClient() as client:
        
        token = get_access_token()
        response = requests.get(
            "https://api.metrolisboa.pt:8243/estadoServicoML/1.0.1/infoDestinos/todos",
            headers={
                "accept": "application/json",
                "Authorization": f"Bearer {token}"
            },
            verify=False,
            timeout=30
        )

        response.raise_for_status()
        return response.json()
    
@app.get("/")
def read_root():
    return {"Wrapper da API https://api.metrolisboa.pt/store"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.metro_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )