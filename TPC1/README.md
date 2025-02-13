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

Utilização do programa:  
```console
$ python3 somador.py "oi=asd12=asd0129="
```

Utilização dos testes unitários:  
```console
$ python3 tester.py
```

## Resultados

O programa cumpre todos os requisitos do seu comportamento, tendo sido utilizados testes unitários para fazer essa validação.   
Os testes unitários encontram-se no ficheiro [tester.py](tester.py), que foi escrito em python utilizando o módulo _unittest_.