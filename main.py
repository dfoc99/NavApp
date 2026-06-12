import time
import threading
import webbrowser
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.core.fetcher import GraphFetcher
from src.core.graph import StationGraph
from src.core.llm import LLMExtractor
from src.schemas.models import QueryRequest

llm = LLMExtractor()


# -------------------------
# Helpers
# -------------------------
def resolve_station_id(name: str, stations: dict) -> str | None:
    for stop_id, data in stations.items():
        if data["nome"].lower() == name.lower():
            return stop_id
    return None

def format_time(seconds: float) -> str:
    total_minutes = int(seconds // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"

def format_route_string(stations: list[dict]) -> str:
    if not stations:
        return ""

    # Build station chain
    station_chain = " -> ".join(s["name"] for s in stations)

    # Try to infer line (if all stations share same first line)
    line_candidates = []

    for s in stations:
        lines = s.get("lines")
        if lines:
            line_candidates.append(lines[0])

    if line_candidates and len(set(line_candidates)) == 1:
        line = line_candidates[0]
    else:
        line = "Mixed Line"

    return f"{station_chain} ({line})"

def serialize_route(graph: StationGraph, path: list[str], arrival_time: float):
    stations = []

    for node_id in path:
        node = graph.G.nodes[node_id]

        stations.append(
            {
                "id": node_id,
                "name": node["nome"],
                "lat": node["lat"],
                "lon": node["lon"],
            }
        )

    return {
        "arrival_time": arrival_time,
        "arrival_time_human": format_time(arrival_time),
        "stations": stations,
    }


# -------------------------
# Lifespan
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    fetcher = GraphFetcher()
    await fetcher.run()

    app.state.fetcher = fetcher
    app.state.stations = fetcher.stations
    app.state.destinations = fetcher.destinos

    def open_browser():
        time.sleep(1.0)  # wait for server to start
        webbrowser.open("http://localhost:8000/")

    threading.Thread(target=open_browser, daemon=True).start()

    yield


# -------------------------
# App
# -------------------------
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Routes
# -------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/stations")
async def stations(request: Request):
    return [
        {
            "id": stop_id,
            "name": data["nome"],
            "lines": data["linhas"],
        }
        for stop_id, data in request.app.state.stations.items()
    ]


# -------------------------
# ROUTE (MAIN ENDPOINT)
# -------------------------
@app.post("/route")
async def route_query(request: Request, body: QueryRequest):
    try:
        origin_name, destination_name = llm.extract_route(
            query=body.query,
            stations=request.app.state.stations,
        )

        origin_id = resolve_station_id(origin_name, request.app.state.stations)
        destination_id = resolve_station_id(destination_name, request.app.state.stations)

        if not origin_id or not destination_id:
            raise ValueError(
                f"Could not resolve stations: {origin_name} -> {destination_name}"
            )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not identify stations: {exc}",
        )

    fetcher = request.app.state.fetcher

    graph = StationGraph(fetcher)
    graph.build()

    result = graph.caminho_mais_rapido(origin_id, destination_id)

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    path, arrival_time = result

    response = serialize_route(graph, path, arrival_time)

    response["origin_id"] = origin_id
    response["destination_id"] = destination_id
    response["origin"] = graph.G.nodes[origin_id]["nome"]
    response["destination"] = graph.G.nodes[destination_id]["nome"]
    response["route_string"] = format_route_string(response["stations"])
    
    return response


# -------------------------
# MAP ROUTE
# -------------------------
@app.get("/map/route")
async def route_map(request: Request, origin_id: str, destination_id: str):
    fetcher = request.app.state.fetcher

    graph = StationGraph(fetcher)
    graph.build()

    result = graph.caminho_mais_rapido(origin_id, destination_id)

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    path, _ = result

    return graph.exportar_para_mapa(caminho=path)

from fastapi.responses import FileResponse
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.get("/")
async def index():
    return FileResponse("frontend/index.html")
# -------------------------
# ENTRY POINT
# -------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )