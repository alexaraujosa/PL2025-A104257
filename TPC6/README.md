# TPC6 - Recursivo Descendente para expressões aritméticas

**Data:** 14/03/2025  
**Nome:** Alex Araújo de Sá  
**Número Mecanográfico:** A104257  
![](./../Imagens/Avatar.png)

## Resumo

Parser LL(1) recursivo descendente que reconhece expressões aritméticas e calcula o respetivo valor, respeitando as prioridades 
das operações.  

## Resultados

Criado um analisador [léxico](lexer.py) que permite detetar números e as operações aritméticas num texto.  
Esses tokens são passados para um analisador [sintático](gram.py) definido pela seguinte gramática:  

```
T = { '+', '-', '*', '/', num }
S = { Expr }
N = { Expr, Expr2, Op }
P = {

    Expr  -> num Expr2
    Expr2 -> ε
          |  Op num Expr2
    Op    -> '+' | '-' | '*' | '/' 

}
```

O programa do analisador sintático possui uma _stack_ e uma _queue_ que permitem a aplicação do algoritmo _Shunting Yard_ a este problema,
de forma a resolver o problema das prioridades das operações. Este algoritmo é utilizado durante a avaliação dos tokens consoante
as regras da gramática, adicionando os operadores ou números à respetiva estrutura de dados. Desta forma, no final da avaliação 
dos tokens, teremos uma stack com notação _postfix_, permitindo-nos, mais uma vez, obter o resultado da expressão aritmética respeitando
as prioridades das operações.  

Por fim, uma ficheiro com [testes](tester.py) foi criado, possuindo 6 tipos de testes:
1. Básico
2. Soma
3. Subtração
4. Multiplicação
5. Divisão
6. Avançado