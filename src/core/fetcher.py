import httpx
import base64
import asyncio
import math
import re
import heapq
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

from src.config.config_loader import ConfigLoader

config = ConfigLoader()

BASE_URL = "https://api.metrolisboa.pt:8243/estadoServicoML/1.0.1"

LINHA_CORES = {
    "Azul": "#1F77B4",
    "Amarela": "#FFD400",
    "Verde": "#2CA02C",
    "Vermelha": "#D62728",
}
COR_DEFAULT = "#999999"

VELOCIDADE_KMH = 30.0


def distancia_para_segundos(distancia_km: float, velocidade_kmh: float = VELOCIDADE_KMH) -> float:
    """Converte uma distância (km) em tempo de viagem (segundos), a uma velocidade constante."""
    horas = distancia_km / velocidade_kmh
    return horas * 3600


def haversine(lat1, lon1, lat2, lon2):
    """Distância em km entre duas coordenadas geográficas."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def latlon_to_xy(lat: float, lon: float, lat_ref: float, lon_ref: float) -> tuple[float, float]:
    """Converte lat/lon para coordenadas cartesianas (km) num plano local,
    usando (lat_ref, lon_ref) como origem."""
    km_por_grau_lat = 110.574
    km_por_grau_lon = 111.320 * math.cos(math.radians(lat_ref))

    x = (lon - lon_ref) * km_por_grau_lon
    y = (lat - lat_ref) * km_por_grau_lat
    return x, y


def parse_tempo(valor) -> int | None:
    """Converte o tempo de espera para int, ou None se não houver dado ('--')."""
    try:
        return int(valor)
    except (ValueError, TypeError):
        return None


def parse_linhas(valor: str) -> list[str]:
    """Converte '[Verde, Vermelha]' em ['Verde', 'Vermelha']."""
    return [nome.strip() for nome in re.findall(r"[A-Za-zÀ-ú]+", valor)]


class GraphFetcher:
    def __init__(self):
        self.stations = {}
        self.destinos = {}
        self.tempos_espera = []

    async def run(self):
        token = await self._get_access_token()
        headers = {"accept": "application/json", "Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            estacoes, destinos, tempos = await asyncio.gather(
                self._get(client, "/infoEstacao/todos", headers),
                self._get(client, "/infoDestinos/todos", headers),
                self._get(client, "/tempoEspera/Estacao/todos", headers),
            )

        self.stations = {
            e["stop_id"]: {
                "nome": e["stop_name"],
                "lat": float(e["stop_lat"]),
                "lon": float(e["stop_lon"]),
                "linhas": parse_linhas(e["linha"]),
            }
            for e in estacoes["resposta"]
        }

        self.destinos = {
            d["id_destino"]: d["nome_destino"]
            for d in destinos["resposta"]
        }

        self.tempos_espera = tempos["resposta"]

    async def _get_access_token(self) -> str:
        consumer_key = config.get("CONSUMER_KEY")
        consumer_secret = config.get("CONSUMER_SECRET")
        token_url = config.get("METRO")["METRO_URL"]

        credentials = f"{consumer_key}:{consumer_secret}"
        basic_auth = base64.b64encode(credentials.encode()).decode()

        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            response = await client.post(
                token_url,
                headers={
                    "Authorization": f"Basic {basic_auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )

        response.raise_for_status()
        return response.json()["access_token"]

    async def _get(self, client, path, headers):
        r = await client.get(BASE_URL + path, headers=headers)
        r.raise_for_status()
        return r.json()
    
    