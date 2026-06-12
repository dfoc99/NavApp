# Dados
API do metro de lisboa
Cada estação tem a seguinte informação:
´´´json
{
    "stop_id": "AM",
    "stop_name": "Alameda",
    "stop_lat": "38.7373",
    "stop_lon": "-9.13409",
    "stop_url": "[https://www.metrolisboa.pt/viajar/alameda-linha-verde/,https://www.metrolisboa.pt/viajar/alameda-linha-vermelha/]",
    "linha": "[Verde, Vermelha]",
    "zone_id": "L"
}
´´´

# Grafo
Tempo entre estações + API tempo
O grafo tem que ser atualizado com o tempo da API
O cálculo do tempo entre estações e o menor tempo para um caminho tem que ter em conta o tempo de partida de cada combóio e o tempo entre cada nodo.

Exemplo:

A -> B -> c
Tempo até A partir: 10 min, 15 min
Tempo A -> B: 5 min
Tempo até B partir: 5 min, 10 min, 20 min
Tempo B -> C: 10 min
Tempo total: A (10 min) + A->B (5 min) = 15 min > 5 min
Tempo total: A (10 min) + A->B (5 min) = 15 min > 10 min
Tempo total: A (10 min) + A->B (5 min) = 15 min < 20 min -> 20 min + B->C (10 min) = 30 min 


Coordenadas X,Y com as coordenadas geográficas


## Encontrar os pontos adjacentes a uma estação
/tempoEspera/Estacao/todos apresenta para cada estação:
  "resposta": [
    {
      "stop_id": "RM",
      "cais": "AL4RMO",
      "hora": "20260612070444",
      "comboio": "26C",
      "tempoChegada1": "248",
      "comboio2": "27C",
      "tempoChegada2": "653",
      "comboio3": "21C",
      "tempoChegada3": "1085",
      "destino": "54",
      "sairServico": "0",
      "UT": "2"
    },
  ]

/infoDestinos/todos apresenta para cada estação:
"resposta": [
    {
      "id_destino": "33",
      "nome_destino": "Reboleira"
    },
  ]

/infoEstacao/todos apresenta para cada estação:
"resposta": [
    {
      "stop_id": "AM",
      "stop_name": "Alameda",
      "stop_lat": "38.7373",
      "stop_lon": "-9.13409",
      "stop_url": "[https://www.metrolisboa.pt/viajar/alameda-linha-verde/,https://www.metrolisboa.pt/viajar/alameda-linha-vermelha/]",
      "linha": "[Verde, Vermelha]",
      "zone_id": "L"
    },
]


"Alameda": "AM",
"Alfornelos": "AF",
"Alto dos Moinhos": "AH",
"Alvalade": "AL",
"Amadora Este": "AS",
"Ameixoeira": "AX",
"Anjos": "AN",
"Areeiro": "AE",
"Arroios": "AR",
"Avenida": "AV",
"Baixa/Chiado": "BC",
"Bela Vista": "BV",
"Cabo Ruivo": "CR",
"Cais do Sodr\u00e9": "CS",
"Campo Grande": "CG",
"Campo Pequeno": "CP",
"Carnide": "CA",
"Chelas": "CH",
"Cidade Universit\u00e1ria": "CU",
"Col\u00e9gio Militar/Luz": "CM",
"Entre Campos": "EC",
"Intendente": "IN",
"Jardim Zool\u00f3gico": "JZ",
"Laranjeiras": "LA",
"Lumiar": "LU",
"Marqu\u00eas de Pombal": "MP",
"Martim Moniz": "MM",
"Odivelas": "OD",
"Olaias": "OL",
"Olivais": "OS",
"Oriente": "OR",
"Parque": "PA",
"Picoas": "PI",
"Pontinha": "PO",
"Pra\u00e7a de Espanha": "PE",
"Quinta das Conchas": "QC",
"Rato": "RA",
"Restauradores": "RE",
"Roma": "RM",
"Rossio": "RO",
"Saldanha": "SA",
"Santa Apol\u00f3nia": "SP",
"S\u00e3o Sebasti\u00e3o": "SS",
"Senhor Roubado": "SR",
"Telheiras": "TE",
"Terreiro do Pa\u00e7o": "TP",
"Moscavide": "MO",
"Encarna\u00e7\u00e3o": "EN",
"Aeroporto": "AP",
"Reboleira": "RB"