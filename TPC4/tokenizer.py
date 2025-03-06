import re

def tokenize(query): 
    token_specification = [
        ("SELECT", r"SELECT|select"),
        ("WHERE", r"WHERE|where"),
        ("LIMIT", r"LIMIT|limit"),
        ("VARIABLE", r"\?\w+"),
        ("PA", r"{"),
        ("PF", r"}"),
        ("DOT", r"\."),
        ("NUM", r"\d+"),
        ("LITERAL", r"\"[\w ]+\"@?\w*"),
        ("PREDICATE", r"a|\w*:?\w+"),
        ("NEWLINE", r"\n"),
        ("SKIP", r"[ \t]+"),
        ("COMMENT", r"#.*"),
        ("ERRO", r".")
    ]
    tok_regex = '|'.join([f'(?P<{id}>{expreg})' for (id, expreg) in token_specification])
    reconhecidos = []
    linha = 1
    
    mo = re.finditer(tok_regex, query)
    for m in mo:
        dic = m.groupdict()
        if dic['SELECT'] is not None:
            t = ("SELECT", dic["SELECT"], linha, m.span())
        elif dic['WHERE']:
            t = ("WHERE", dic["WHERE"], linha, m.span())
        elif dic['LIMIT']:
            t = ("LIMIT", dic["LIMIT"], linha, m.span())
        elif dic['VARIABLE']:
            t = ("VARIABLE", dic["VARIABLE"], linha, m.span())
        elif dic['PA']:
            t = ("PA", dic["PA"], linha, m.span())
        elif dic["PF"]:
            t = ("PF", dic["PF"], linha, m.span())
        elif dic['DOT']:
            t = ("DOT", ".", linha, m.span())
        elif dic["NUM"]:
            t = ("NUM", dic["NUM"], linha, m.span())
        elif dic["LITERAL"]:
            t = ("LITERAL", dic["LITERAL"], linha, m.span())
        elif dic['PREDICATE']:
            t = ("PREDICATE", dic["PREDICATE"], linha, m.span())
        elif dic["NEWLINE"]:
            t = ("NEWLINE", dic["NEWLINE"], linha, m.span())
            linha += 1
        elif dic["COMMENT"]:
            t = ("COMMENT", dic["COMMENT"], linha, m.span())
        elif dic['SKIP']:
            pass
        else:
            t = ("ERRO", m.group(), linha, m.span())
        if not dic['SKIP']: reconhecidos.append(t)

    return reconhecidos

query = """# DBPedia: obras de Chuck Berry

select ?nome ?desc where {
    ?s a dbo:MusicalArtist.
    ?s foaf:name "Chuck Berry"@en .
    ?w dbo:artist ?s.
    ?w foaf:name ?nome.
    ?w dbo:abstract ?desc
} LIMIT 1000
"""

tokens = tokenize(query)
for token in tokens:
    print(token)