# TPC4 - Analisador Léxico

**Data:** 28/02/2025  
**Nome:** Alex Araújo de Sá  
**Número Mecanográfico:** A104257  
![](./../Imagens/Avatar.png)

## Resumo

Analisador léxico em python para uma linguagem de query simples.     

## Resultados

Desenvolvido o [analisador](./tokenizer.py) de forma a obter os tokens da frase:
```
# DBPedia: obras de Chuck Berry

select ?nome ?desc where {
    ?s a dbo:MusicalArtist.
    ?s foaf:name "Chuck Berry"@en .
    ?w dbo:artist ?s.
    ?w foaf:name ?nome.
    ?w dbo:abstract ?desc
} LIMIT 1000
```

Esta frase representa uma query em SPARQL, na qual são utilizadas poucas funcionalidades desta linguagem.  
De seguida está representada a lista de tokens, nomeadamente expressões regulares para os identificar, seguindo uma ordem de prioridade decrescente:
- Palavras Reservadas: `r"SELECT|select"`, `r"WHERE|where"`, `r"LIMIT|limit"`  
- Variáveis: `r"\?\w+"`  
- Símbolos: `r"{"`, `r"}"`, `r"\."`
- Números: `r"\d+"`
- Literais: `r"\"[\w ]+\"@?\w*"`
- Predicados: `r"a|\w*:?\w+"`
- Comentários: `r"#.*"`   

Ainda assim, existem mais 3 expressões regulares definidas no analisador léxico, de forma a alterar a linha, ignorar espaços em branco e printar erros.  
Por fim, o resultado da execução do programa gera o seguinte output para o terminal:  

```
('COMMENT', '# DBPedia: obras de Chuck Berry', 1, (0, 31))
('NEWLINE', '\n', 1, (31, 32))
('NEWLINE', '\n', 2, (32, 33))
('SELECT', 'select', 3, (33, 39))
('VARIABLE', '?nome', 3, (40, 45))
('VARIABLE', '?desc', 3, (46, 51))
...
```