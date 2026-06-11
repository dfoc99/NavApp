# Dados
API do metro de lisboa

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


