from lexer import lexer

next_simb = ("Erro", "", 0, 0)
stack = []
queue = []

def parseError(simb):
    print(f"Erro sintático, token inesperado: {simb}")

def rec_term(simb):
    global next_simb
    if next_simb.type == simb:
        value = next_simb.value
        next_simb = lexer.token()
        return value
    else:
        parseError(next_simb)

def rec_expr2():
    global next_simb
    if not next_simb:
        print("Reconheci P2: Expr2 -> ")
    elif next_simb.type == "OP":
        print("Reconheci P3: Expr2 -> Op Expr")
        operator = rec_term("OP")
        if operator in ["+", "-"]:
            if len(stack) > 0 and stack[-1] in ["*", "/", "+", "-"]:
                queue.append(stack.pop())
        stack.append(operator)
        rec_expr()
    else:
        parseError(next_simb)

def rec_expr():
    global next_simb
    if next_simb and next_simb.type == "NUM":
        print("Reconheci P1: Expr -> Num Expr2")
        number = int(rec_term("NUM"))
        queue.append(number)
        rec_expr2()
    else:
        parseError(next_simb)

def rec_parser(data):
    global next_simb
    lexer.input(data)
    next_simb = lexer.token()
    rec_expr()

def anasin(line):
    rec_parser(line)
    while len(stack) > 0:
        queue.append(stack.pop())
    while len(queue) > 0:
        if queue[0] not in ["+", "-", "*", "/"]:
            stack.append(queue.pop(0))
        else:
            secondElement = stack.pop()
            firstElement = stack.pop()
            match queue.pop(0):
                case "+":
                    stack.append(firstElement + secondElement)
                case "-":
                    stack.append(firstElement - secondElement)
                case "*":
                    stack.append(firstElement * secondElement)
                case "/":
                    stack.append(firstElement / secondElement)
    result = stack.pop()
    print(result)
    return result

if __name__ == "__main__":
    while(True):
        line = input("Introduza uma linha: ")
        anasin(line)