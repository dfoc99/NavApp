from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str


class StationPoint(BaseModel):
    id: str
    name: str
    lat: float
    lon: float


class RouteResponse(BaseModel):
    origin: str
    destination: str
    arrival_time: float
    stations: list[StationPoint]
    
class RouteRequest(BaseModel):
    query: str