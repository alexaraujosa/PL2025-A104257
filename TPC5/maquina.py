import json
from math import floor
from datetime import datetime
from lexer import lex_input

moedas = [1, 2, 5, 10, 20, 50, 100, 200]

def load_json(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def setupMachine():
    stock = load_json("stock.json")["stock"]
    date = datetime.today().strftime('%Y-%m-%d')
    print(f"maq: {date}, Stock carregado, Estado atualizado.")
    print("maq: Bom dia. Estou disponível para atender o seu pedido.")
    return stock

def printStock(stock):
    print(f"maq:\ncod\t|\tnome\t\t|\tquantidade\t|\tpreço\n-----------------------------------------------------------------------")
    for item in stock:
        if item:
            print(f'{item.get("cod")}\t\t{item.get("nome")}\t\t{item.get("quant")}\t\t\t{item.get("preco")}')

def convertValue(value):
    euros = floor(value/100)
    centimos = value%100
    res = f'{str(euros)+"e" if euros != 0 else ""}{str(centimos)+"c" if centimos != 0 else ""}'
    return res if len(res) > 0 else "0c"

if __name__ == "__main__":
    stock = setupMachine()
    saldo = 0
    while (True):
        data = input(">> ")
        tokens = lex_input(data)
        while(len(tokens) > 0):
            tk = tokens.pop(0)
            match tk.value:
                case "LISTAR":
                    printStock(stock)
                case "MOEDA":
                    tk = tokens.pop(0)
                    print(tokens)
                    while(tk and tk.value != "."):
                        if tk.value in moedas:
                            saldo += tk.value
                        if len(tokens) > 0:
                            tk = tokens.pop(0)
                    print(f'maq: Saldo = {convertValue(saldo)}')
                case "SELECIONAR":
                    item_id = tokens.pop(0).value
                    item = None
                    for entry in stock:
                        if entry["cod"] == item_id:
                            item = entry
                    if item and item["quant"] > 0:
                        preco = int(item["preco"] * 100)
                        if saldo >= preco:
                            saldo -= preco
                            item["quant"] -= 1
                            print(f'maq: Pode retirar o produto dispensado "{item["nome"]}"')
                            print(f'maq: Saldo = {convertValue(saldo)}')
                        else:
                            print(f'maq: Saldo insuficiente para satisfazer o seu pedido')
                            print(f'maq: Saldo = {convertValue(saldo)}; Pedido = {convertValue(preco)}')
                    else:
                        print(f'maq: Não existe stock para esse produto.')
                case "SAIR":
                    moeda1e = floor(saldo/100)
                    saldo -= 100 * moeda1e
                    moeda50c = floor(saldo/50)
                    saldo -= 50 * moeda50c
                    moeda20c = floor(saldo/20)
                    saldo -= 20 * moeda20c
                    moeda10c = floor(saldo/10)
                    saldo -= 10 * moeda10c
                    moeda5c = floor(saldo/5)
                    saldo -= 5 * moeda5c
                    moeda2c = floor(saldo/2)
                    saldo -= 2 * moeda2c
                    moeda1c = saldo 
                    print(f'maq: Pode retirar o troco: ', end="")
                    print(f'{moeda1e}x 1e, {moeda50c}x 50c, {moeda20c}x 20c, {moeda10c}x 10c, {moeda5c}x 5c, {moeda2c}x 2c e {moeda1c}x 1c.')
                    print("maq: Até à próxima")
                    save_json("stock.json", {"stock": stock})
                    exit()