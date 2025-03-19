import ply.lex as lex

states = (
    ("moeda", "exclusive"),
    ("selecionar", "exclusive")
)

tokens = (
    "LISTAR",
    "MOEDA",
    "SELECIONAR",
    "SAIR",
    "ID",
    "SEPARADOR",
    "TERMINATOR",
    "VALUE"
)

def t_LISTAR(t):
    r"LISTAR"
    return t

def t_MOEDA(t):
    r"MOEDA"
    t.lexer.begin("moeda")
    return t

def t_SELECIONAR(t):
    r"SELECIONAR"
    t.lexer.begin("selecionar")
    return t

def t_ANY_SAIR(t):
    r"SAIR"
    t.lexer.begin("INITIAL")
    return t

def t_selecionar_ID(t):
    r"[A-Z]\d+"
    t.lexer.begin("INITIAL")
    return t

def t_moeda_SEPARADOR(t):
    r","
    pass

def t_moeda_TERMINATOR(t):
    r"\."
    t.lexer.begin("INITIAL")
    return t

def t_moeda_VALUE(t):
    r"\d+(?P<unidade>e|c)"
    t.value = int(t.value[:-1])
    if t.lexer.lexmatch.groupdict()["unidade"] == "e":
        t.value *= 100
    return t

t_ANY_ignore = " \t\n"

def t_ANY_error(t):
    print(f"ERROR ON TOKEN: {t.value}")
    t.lexer.skip(1)

lexer = lex.lex()

def lex_input(data):
    lexer.input(data)
    list = []
    while tok := lexer.token():
        list.append(tok)
    return list
    # while tok := lexer.token():
    #     print(tok)

# if __name__ == "__main__":
#     data = """
#         MOEDA 1e, 20c, 5c, 5c .
#         SELECIONAR A23
#         SAIR
#     """
#     lexer = lex.lex()
#     lexer.input(data)
#     print(data)
#     while tok := lexer.token():
#         print(tok)