from ply import lex

tokens = (
    "OP",
    "NUM"
)

def t_OP(t):
    r"(\+|-|\*|\/)"
    return t

def t_NUM(t):
    r"\d+"
    return t

def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)

t_ignore  = " \t"

def t_error(t):
    print(f"ERROR ON TOKEN: {t.value}")
    t.lexer.skip(1)

lexer = lex.lex()

# if __name__ == "__main__":
#     data = """
#     5
#     5 + 3
#     5 + 3 * 2
#     2 * 7 - 5 * 3
#     2 / 5
# """
#     lexer.input(data)
#     while tok := lexer.token():
#         print(tok)