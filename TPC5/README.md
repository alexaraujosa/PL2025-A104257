# TPC5 - Máquina de Vending

**Data:** 14/03/2025  
**Nome:** Alex Araújo de Sá  
**Número Mecanográfico:** A104257  
![](./../Imagens/Avatar.png)

## Resumo

Programa que simula uma máquina de vending, carregando de um ficheiro `json` o seu stock, de forma a suportar
um conjunto de operações básicas:  

- Listar os Produtos
- Inserir moedas
- Selecionar um produto
- Sair  

O programa carrega os dados do ficheiro `json` para a memória quando o programa arrancar, gravando os mesmo quando este termina.  

## Resultados

O programa foi desenvolvido na linguagem `python` e cumpre com todos os requisitos.  
Foi utilizado um analisador [léxico](./lexer.py) que permitiu a extração e manipulação de tokens, sendo estes utilizados
no programa [principal](maquina.py) de forma a interpretar e decidir consoante os diferentes tipos de operações.  
O programa tem como [stock](./stock.json) um ficheiro `json`, sendo os seus dados carregados assim que o programa arranca e, de igual forma,
guardados quando o utilizador desejar sair do programa.  