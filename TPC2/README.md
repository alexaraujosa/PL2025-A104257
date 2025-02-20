# TPC2 - Análise de um dataset de obras musicais

**Data:** 14/02/2025  
**Nome:** Alex Araújo de Sá  
**Número Mecanográfico:** A104257  
![](./../Imagens/Avatar.png)

## Resumo

Leitura e processamento do [dataset](obras.csv), gerando os resultados:  

1. Lista ordenada alfabeticamente dos compositores musicais  
2. Distribuição das obras por período: quantas obras catalogadas em cada período  
3. Dicionário em que a cada período está a associada uma lista alfabética dos títulos das obras desse período  

Para a lista dos compositores musicais, aquando do processamento do dataset, são normalizadas entradas do campo compositor 
que possuam o caractér "," de forma a todas as entradas ficarem com o formato: ```<Primeiro Nome> <Último Nome>```.  

## Resultados

O programa imprime no terminal as respostas aos três requisitos apresentados.  
Para além disso, são criados três ficheiros em formato _json_ com os resultados, sendo eles:  
- [compositores](compositores.json)  
- [numeros](numeros.json)  
- [periodos](periodos.json)  