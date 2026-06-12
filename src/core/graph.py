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
from src.core.fetcher import GraphFetcher

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


class StationGraph:
    def __init__(self, fetcher: GraphFetcher):
        self.fetcher = fetcher
        self.G = nx.Graph()

    def build(self) -> nx.Graph:
        # ponto de referência: centro geográfico de todas as estações
        lats = [info["lat"] for info in self.fetcher.stations.values()]
        lons = [info["lon"] for info in self.fetcher.stations.values()]
        lat_ref = sum(lats) / len(lats)
        lon_ref = sum(lons) / len(lons)

        partidas_por_estacao = self._agrupar_tempos_por_estacao()

        for stop_id, info in self.fetcher.stations.items():
            x, y = latlon_to_xy(info["lat"], info["lon"], lat_ref, lon_ref)
            self.G.add_node(
                stop_id,
                nome=info["nome"],
                lat=info["lat"],
                lon=info["lon"],
                x=x,
                y=y,
                linhas=info["linhas"],
                partidas=partidas_por_estacao.get(stop_id, {}),
            )

        # arestas: reconstruir cada linha como um ou mais caminhos
        for linha in self._todas_as_linhas():
            arestas = self._reconstruir_linha(linha)

            for caminho in self._caminhos_da_linha(arestas):
                destino_inicio = self.fetcher.stations[caminho[0]]["nome"]
                destino_fim = self.fetcher.stations[caminho[-1]]["nome"]

                for i in range(len(caminho) - 1):
                    u, v = caminho[i], caminho[i + 1]
                    dist = self._distancia(u, v)
                    tempo_seg = distancia_para_segundos(dist)

                    self.G.add_edge(
                        u,
                        v,
                        weight=tempo_seg,
                        distancia_km=dist,
                        tempo_seg=tempo_seg,
                        linha=linha,
                        cor=LINHA_CORES.get(linha, COR_DEFAULT),
                        # para cada nó, a direção (terminal) para onde se vai
                        # ao atravessar esta aresta a partir desse nó
                        direcao={u: destino_fim, v: destino_inicio},
                    )

        return self.G

    def _todas_as_linhas(self) -> set[str]:
        linhas = set()
        for info in self.fetcher.stations.values():
            linhas.update(info["linhas"])
        return linhas

    def _reconstruir_linha(self, linha: str) -> list[tuple[str, str, float]]:
        """Reconstrói a sequência de uma linha como um caminho, ligando
        sempre o par de estações mais próximo ainda disponível, sem
        exceder grau 2 e sem formar ciclos."""
        estacoes = [
            stop_id for stop_id, info in self.fetcher.stations.items()
            if linha in info["linhas"]
        ]

        pares = sorted(
            (self._distancia(a, b), a, b)
            for i, a in enumerate(estacoes)
            for b in estacoes[i + 1:]
        )

        grau = {stop_id: 0 for stop_id in estacoes}
        pai = {stop_id: stop_id for stop_id in estacoes}

        def encontrar(x):
            while pai[x] != x:
                x = pai[x]
            return x

        arestas = []
        for dist, a, b in pares:
            if grau[a] >= 2 or grau[b] >= 2:
                continue
            if encontrar(a) == encontrar(b):
                continue  # evitar ciclos

            arestas.append((a, b, dist))
            grau[a] += 1
            grau[b] += 1
            pai[encontrar(a)] = encontrar(b)

        return arestas

    def _caminhos_da_linha(self, arestas: list[tuple[str, str, float]]) -> list[list[str]]:
        """Agrupa as arestas de uma linha em caminhos ordenados (sequências de nós),
        começando sempre num terminal (nó com grau 1)."""
        adj = defaultdict(list)
        for a, b, _ in arestas:
            adj[a].append(b)
            adj[b].append(a)

        visitados = set()
        caminhos = []

        for nodo in adj:
            if nodo in visitados or len(adj[nodo]) != 1:
                continue  # começar só a partir de terminais

            caminho = [nodo]
            visitados.add(nodo)
            atual = nodo

            while True:
                seguintes = [n for n in adj[atual] if n not in visitados]
                if not seguintes:
                    break
                atual = seguintes[0]
                caminho.append(atual)
                visitados.add(atual)

            caminhos.append(caminho)

        return caminhos

    def _agrupar_tempos_por_estacao(self) -> dict[str, dict[str, list[int]]]:
        """Agrupa as partidas por estação e por direção (nome do destino),
        devolvendo {stop_id: {destino_nome: [partidas em segundos, ordenadas]}}."""
        agrupado: dict[str, dict[str, list[int]]] = {}

        for entrada in self.fetcher.tempos_espera:
            stop_id = entrada["stop_id"]
            destino_nome = self.fetcher.destinos.get(entrada["destino"])

            if destino_nome is None:
                continue

            partidas = [
                parse_tempo(entrada.get(chave))
                for chave in ("tempoChegada1", "tempoChegada2", "tempoChegada3")
            ]
            partidas = [p for p in partidas if p is not None]

            agrupado.setdefault(stop_id, {}).setdefault(destino_nome, []).extend(partidas)

        for direcoes in agrupado.values():
            for partidas in direcoes.values():
                partidas.sort()

        return agrupado

    def _distancia(self, stop_id_a, stop_id_b) -> float:
        a = self.fetcher.stations[stop_id_a]
        b = self.fetcher.stations[stop_id_b]
        return haversine(a["lat"], a["lon"], b["lat"], b["lon"])

    # -----------------------------
    # CAMINHO MAIS RÁPIDO (time-dependent)
    # -----------------------------
    def caminho_mais_rapido(
        self, origem_id: str, destino_id: str, hora_inicio: float = 0.0
    ) -> tuple[list[str], float] | None:
        """Calcula o caminho com menor hora de chegada, partindo de
        `origem_id` no instante `hora_inicio` (segundos a partir de 'agora'),
        tendo em conta as partidas reais de cada estação."""

        fila = [(hora_inicio, origem_id, (origem_id,))]
        melhor_chegada = {origem_id: hora_inicio}

        while fila:
            hora_atual, nodo, caminho = heapq.heappop(fila)

            if nodo == destino_id:
                return list(caminho), hora_atual

            if hora_atual > melhor_chegada.get(nodo, float("inf")):
                continue  # já encontrámos forma mais rápida de chegar aqui

            for vizinho in self.G.neighbors(nodo):
                dados = self.G[nodo][vizinho]

                # direção a seguir a partir deste nó (nome do terminal)
                direcao = dados["direcao"][nodo]
                partidas = self.G.nodes[nodo]["partidas"].get(direcao, [])

                proxima_partida = next(
                    (p for p in partidas if p >= hora_atual), None
                )

                if proxima_partida is None:
                    # sem informação de partidas futuras: assume partida imediata
                    proxima_partida = hora_atual

                hora_chegada = proxima_partida + dados["tempo_seg"]

                if hora_chegada < melhor_chegada.get(vizinho, float("inf")):
                    melhor_chegada[vizinho] = hora_chegada
                    heapq.heappush(fila, (hora_chegada, vizinho, caminho + (vizinho,)))

        return None  # sem caminho encontrado
    # -----------------------------
    # EXPORTAÇÃO PARA O MAPA
    # -----------------------------
    def exportar_para_mapa(self, caminho: list[str] | None = None) -> dict:
        """Exporta os dados do grafo num formato simples para usar num mapa Leaflet."""
        estacoes = [
            {
                "id": stop_id,
                "nome": dados["nome"],
                "lat": dados["lat"],
                "lon": dados["lon"],
                "linhas": dados["linhas"],
            }
            for stop_id, dados in self.G.nodes(data=True)
        ]

        ligacoes = [
            {
                "origem": u,
                "destino": v,
                "linha": dados["linha"],
                "cor": dados["cor"],
            }
            for u, v, dados in self.G.edges(data=True)
        ]

        return {
            "estacoes": estacoes,
            "ligacoes": ligacoes,
            "caminho": caminho or [],
        }

    def guardar_json(self, path: str, caminho: list[str] | None = None) -> None:
        import json
        dados = self.exportar_para_mapa(caminho)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            
    # -----------------------------
    # VISUALIZAÇÃO
    # -----------------------------
    def visualize(self, show_labels: bool = False, node_size: int = 40):
        if self.G is None or self.G.number_of_nodes() == 0:
            return

        pos = {
            n: (d["x"], d["y"])
            for n, d in self.G.nodes(data=True)
        }

        plt.figure(figsize=(12, 10))

        edges = list(self.G.edges(data=True))
        weights = [d.get("weight", 1.0) for _, _, d in edges]
        max_w = max(weights) if weights else 1.0

        nx.draw_networkx_edges(
            self.G,
            pos,
            edgelist=[(u, v) for u, v, _ in edges],
            edge_color=[d.get("cor", COR_DEFAULT) for _, _, d in edges],
            width=[1 + 2 * (d.get("weight", 1.0) / max_w) for _, _, d in edges],
            alpha=0.7,
        )

        nx.draw_networkx_nodes(
            self.G,
            pos,
            node_size=node_size,
            node_color="black",
            alpha=0.8,
        )

        if show_labels:
            labels = {
                n: d.get("nome", n)
                for n, d in self.G.nodes(data=True)
            }
            nx.draw_networkx_labels(self.G, pos, labels, font_size=8)

        plt.title("Metro Graph (plano XY em km)")
        plt.xlabel("X (km, este-oeste)")
        plt.ylabel("Y (km, norte-sul)")
        plt.axis("equal")
        plt.tight_layout()
        plt.show()


async def main():
    fetcher = GraphFetcher()
    await fetcher.run()

    grafo = StationGraph(fetcher)
    grafo.build()

    print(f"Nós: {grafo.G.number_of_nodes()}")
    print(f"Arestas: {grafo.G.number_of_edges()}")
    for origem, destino, dados in grafo.G.edges(data=True):
        print(
            f"{origem} -> {destino} | "
            f"linha={dados['linha']} | "
            f"distância={dados['distancia_km']:.3f} km | "
            f"tempo={dados['tempo_seg']:.1f} s"
        )

    # exemplo: caminho mais rápido entre duas estações (ajustar os stop_id)
    origem_id, destino_id = next(iter(grafo.G.nodes)), list(grafo.G.nodes)[-1]
    resultado = grafo.caminho_mais_rapido(origem_id, destino_id)

    if resultado:
        caminho, hora_chegada = resultado
        nomes = [grafo.G.nodes[n]["nome"] for n in caminho]
        print(f"\nCaminho mais rápido de {nomes[0]} a {nomes[-1]}:")
        print(" -> ".join(nomes))
        print(f"Hora de chegada: {hora_chegada / 60:.1f} min")

    grafo.visualize(show_labels=True)
    caminho_ids = resultado[0] if resultado else None

    grafo.guardar_json("mapa/grafo.json", caminho=caminho_ids)

if __name__ == "__main__":
    asyncio.run(main())