import sys

def somador(texto):
    active = True
    sum = 0
    for linha in texto.splitlines():
        i = 0
        while i < len(linha):
            if linha[i].lower() == '=':
                print(sum)

            if linha[i].lower() == 'o' and i+1 < len(linha):
                if linha[i+1].lower() == 'n':
                    active = True
                elif linha[i+1].lower() == 'f' and i+2 < len(linha) and linha[i+2].lower() == 'f':
                    active = False

            if active and linha[i].isdigit():
                value = ""
                while (i < len(linha)):
                    if linha[i].isdigit():
                        value += linha[i]
                        i += 1
                    else:
                        i -= 1
                        break
                sum += int(value)

            i += 1

def main(argv):
    somador(argv[1])

if __name__ == "__main__":
    main(sys.argv)