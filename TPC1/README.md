# TPC1 - Somador On/Off

**Realizado em:** 08/02/2025  
**Nome:** Alex Araújo de Sá  
**Número Mecanográfico:** A104257  
![](./../Imagens/Avatar.png)

## Resumo

Programa escrito em python que soma todas as sequências de dígitos que encontre num texto. 
O comportamento (somador) possui os seguintes requisitos:

- **Ligado:** Sempre que encontrar a string "On" em qualquer combinação de maiúsculas e minúsculas. 
- **Desligado:** Sempre que encontrar a string "Off" em qualquer combinação de maiúsculas e minúsculas. 
- **Mostrar resultado:** Sempre que encontrar o caráter "=". 

Ao iniciar o programa, o comportamento encontra-se **ligado**. 

## Resultados

O programa cumpre todos os requisitos do seu comportamento, tendo sido utilizados os seguintes testes para essa validação: 

1. Teste sem alteração do comportamento inicial 
    ```console
    $ python3 somador.py "182 19230 ="
    $ 19412
    ```

2. Teste com comportamento intercalado
    ```console
    $ python3 somador.py "1821 oFf 19230 oN 1="
    $ 1822
    ```

3. Teste com comportamento desligado
    ```console
    $ python3 somador.py "Off 12 123 123="
    $ 0
    ```

4. Teste com newlines e comportamento intercalado
    ```console
    $ python3 somador.py "Off = 12=On=asd12mkas\nadji12m\n\n\naas9id=ONasd12d=="
    $ 0
    $ 0
    $ 0
    $ 33
    $ 45
    $ 45
    ```

5. Teste demonstrado em sala de aula
    ```console
    $ python3 somador.py "opwaodsok45okaSknwIskndPOAWKs\noiwJAkjsndkasdj2025-02-07lkawmSDPMwkmoAnjsd\n=OIJWklamsdknwaOFfiawodam,awkmasd.\nawdisad789wands43akjwdasd\njawndkasndonoiijwdasd2auindiasnd\nAWOIJasjdnAW5jiawdasd="
    $ 2079
    $ 2086
    ```
