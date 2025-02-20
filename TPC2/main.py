import sys 
import json

def save_to_json(filename, data):
    with open(filename, "w") as file:
        file.write(json.dumps(data, indent=2, ensure_ascii=False))

def custom_read_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        header = file.readline()

        result = []
        line = []
        for i in range(len(header.split(";"))):
            line.append("")
        index = 0
        in_description = False

        c = file.read(1)
        last_c = ""
        while(c):
        
            # Skip new line on begin
            if index == 0 and c == "\n":
                c = file.read(1)
                continue

            # Start of description
            if last_c == ";" and c == "\"":
                in_description = True
            
            # End of description
            if last_c == "\"" and c == ";":
                in_description = False
                line[index] = line[index].replace("\n", "")

            # New field
            if c == ";" and not in_description:
                # Normalize compositor name
                if index == 4 and "," in line[4]:
                    splited = line[4].split(",")
                    new_name = splited[1][1:] + " " + splited[0]
                    line[4] = new_name

                # Change field
                index += 1
                last_c = c
                c = file.read(1)
                continue

            # Cleanup description
            if c.isspace() and in_description:
                while (c.isspace()):
                    c = file.read(1)
                line[index] += " "

            # End of line
            if last_c == ";" and c == "O":
                line[index] += c
                # Consume line until end
                c = file.read(1)
                while (c.isdigit()):
                    line[index] += c
                    c = file.read(1)
                # Result setup
                result.append(line[:])
                # Reset variables
                for i in range(len(line)):
                    line[i] = ""
                index = 0
                continue
                

            line[index] += c
            last_c = c
            c = file.read(1)
    
    return result    


def main(path):
    parsed = custom_read_file(path)
    compositores = set()
    periodos = {}

    for line in parsed:
        # Períodos
        if line[3]:
            if not periodos.get(line[3]):
                periodos[line[3]] = []
                periodos[line[3]].append(line[0])
            else:
                periodos[line[3]].append(line[0])

        # Compositores
        if line[4]:
            compositores.add(line[4])

    compositores = sorted(compositores)
    quantidades_periodo = {}

    # Output
    print("Lista ordenada alfabeticamente dos compositores musicais (normalizado):")
    for compositor in compositores:
        print(f" - {compositor}")
    print("-----")

    print("Quantidade de obras por período:")
    for periodo in periodos.keys():
        print(f" - {periodo} tem {len(periodos[periodo])} obras")
        quantidades_periodo[periodo] = len(periodos[periodo])
    print("-----")

    print("Dicionário que associa a cada período uma lista com os títulos das obras, ordenada alfabeticamente:")
    for periodo in periodos.keys():
        print(f"-> {periodo}:")
        periodos[periodo].sort()
        for titulo in periodos[periodo]:
            print(f" :: {titulo}")

    # Results saver
    save_to_json("compositores.json", compositores)
    save_to_json("periodos.json", periodos)
    save_to_json("numeros.json", quantidades_periodo)
    

if __name__ == "__main__":
    if (len(sys.argv) == 2):
        main(sys.argv[1])
    else:
        print("Insufficient arguments. Usage: python3 main.py filepath")