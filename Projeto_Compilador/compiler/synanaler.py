from ply import yacc
from inspect import getframeinfo, stack
from .lexer import tokens, TokenPos, posToRowCol, lexer
from .diag import Diagnostic, DiagnosticType, DiagnosticKind, DiagnosticSource
import compiler.ast as ast

#
# Syntatic Analyser
# 
#   This module performs syntatic analysis on a token stream obtained through the lexing of a given source text.
#   In order for diagnostics to be properly processed, the lexer should be called to iterate on the whole source text
# before passing control over to the syntatic analyser in order to extract lexical diagnostics, followed by a call to
# lexer.reset().
#   When calling parser.parse, the lexer should be passed explicitly as an argument, along with it's custom token
# mock, lexer.getExtendedToken, in order for the tokens passed to have their location metadata correctly mapped to the
# source text.
#
#  On Error Handling:
#    Error handling should be preferrably done through resynchronization rules (see Section 6.8.1 of 
# https://www.dabeaz.com/ply/ply.html). When designing resynchronization rules, take into consideration that having an
# 'error' token on the right hand side of a production WILL silently capture every error due to the rule being 
# instantly reduced. During testing, it might APPEAR to work fine for one singular error on the same rule, but further 
# testing will reveal the non-intuitive behavior. This is a built-in functionality of PLY.yacc and cannot feasibly be 
# worked around.
#

start = "program"
precedence = (
    ('left', 'SEMICOLON'),
    ('left', 'COLON'),
    ('right', 'OP_ASSIGN'),
    ('left', 'OP_PLUS', 'OP_MINUS', 'KW_OR'),
    ('left', 'OP_MULT', 'OP_DIV', 'KW_DIV', 'KW_MOD', 'KW_AND'),
    ('left', 'OP_EQ', 'OP_NEQ', 'OP_LT', 'OP_LTE', 'OP_GT', 'OP_GTE', 'KW_IN'),
    ('right', 'KW_NOT'),
    ('left', 'LPAREN', 'RPAREN'),
    ('left', 'LSBRACKET', 'RSBRACKET'),
    ('left', 'LBRACE', 'RBRACE'),
    ('nonassoc', 'KW_ELSE'), 
)

#region ============== Backtracks =============
# In this region are defined backtrack tokens. When an error might be caused by an erroneous production after a known
# terminal, it might be useful to get the token that is the true cause of the error, instead of the token that triggered
# the resynchronization (usually SEMICOLON). In those cases, instead of using the terminal itself, one should use it's
# backtrack correspondent (e.g. instead of using KW_OP, one would use bt_KW_OF).

def p_bt_KW_OF(p):
    """
    bt_KW_OF : KW_OF
    """
    p.parser.backtracks["KW_OF"] = lexer._cur
    p[0] = p[1]

def p_bt_GENERIC(p):
    """
    bt_GENERIC : empty
    """
    p.parser.backtracks["GENERIC"] = lexer._lastSep
#endregion ============== Backtracks =============

#region ============== Compound Primitives =============
def p_number(p):
    """
    number : UNSIGNED_REAL 
           | UNSIGNED_INTEGER 
    """
        #    | SIGNED_REAL 
        #    | SIGNED_INTEGER
    # Ply.yacc reduces all terminals to their values by default. Here, the type of the token is also required to 
    #   differentiate between real and integer numbers and their sign kind. For this purpose, a YaccProduction object 
    #   contains the property 'slice', which contains the token instances.
    t = p.slice[1]
    p[0] = ast.NumberNode(t.value, ast.NumberKind[t.type]).setTokenPos(t.pos)

def p_unsignedConstant(p):
    """
    unsignedConstant : UNSIGNED_REAL 
                     | UNSIGNED_INTEGER 
                     | STRING
                     | KW_NIL
    """
                    #  | IDENTIFIER
    t = p.slice[1]
    match(t.type):
        case "UNSIGNED_REAL" | "UNSIGNED_INTEGER": 
            p[0] = ast.UnsignedConstantNode(ast.NumberNode(t.value, ast.NumberKind[t.type]).setTokenPos(t.pos))
        case "STRING": p[0] = ast.UnsignedConstantNode(ast.StringNode(p[1]).setTokenPos(t.pos))
        case "IDENTIFIER": p[0] = ast.UnsignedConstantNode(ast.IdentifierNode(p[1]).setTokenPos(t.pos))
        case "KW_NIL": p[0] = ast.UnsignedConstantNode(ast.SpecialSymbolNode(ast.SpecialSymbolKind.SS_NIL).setTokenPos(t.pos))

def p_directive(p):
    """
    directive : IDENTIFIER
    """
    p[0] = ast.DirectiveNode(p[1]).setTokenPos(p.slice[1].pos)
#endregion ============== Compound Primitives =============

#region ============== Section 3 ==============
def p_program(p):
    """
    program : programHeading SEMICOLON block DOT
    """
    p[0] = ast.ProgramNode(p[1], p[3]).setStartTokenPos(p[1].pos).setEndTokenPos(p.slice[4].pos)

# Section 3.A
#region -------------- Program Heading --------------
def p_programHeading(p):
    """
    programHeading : KW_PROGRAM IDENTIFIER programExternals
    """
    p[0] = ast.ProgramHeadingNode(p[2], p[3]).setStartTokenPos(p.slice[1].pos)
    if (p[3] != None):  p[0].setEndTokenPos(p.slice[1].lexer.peek().pos)

def p_programExternals(p):
    """
    programExternals : LPAREN programExternalsBody RPAREN
                     | empty
    """
    if (len(p) == 4): p[0] = p[2]
    else: p[0] = None
def p_programExternals_error(p):
    """
    programExternals : LPAREN error RPAREN
    """
    popDiagnostic()
    t = p[2]
    syn_error(t, DiagnosticType.UNEXPECTED_TOKEN, { "token": t.type })

def p_programExternalsBody(p):
    """
    programExternalsBody : programExternalsBody COMMA IDENTIFIER
                         | IDENTIFIER
                         | empty
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

#endregion -------------- Program Heading --------------


#region -------------- Block --------------
def p_block(p):
    """
    block : labelDeclarationPart constDefinitionPart typeDefinitionPart variableDeclarationPart procedureAndFunctionDefinitionPart statementPart
    """
    p[0] = ast.BlockNode(p[1], p[2], p[3], p[4], p[5], p[6])#.setStartTokenPos(p[1].pos).setEndTokenPos(p[5].pos)
    for i in range(1, 7):
        if (p[i] != None): 
            p[0].setStartTokenPos(p[i].pos)
            break
    
    if (p[6] == None): raise SyntaxError()
    p[0].setEndTokenPos(p[6].pos)

# Section 3.B
#region ------- Label Declaration -------
def p_labelDeclarationPart(p):
    """
    labelDeclarationPart : KW_LABEL labelDeclarationPartBody SEMICOLON
                         | empty
    """
    if (len(p) == 4): p[0] = ast.LabelDeclarationNode(p[2]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[3].pos)
    else: p[0] = None
def p_labelDeclarationPart_error(p):
    """
    labelDeclarationPart : KW_LABEL error SEMICOLON
    """
    popDiagnostic()
    t = p[2]
    syn_error(t, DiagnosticType.INVALID_LABEL, { "value": t.value })

def p_labelDeclarationPartBody(p):
    """
    labelDeclarationPartBody : labelDeclarationPartBody COMMA UNSIGNED_INTEGER
                             | UNSIGNED_INTEGER
                             | empty
    """
    if (len(p) == 4): p[0] = p[1] + [ast.NumberNode(p[3], ast.NumberKind.UNSIGNED_INTEGER).setTokenPos(p.slice[3].pos)]
    else: p[0] = [ast.NumberNode(p[1], ast.NumberKind.UNSIGNED_INTEGER).setTokenPos(p.slice[1].pos)]
#endregion ------- Label Declaration -------

# Section 3.C
#region ------- Constants Definition -------
#   Note: There aren't enough words in the english lexicon to express the full extent of the mental anguish and pure 
# unadulterated suffering I've put myself through to handle syntax errors in this section, only to ultimately give up.
#   I am dumbfounded by how bad of a tool ply.yacc is for doing the only job it had to and I would only recommend it's 
# usage to someone who's either a masochist or wants an excuse to end their own existence.

def p_constDefinitionPart(p):
    """
    constDefinitionPart : KW_CONST constDefinitionPartBody SEMICOLON
                        | empty
    """
    if (len(p) == 4): 
        p[0] = ast.ConstantDefinitionPartNode(p[2]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[3].pos)
    else: p[0] = None
def p_constDefinitionPart_error(p):
    """
    constDefinitionPart : KW_CONST error SEMICOLON
    """
    # Purposedly doesn't pop the default diagnostic. This rule immediately makes the parser give up processing the 
    # constants.
    p[0] = None
    
def p_constDefinitionPartBody(p):
    """
    constDefinitionPartBody : constDefinitionPartBody SEMICOLON constDefinition
                            | constDefinition
    """
    if (len(p) > 2): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_constDefinition(p):
    """
    constDefinition : IDENTIFIER OP_EQ constElem
    """
    p[0] = ast.ConstantDefinitionNode(p[1], p[3]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[3].pos)

# def p_constElem(p):
#     """
#     constElem : number 
#               | IDENTIFIER 
#               | STRING
#     """
#     if (isinstance(p[1], ast.Node)): p[0] = p[1]
#     elif (p.slice[1].type == "STRING"): p[0] = ast.StringNode(p[1]).setTokenPos(p.slice[1].pos)
#     else: p[0] = ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos)
def p_constElem(p):
    """
    constElem : number 
              | OP_PLUS number
              | OP_MINUS number
              | IDENTIFIER 
              | STRING
    """
    if (isinstance(p[1], ast.Node)): p[0] = p[1]
    elif (p.slice[1].type == "OP_PLUS" or p.slice[1].type == "OP_MINUS"): 
        p[0] = p[2].sign(p.slice[1].type).setStartTokenPos(p.slice[1].pos)
    elif (p.slice[1].type == "STRING"): p[0] = ast.StringNode(p[1]).setTokenPos(p.slice[1].pos)
    else: p[0] = ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos)
#endregion ------- Constants Definition -------

# Section 3.D
#region ------- Type Definition -------
def p_typeDefinitionPart(p):
    """
    typeDefinitionPart : KW_TYPE typeDefinitionPartBody SEMICOLON
                       | empty
    """
    if (len(p) == 4): p[0] = ast.TypeDefinitionPartNode(p[2]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[3].pos)
    else: p[0] = None

def p_typeDefinitionPartBody(p):
    """
    typeDefinitionPartBody : typeDefinitionPartBody SEMICOLON typeDefinition
                           | typeDefinition
    """
    if (len(p) == 4): 
        if (p[1] == None or p[3] == None): p[0] = None
        else: p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]
def p_typeDefinitionPartBody_error(p):
    """
    typeDefinitionPartBody : typeDefinitionPartBody error
                           | typeDefinitionPartBody SEMICOLON error
                           | error
    """
    # typeDefinitionPartBody : error SEMICOLON typeDefinition
    popDiagnostic()
    t = None
    if (len(p) == 2): t = p[1]
    elif (len(p) == 3): t = p[2]
    else: t = p[3]

    # print("TDPB ERR:", list(p), vars(p.slice[-1]), t)
    syn_error(t, DiagnosticType.INVALID_TYPE, { "value": t.value })

def p_typeDefinition(p):
    """
    typeDefinition : IDENTIFIER OP_EQ type
    """
    p[0] = ast.TypeDefinitionNode(p[1], p[3]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[3].pos)

def p_type(p):
    """
    type : simpleType 
         | structuredType 
         | pointerType
    """
    p[0] = p[1]

#region ---- Section R6.1 ----
def p_simpleType(p):
    """
    simpleType : ordinalType
    """
            #    | IDENTIFIER
    if (isinstance(p[1], ast.Node)): p[0] = p[1]
    elif (p[1] == None): p[0] = p[1] # Error occured
    # else: p[0] = ast.TypeIdentifierNode(ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos))

def p_ordinalType(p):
    """
    ordinalType : enumeratedType
                | subrangeType
                | IDENTIFIER
    """
    if (isinstance(p[1], ast.Node)): p[0] = p[1]
    elif (p[1] == None): p[0] = p[1] # Error occured
    else: p[0] = ast.TypeIdentifierNode(ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos))

#region - Section R6.1.1 -
def p_enumeratedType(p):
    """
    enumeratedType : LPAREN enumeratedTypeList RPAREN
    """
    p[0] = ast.EnumeratedTypeNode(p[2]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[3].pos)
def p_enumeratedType_error(p):
    """
    enumeratedType : LPAREN error RPAREN
    """
                #    | LPAREN 
    popDiagnostic()
    t = p[2]

    match(t.type):
        case "SEMICOLON":
            syn_error(t, DiagnosticType.MALTERMINATED_TYPE, { "expected": ")", "actual": t.value })
        case _:
            syn_error(t, DiagnosticType.INVALID_TYPE, { "value": t.value })

def p_enumeratedTypeList(p):
    """
    enumeratedTypeList : enumeratedTypeList COMMA IDENTIFIER
                       | IDENTIFIER
    """
    if (len(p) == 4): p[0] = p[1] + [ast.IdentifierNode(p[3]).setTokenPos(p.slice[3].pos)]
    else: p[0] = [ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos)]
def p_enumeratedTypeList_error(p):
    """
    enumeratedTypeList : enumeratedTypeList COMMA IDENTIFIER error
                       | IDENTIFIER error
    """
    # This production is here to prevent an infinite loop that occurs if a COMMA is ommited between IDENTIFIERs.
    p[0] = []
#endregion - Section R6.1.1 -

#region - Section R6.1.3 -
def p_subrangeType(p):
    """
    subrangeType : constElem OP_RANGE constElem
    """
    p[0] = ast.SubrangeTypeNode(p[1], p[3]).setStartTokenPos(p[1].pos).setEndTokenPos(p[3].pos)
#endregion - Section R6.1.3 -
#endregion ---- Section R6.1 ----

#region ---- Section R6.2 ----
def p_structuredType(p):
    """
    structuredType : KW_PACKED unpackedStructuredType
                   | unpackedStructuredType
    """
                #    | IDENTIFIER
    if (len(p) > 2):
        if (p[2] == None): return None
        else:
            p[2].packed = True
            p[0] = p[2].setStartTokenPos(p.slice[1].pos)
    else:
        if (p[1] == None): p[0] = None
        elif (p[1].ist(ast.Node)): p[0] = p[1]
        else: p[0] = ast.TypeIdentifierNode(ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos))

def p_unpackedStructuredType(p):
    """
    unpackedStructuredType : arrayType
                           | recordType
                           | setType
    """
                        #    | fileType
    p[0] = p[1]

#region - Section R6.2.1 -
def p_arrayType(p):
    """
    arrayType : KW_ARRAY LSBRACKET indexTypeList RSBRACKET bt_KW_OF type
    """
    p[0] = ast.ArrayTypeNode(p[3], p[6]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[6].pos)
def p_arrayType_error(p):
    """
    arrayType : KW_ARRAY LSBRACKET indexTypeList RSBRACKET bt_KW_OF error
              | KW_ARRAY LSBRACKET error
    """
    if (len(p) == 7): 
        popDiagnostic()
        t = p[6]
        # For the sake of better error handling, I'm using this hack with backtracking and direct access to the lexer's 
        # current token in order to display a more accurate error message, rather than letting it fallback to typeDefinition
        # and throw the error at the SEMICOLON token, which is far less useful.
        syn_error(t, DiagnosticType.INVALID_TYPE, { "value": p.parser.backtracks["KW_OF"].value })
   
    p[0] = None

def p_indexTypeList(p):
    """
    indexTypeList : indexTypeList COMMA ordinalType
                  | ordinalType
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]
#endregion - Section R6.2.1 -

#region - Section 7 -
# NOTE: The grammar is the Report Section 6.2.2 is not only nonsensical, it's completely fucking wrong. Use the grammar 
# in Section 7 instead.
def p_recordType(p):
    """
    recordType : KW_RECORD fieldList KW_END
    """
    fieldList = p[2]
    if (fieldList == None): 
        p[0] = ast.RecordTypeNode().setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[3].pos)
    else: 
        p[0] = ast.RecordTypeNode(fieldList[0], fieldList[1]) \
            .setStartTokenPos(p.slice[1].pos) \
            .setEndTokenPos(p.slice[3].pos)
def p_recordType_error(p):
    """
    recordType : KW_RECORD fieldList error
    """
    # This production doesn't generate a new diagnostic because at this point, the program can (and probably be) fucked
    # six ways to Sunday and the token that will trigger the error is probably halfway to Narnia at this point, so I 
    # rely on the backtrack mark GENERIC, used by the fieldListTerminator production to get a (somewhat) more accurate
    # error position. Does this solve anything? FUCK NO. Ply.Yacc is simply a horrible tool and I could do something
    # better in less time with fucking assembly.

    # print("RT ERR", list(p), parser.backtracks["GENERIC"])
    # popDiagnostic()
    # t = parser.backtracks["GENERIC"]
    # syn_error(t, DiagnosticType.UNTERMINATED_TYPE, {})

def p_fieldList(p):
    """
    fieldList : fixedPart fieldListTail
              | fieldListDirectTail
              | empty
    """
    if (len(p) > 2): p[0] = (p[1], p[2])
#     else: p[0] = (None, p[1])
# def p_fieldList_error(p):
#     """
#     fieldList : error fieldListTail
#     """
#             #   | KW_CASE
#     print("FL ERR:", list(p), list(p.slice), )
#     t = p.slice[1]
#     # if (t.type == "KW_CASE"):
#     #     popDiagnostic()
#     #     syn_error(t, DiagnosticType.RECORD_NO_FIXED_PART, {})
#     #     advanceUntil(lambda t: t.type == 'KW_END')

def p_fieldListDirectTail(p):
    """
    fieldListDirectTail : variantPart fieldListTerminator
    """
    p[0] = p[1]

def p_fieldListTail(p):
    """
    fieldListTail : SEMICOLON variantPart fieldListTerminator
                  | fieldListTerminator
    """
    if (len(p) == 4): p[0] = p[2]
    else: p[0] = None

def p_fieldListTerminator(p):
    """
    fieldListTerminator : SEMICOLON bt_GENERIC
                        | bt_GENERIC
    """
    p[0] = p[1]

#region - Section 7.A - 
def p_fixedPart(p):
    """
    fixedPart : fixedPart SEMICOLON recordSection
              | recordSection
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_recordSection(p):
    """
    recordSection : recordSectionHead COLON type
    """
    if (p[1] == None or p[3] == None):
        # t = p.slice[2]
        # if (getattr(t, "lexer", None) == None): t.lexer = lexer
        # syn_error(t, DiagnosticType.INVALID_TYPE, { "value": "None" })
        raise SyntaxError
    else:
        p[0] = ast.RecordSectionNode(p[1], p[3]).setStartTokenPos(p[1][0].pos).setEndTokenPos(p[3].pos)

def p_recordSectionHead(p):
    """
    recordSectionHead : recordSectionHead COMMA IDENTIFIER
                      | IDENTIFIER
    """
    if (len(p) == 4): p[0] = p[1] + [ast.IdentifierNode(p[3]).setTokenPos(p.slice[3].pos)]
    else: p[0] = [ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos)]
# def p_recordSectionHead_error(p):
#     """
#     recordSectionHead : error
#     """
#     print("RSH ERR:", list(p))
#     p[0] = 0
#endregion - Section 7.A - 

#region - Section 7.B - 
# Here, I'm using fieldListTerminator to resolve a shift/reduce conflict caused by the optional SEMICOLON.
# Allowing it to bubble up to fieldListTail makes it explode, for some fucking reason.
def p_variantPart(p):
    # """
    # variantPart : KW_CASE variantSelector KW_OF variantPartBody variantPartTerminator
    # """
    """
    variantPart : KW_CASE variantSelector KW_OF variantPartBody
    """
    p[0] = ast.RecordVariantNode(
        p[2][0], 
        ast.TypeIdentifierNode(ast.IdentifierNode(p[2][1]).setTokenPos(p.slice[1].pos)), 
        p[4]
    ).setStartTokenPos(p.slice[1].pos)
    p[0].setEndTokenPos(p[4][-1].pos)
    # p[0].setEndTokenPos(p[4][1].pos)

def p_variantSelector(p):
    """
    variantSelector : IDENTIFIER variantIdentifier
    """
    if (p[2] == None): p[0] = (None, p[1])
    else: p[0] = (p[1], p[2])

def p_variantIdentifier(p):
    """
    variantIdentifier : COLON IDENTIFIER
                      | empty
    """
    if (len(p) == 3): p[0] = p[2]
    else: p[0] = None

def p_variantPartTerminator(p):
    """
    variantPartTerminator : SEMICOLON
                          | empty
    """

def p_variantPartBodyList(p):
    """
    variantPartBodyList : variantPartBody
                        | variantPartBody SEMICOLON
    """
    if (len(p) == 3): p[0] = (p[1], p.slice[2])
    else: p[0] = (p[1], p[1][-1])

def p_variantPartBody(p):
    """
    variantPartBody : variantPartBody SEMICOLON variantCase
                    | variantCase
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_variantCase(p):
    """
    variantCase : variantCaseConsts COLON LPAREN fieldList RPAREN
    """
    fieldList = p[4]
    if (fieldList == None): 
        p[0] = ast.RecordVariantCaseNode(p[1]).setStartTokenPos(p[1][0].pos).setEndTokenPos(p.slice[5].pos)
    else: 
        p[0] = ast.RecordVariantCaseNode(p[1], fieldList[0], fieldList[1]) \
        .setStartTokenPos(p[1][0].pos).setEndTokenPos(p.slice[5].pos)
def p_variantCase_error(p):
    """
    variantCase : variantCaseConsts COLON LPAREN fieldList error
    """
    # This production is here to prevent an infinite loop that occurs if a case in initiated, but not terminated.
    p.parser.errok()

def p_variantCaseConsts(p):
    """
    variantCaseConsts : variantCaseConsts COMMA constElem
                      | constElem
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

#endregion - Section 7.B - 
#endregion - Section 7 -

#region - Section R6.2.3 -
def p_setType(p):
    """
    setType : KW_SET KW_OF ordinalType
    """
    p[0] = ast.SetTypeNode(p[3]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[3].pos)
#endregion - Section R6.2.3 -

#region - Section R6.2.4 -
# NOTE: Removed for the time being due to limitations on the target architecture.
# def p_fileType(p):
#     """
#     fileType : KW_FILE KW_OF type
#     """
#     p[0] = ast.FileTypeNode(p[3])
#endregion - Section R6.2.4 -
#endregion ---- Section R6.2 ----

#region ---- Section R6.3 ----
def p_pointerType(p):
    """
    pointerType : OP_UPARROW type
    """
                # | IDENTIFIER
    if (len(p) == 3): p[0] = ast.PointerTypeNode(p[2]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[2].pos)
    # else: p[0] = ast.TypeIdentifierNode(ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos))
#endregion ---- Section R6.3 ----
#endregion ------- Type Definition -------

# Section 3.E
#region ------- Variable Declaration -------
def p_variableDeclarationPart(p):
    """
    variableDeclarationPart : KW_VAR variableDeclarationPartBody SEMICOLON
                            | empty
    """
    if (len(p) == 4): 
        p[0] = ast.VariableDeclarationPartNode(p[2]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[3].pos)
    else: p[0] = None

def p_variableDeclarationPartBody(p):
    """
    variableDeclarationPartBody : variableDeclarationPartBody SEMICOLON variableDeclaration
                                | variableDeclaration
    """
    if (len(p) == 4): 
        if (p[1] == None or p[3] == None): p[0] = None
        else: p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]
def p_variableDeclarationPartBody_error(p):
    """
    variableDeclarationPartBody : variableDeclarationPartBody error
                                | variableDeclarationPartBody SEMICOLON error
                                | error
    """
    popDiagnostic()
    t = None
    if (len(p) == 2): t = p[1]
    elif (len(p) == 3): t = p[2]
    else: t = p[3]

    syn_error(t, DiagnosticType.INVALID_VARIABLE, { "value": t.value })

def p_variableDeclaration(p):
    """
    variableDeclaration : variableDeclarationHead COLON type
    """
    p[0] = ast.VariableDeclarationNode(p[1], p[3]).setStartTokenPos(p[1][0].pos).setEndTokenPos(p[3].pos)
    
def p_variableDeclarationHead(p):
    """
    variableDeclarationHead : variableDeclarationHead COMMA IDENTIFIER
                            | IDENTIFIER
    """
    if (len(p) == 4): p[0] = p[1] + [ast.IdentifierNode(p[3]).setTokenPos(p.slice[3].pos)]
    else: p[0] = [ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos)]
#endregion ------- Variable Declaration -------
#endregion -------------- Block --------------
#endregion ============== Section 3 ==============

#region ============== Section 11 ==============
def p_procedureAndFunctionDefinitionPart(p):
    """
    procedureAndFunctionDefinitionPart : procedureAndFunctionDefinitionPartList SEMICOLON
                                       | empty
    """
    if (p[1] != None): p[0] = ast.ProcedureAndFunctionDeclarationPartNode(p[1]) \
        .setStartTokenPos(p[1][0].pos).setEndTokenPos(p.slice[2].pos)

def p_procedureAndFunctionDefinitionPartList(p):
    """
    procedureAndFunctionDefinitionPartList : procedureAndFunctionDefinitionPartList SEMICOLON procedureAndFunctionDefinition
                                           | procedureAndFunctionDefinition
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_procedureAndFunctionDefinition(p):
    """
    procedureAndFunctionDefinition : procedureOrFunctionHeading SEMICOLON procedureOrFunctionBody
    """
    if (p[1].ist(ast.ProcedureHeadingNode)): p[0] = ast.ProcedureDeclarationNode(p[1], p[3]) \
        .setStartTokenPos(p[1].pos).setEndTokenPos(p[3].pos)
    else: p[0] = ast.FunctionDeclarationNode(p[1], p[3]).setStartTokenPos(p[1].pos).setEndTokenPos(p[3].pos)

def p_procedureOrFunctionHeading(p):
    """
    procedureOrFunctionHeading : procedureHeading
                               | functionHeading
    """
    p[0] = p[1]

def p_procedureOrFunctionBody(p):
    """
    procedureOrFunctionBody : block
                            | directive
    """
    p[0] = p[1]

# Section 11.A
#region -------------- Procedure --------------
def p_procedureHeading(p):
    """
    procedureHeading : KW_PROCEDURE IDENTIFIER procedureHeadingParams
    """
    p[0] = ast.ProcedureHeadingNode(p[2], p[3]).setStartTokenPos(p.slice[1].pos)
    if (p[3] != None): p[0].setEndTokenPos(p[3][-1].pos)
    else: p[0].setEndTokenPos(p.slice[2].pos)

def p_procedureHeadingParams(p):
    """
    procedureHeadingParams : formalParameterList
    """
                        #    | empty
    p[0] = p[1] 
#endregion  -------------- Procedure --------------

#region -------------- Function --------------
def p_functionHeading(p):
    """
    functionHeading : KW_FUNCTION IDENTIFIER functionHeadingTail
    """
    (params, rettype) = p[3]
    p[0] = ast.FunctionHeadingNode(p[2], params, rettype).setStartTokenPos(p.slice[1].pos)
    if (p[3] != None): p[0].setEndTokenPos(p[3][-1].pos)
    else: p[0].setEndTokenPos(p.slice[2].pos)

def p_functionHeadingParams(p):
    """
    functionHeadingParams : formalParameterList
    """
                        #   | empty
    p[0] = p[1]

def p_functionHeadingTail(p):
    """
    functionHeadingTail : functionHeadingParams COLON IDENTIFIER
                        | empty
    """
    if (len(p) == 4): p[0] = (p[1], ast.TypeIdentifierNode(ast.IdentifierNode(p[3]).setTokenPos(p.slice[3].pos)))
    else: p[0] = (None, None)

#endregion  -------------- Function --------------

#region ------- Section R11.3.1 -------
def p_formalParameterList(p):
    """
    formalParameterList : LPAREN formalParameterListBody RPAREN
                        | empty
    """
    if (len(p) == 4): p[0] = p[2]
    else: p[0] = None
def p_formalParameterList_error(p):
    """
    formalParameterList : LPAREN error RPAREN
    """
    popDiagnostic()
    t = p[2]
    syn_error(t, DiagnosticType.UNEXPECTED_TOKEN, { "token": t.type })

def p_formalParameterListBody(p):
    """
    formalParameterListBody : formalParameterListBody SEMICOLON formalParameterSection
                            | formalParameterSection
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_formalParameterSection(p):
    """
    formalParameterSection : variableParameterSpecification
                           | valueParameterSpecification
                           | procedureOrFunctionHeading
    """
    p[0] = p[1]

def p_variableParameterSpecification(p):
    """
    variableParameterSpecification : KW_VAR valueParameterSpecification
    """
    p[0] = p[2].setVariable(True).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[2].pos)

def p_valueParameterSpecification(p):
    """
    valueParameterSpecification : bt_GENERIC identifierList COLON formalParameterSpecificationBody
    """
    # p[0] = ast.ParameterSpecificationNode(p[1], p[3]).setStartTokenPos(p[1][0].pos).setEndTokenPos(p[3].pos)
    p[0] = ast.ParameterSpecificationNode(p[2], p[4]) \
        .setStartTokenPos(p.parser.backtracks["GENERIC"].pos).setEndTokenPos(p[4].pos)

def p_identifierList(p):
    """
    identifierList : identifierList COMMA IDENTIFIER
                   | IDENTIFIER
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_formalParameterSpecificationBody(p):
    """
    formalParameterSpecificationBody : IDENTIFIER
                                     | conformantArraySchema
    """
    if (isinstance(p[1], ast.Node)): p[0] = p[1]
    else: p[0] = ast.TypeIdentifierNode(ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos))

def p_conformantArraySchema(p):
    """
    conformantArraySchema : packedConformantArraySchema
                          | unpackedConformantArraySchema
    """
    p[0] = p[1]

def p_packedConformantArraySchema(p):
    """
    packedConformantArraySchema : KW_PACKED KW_ARRAY LSBRACKET indexTypeSpecification RSBRACKET KW_OF IDENTIFIER
    """
    ast.PackedConformantArraySchemaNode(p[4], p[7]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[7].pos)

def p_unpackedConformantArraySchema(p):
    """
    unpackedConformantArraySchema : KW_ARRAY LSBRACKET indexTypeSpecification RSBRACKET KW_OF IDENTIFIER
    """
    p[0] = ast.UnpackedConformantArraySchemaNode(p[3], p[6]) \
        .setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[6].pos)

def p_indexTypeSpecificationList(p):
    """
    indexTypeSpecificationList : indexTypeSpecificationList SEMICOLON indexTypeSpecification
                               | indexTypeSpecification
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_indexTypeSpecification(p):
    """
    indexTypeSpecification : IDENTIFIER OP_RANGE IDENTIFIER COLON IDENTIFIER
    """
    p[0] = ast.IndexTypeSpecificationNode(p[1], p[3], p[5]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[5].pos)
#endregion ------- Section R11.3.1 -------

#region ------- Section R11.3.2 -------
def p_actualParameterList(p):
    """
    actualParameterList : LPAREN actualParameterListBody RPAREN
    """
    p[0] = ast.ActualParameterListNode(p[2]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[3].pos)

def p_actualParameterListBody(p):
    """
    actualParameterListBody : actualParameterListBody COMMA actualParameter
                            | actualParameter
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

# Here, all would be fine if PLY WASN'T A FUCKING MORON AND JUST FOLLOWED THE FUCKING DEFINITION ORDER, WHICH IS THE 
# PATH OF LEAST COST, YET THIS MOTHERFUCKER DECIDES TO GO TO HELL AND BACK TO REDUCE THE EXPRESSION AND THE VARIABLE
# INSTEAD OF THE IDENTIFIER THAT IS *RIGHT FUCKING THERE*.
def p_actualParameter(p):
    # """
    # actualParameter : IDENTIFIER
    #                 | variable
    #                 | expression
    # """
    """
    actualParameter : expression
    """
                    # | variable
    if (isinstance(p[1], ast.Node)): p[0] = p[1]
    else: p[0] = ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos)
#endregion ------- Section R11.3.2 -------
#endregion ============== Section 11 ==============

#region ============== Section R7 ==============
def p_variable(p):
    """
    variable : entireVariable
             | componentVariable
             | identifiedVariable
    """
            #  | bufferVariable
    p[0] = p[1]

def p_entireVariable(p):
    """
    entireVariable : IDENTIFIER
    """
    p[0] = ast.EntireVariableNode(p[1]).setTokenPos(p.slice[1].pos)

#region ------- Section 7.2 -------
def p_arrayVariable(p):
    """
    arrayVariable : variable
    """
    p[0] = p[1].setStaticType(ast.VariableStaticType.VARIABLE_ST_ARRAY)

def p_componentVariable(p):
    """
    componentVariable : indexedVariable
                      | fieldDesignator
    """
    p[0] = p[1]

def p_indexedVariable(p):
    """
    indexedVariable : arrayVariable LSBRACKET ordinalExpression indexedVariableTail
    """
    p[0] = ast.IndexedVariableNode(p[1], p[3], p[4] if isinstance(p[4], ast.Node) else None) \
        .setStartTokenPos(p[1].pos).setEndTokenPos(p[4].pos)

def p_indexedVariableTail(p):
    """
    indexedVariableTail : COMMA ordinalExpression RSBRACKET
                        | RSBRACKET
    """
    if (len(p) == 4): p[0] = p[2].setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[3].pos)
    else: p[0] = p.slice[1]

# PLY won't reach IDENTIFIER here no matter the fuckery I do, so I gave up. Diverges from spec in terms that 
# "variable DOT" is no longer optional. Use IdentifiedVariable if needed.
def p_fieldDesignator(p):
    """
    fieldDesignator : variable DOT IDENTIFIER
    """
                    # | IDENTIFIER
    if (len(p) == 4): 
        p[0] = ast.FieldDesignatorNode(p[1], ast.IdentifierNode(p[3]).setTokenPos(p.slice[3].pos)) \
            .setStartTokenPos(p[1].pos).setEndTokenPos(p.slice[3].pos)
    # else: 
    #     p[0] = ast.FieldDesignatorNode(p[1], None).setTokenPos(p.slice[1].pos)
        
#endregion ------- Section 7.2 -------

#region ------- Section 7.3 -------
def p_identifiedVariable(p):
    """
    identifiedVariable : variable OP_UPARROW
    """
    p[0] = ast.IdentifiedVariableNode(p[1]).setStartTokenPos(p[1].pos).setEndTokenPos(p.slice[2].pos)
#endregion ------- Section 7.3 -------

#region ------- Section 7.4 -------
# NOTE: Removed for the time being due to limitations on the target architecture.
# def p_bufferVariable(p):
#     """
#     bufferVariable : variable OP_UPARROW
#     """
#endregion ------- Section 7.4 -------
#endregion ============== Section R7 ==============

#region ============== Section R8 ==============
# # # # Prof rangel shit:
# # ExprBool : Expr
# #      | Expr OpRel Expr
# # OpRel : EQ | NE | LT | LE | GT |GE
# # Expr : Termo  
# #    | Expr OpAd Termo
# # Termo : Fator
# #    | Termo OpMul Fator
# # OpAd : MAIS | MENOS | OU
# # OpMul : VEZES | DIV | AND
# # Fator : Const
# #    | Var
# #    | "(" ExprBool ")"
# #    | FuncCall
# # Const : INT | REAL | STRING
# # Var  : ID | ID "[" Expr "]"
# # FuncCall : ID "(" Args ")"

def p_expression(p):
    """
    expression : simpleExpression expressionTail
    """
    tail = p[2]
    if (tail == None): p[0] = p[1]
    else: p[0] = ast.ExpressionNode(p[1], tail[0], tail[1]).setStartTokenPos(p[1].pos).setEndTokenPos(tail[1].pos)

def p_expressionTail(p):
    """
    expressionTail : relationalOperator simpleExpression
                   | empty
    """
    if (p[1] == None): p[0] = None
    else: p[0] = (p[1], p[2])

def p_sign(p):
    """
    sign : OP_PLUS 
         | OP_MINUS
    """
    match (p.slice[1].type):
        case "OP_PLUS":  p[0] = ast.OpNode(ast.OpKind.OP_ADD).setTokenPos(p.slice[1].pos)
        case "OP_MINUS": p[0] = ast.OpNode(ast.OpKind.OP_SUB).setTokenPos(p.slice[1].pos)

def p_addingOperator(p):
    """
    addingOperator : OP_PLUS
                   | OP_MINUS
                   | KW_OR
    """
    match (p.slice[1].type):
        case "OP_PLUS":  p[0] = ast.OpNode(ast.OpKind.OP_ADD).setTokenPos(p.slice[1].pos)
        case "OP_MINUS": p[0] = ast.OpNode(ast.OpKind.OP_SUB).setTokenPos(p.slice[1].pos)
        case "KW_OR":    p[0] = ast.OpNode(ast.OpKind.OP_OR).setTokenPos(p.slice[1].pos)

def p_multiplyingOperator(p):
    """
    multiplyingOperator : OP_MULT
                        | OP_DIV
                        | KW_DIV
                        | KW_MOD
                        | KW_AND
    """
    match (p.slice[1].type):
        case "OP_MULT": p[0] = ast.OpNode(ast.OpKind.OP_MUL).setTokenPos(p.slice[1].pos)
        case "OP_DIV":  p[0] = ast.OpNode(ast.OpKind.OP_DIV).setTokenPos(p.slice[1].pos)
        case "KW_DIV":  p[0] = ast.OpNode(ast.OpKind.OP_DIV).setTokenPos(p.slice[1].pos)
        case "KW_MOD":  p[0] = ast.OpNode(ast.OpKind.OP_MOD).setTokenPos(p.slice[1].pos)
        case "KW_AND":  p[0] = ast.OpNode(ast.OpKind.OP_AND).setTokenPos(p.slice[1].pos)

def p_relationalOperator(p):
    """
    relationalOperator : OP_EQ
                       | OP_NEQ
                       | OP_LT
                       | OP_LTE
                       | OP_GT
                       | OP_GTE
                       | KW_IN
    """
    match (p.slice[1].type):
        case "OP_EQ":  p[0] = ast.OpNode(ast.OpKind.OP_EQ).setTokenPos(p.slice[1].pos)
        case "OP_NEQ": p[0] = ast.OpNode(ast.OpKind.OP_NEQ).setTokenPos(p.slice[1].pos)
        case "OP_LT":  p[0] = ast.OpNode(ast.OpKind.OP_LT).setTokenPos(p.slice[1].pos)
        case "OP_LTE": p[0] = ast.OpNode(ast.OpKind.OP_LTE).setTokenPos(p.slice[1].pos)
        case "OP_GT":  p[0] = ast.OpNode(ast.OpKind.OP_GT).setTokenPos(p.slice[1].pos)
        case "OP_GTE": p[0] = ast.OpNode(ast.OpKind.OP_GTE).setTokenPos(p.slice[1].pos)
        case "KW_IN":  p[0] = ast.OpNode(ast.OpKind.OP_IN).setTokenPos(p.slice[1].pos)

def p_simpleExpression(p):
    """
    simpleExpression : simpleExpressionBody
                     | sign simpleExpressionBody
    """
    if (p[1].ist(ast.OpKind)):
        p[0] = ast.ExpressionNode(None, p[1], p[2]).setKind(ast.ExpressionKind.EXP_UNARY) \
            .setStartTokenPos(p[1].pos).setEndTokenPos(p[2].pos)
    else: p[0] = p[1]

def p_simpleExpressionBody(p):
    """
    simpleExpressionBody : simpleExpressionBody addingOperator term
                         | term
    """
    if (len(p) == 4): p[0] = ast.ExpressionNode(p[1], p[2], p[3]).setStartTokenPos(p[1].pos).setEndTokenPos(p[3].pos)
    else: p[0] = p[1]

def p_term(p):
    """
    term : term multiplyingOperator factor
         | factor
    """
    if (len(p) == 4): p[0] = ast.ExpressionNode(p[1], p[2], p[3]).setStartTokenPos(p[1].pos).setEndTokenPos(p[3].pos)
    else: p[0] = p[1]

def p_factor(p):
    """
    factor : unsignedConstant
           | setConstructor
           | factorVariableFunctionDesignator
           | KW_NOT factor
           | LPAREN expression RPAREN
    """
        #    | variable
        #    | functionDesignator
        #    | IDENTIFIER
    if (isinstance(p[1], ast.Node)): 
        if (p[1].ist(ast.UnsignedConstantNode)): p[0] = ast.ExpressionLikeNode(p[1])
        else: p[0] = p[1]
    else:
        t = p.slice[1]
        match (t.type):
            case "IDENTIFIER": p[0] = ast.ExpressionLikeNode(ast.IdentifierNode(p[1]).setTokenPos(t.pos))
            case "KW_NOT": p[0] = p[2]
            case "LPAREN": p[0] = p[2]

#region ------- Set Constructor -------
def p_setConstructor(p):
    """
    setConstructor : LSBRACKET setConstructorBody RSBRACKET
    """
    p[0] = ast.SetConstructorNode(p[2]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[3].pos)

def p_setConstructorBody(p):
    """
    setConstructorBody : setConstructorBodyList
                       | empty
    """
    p[0] = p[1]

def p_setConstructorBodyList(p):
    """
    setConstructorBodyList : setConstructorBodyList COMMA elementDescription
                           | elementDescription
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_elementDescription(p):
    """
    elementDescription : ordinalExpression elementDescriptionTail
    """
    p[0] = ast.ElementDescriptionNode(p[1], p[2]).setStartTokenPos(p[1].pos)
    if (p[2] != None): p[0].setEndTokenPos(p[2].pos)

def p_elementDescriptionTail(p):
    """
    elementDescriptionTail : OP_RANGE expression
                           | empty
    """
    if (p[1] == None): p[0] = p[1]
    else: p[0] = p[2]
#endregion ------- Set Constructor -------

# def p_functionDesignator(p):
#     """
#     functionDesignator : IDENTIFIER functionDesignatorTail
#     """
#     p[0] = ast.FunctionDesignatorNode(ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos), p[2]) \
#         .setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[2].pos)

# This rule is required because PLY.YACC is a fucking moron and, once again, doesn't respect the defined order.
def p_factorVariableFunctionDesignator(p):
    """
    factorVariableFunctionDesignator : variable functionDesignatorTail
    """
    if (p[2] != None):
        if (not p[1].ist(ast.EntireVariableNode)): raise SyntaxError()
        else: p[0] = ast.FunctionDesignatorNode(p[1].toIdentifierNode(), p[2]) \
            .setStartTokenPos(p[1].pos).setEndTokenPos(p[2].pos)
    else:
        p[0] = ast.ExpressionLikeNode(p[1]).setTokenPos(p[1].pos)
    # p[0] = ast.FunctionDesignatorNode(ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos), p[2]) \
    #     .setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[2].pos)

def p_functionDesignatorTail(p):
    """
    functionDesignatorTail : actualParameterList
                           | empty
    """
    p[0] = p[1]

def p_ordinalExpression(p):
    """
    ordinalExpression : expression
    """
    p[0] = p[1].setStaticType(ast.ExpressionStaticType.EXP_ORDINAL)

def p_booleanExpression(p):
    """
    booleanExpression : expression
    """
    p[0] = p[1].setStaticType(ast.ExpressionStaticType.EXP_BOOLEAN)

def p_integerExpression(p):
    """
    integerExpression : expression
    """
    p[0] = p[1].setStaticType(ast.ExpressionStaticType.EXP_INTEGER)
#endregion ============== Section R8 ==============

#region ============== Section R9 ==============
def p_statementPart(p):
    """
    statementPart : compoundStatement
    """
    p[0] = p[1]

def p_compoundStatement(p):
    """
    compoundStatement : KW_BEGIN statementSequence KW_END
    """
    # In this part, a trailing semicolon IS allowed, however, the grammar will yield an empty element which will not
    # be present if the trailing semicolon is ommited. If the last element is None, pop it.
    if (p[2][-1] == None): p[2].pop()
    p[0] = ast.CompoundStatementNode(p[2]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[3].pos)
def p_compoundStatement_error(p):
    """
    compoundStatement : KW_BEGIN error KW_END
    """
    # popDiagnostic()
    # t = p[2]
    # syn_error(t, DiagnosticType.UNEXPECTED_TOKEN, { "token": t.type })

def p_statementSequence(p):
    """
    statementSequence : statementSequence SEMICOLON statement
                      | statement
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    # elif (p[1] == None): p[0] = [None]
    else: p[0] = [p[1]]

# def p_statementSequence_error(p):
#     """
#     statementSequence : statementSequence error
#     """
#     # Here I'm being a cheeky little bastard and aglutinating any error that occurs after a Statement Sequence, even
#     # if it doesn't necessarily belong to it, but it's easier to deal with.
#     p[0] = [None]

# def p_statement(p):
#     """
#     statement : statementLabel statementBody
#     """
#     if (p[2] != None): 
#         p[2].setTokenPos(p[2].pos)
#         if (p[1] != None): p[2].setLabel(
#             ast.NumberNode(p[1].value, ast.NumberKind.UNSIGNED_INTEGER).setTokenPos(p[1].pos)
#         )
        
#     p[0] = p[2]

# Here, the statement definition has to be split between it's matched and unmatched versions in order to resolve the
# dangling else problem that occurs on the ifStatement production below.
def p_statement(p):
    """
    statement : matchedStatement
              | unmatchedStatement
    """
    p[0] = p[1]

def p_matchedStatement(p):
    """
    matchedStatement : statementLabel matchedStatementBody
    """
    if (p[2] != None): 
        p[2].setTokenPos(p[2].pos)
        if (p[1] != None): p[2].setLabel(
            ast.NumberNode(p[1].value, ast.NumberKind.UNSIGNED_INTEGER).setTokenPos(p[1].pos)
        )
        
    p[0] = p[2]

def p_matchedStatementBody(p):
    """
    matchedStatementBody : simpleStatement
                         | matchedStructuredStatement
    """
    p[0] = p[1]

def p_unmatchedStatement(p):
    """
    unmatchedStatement : statementLabel unmatchedStatementBody
    """
    if (p[2] != None): 
        p[2].setTokenPos(p[2].pos)
        if (p[1] != None): p[2].setLabel(
            ast.NumberNode(p[1].value, ast.NumberKind.UNSIGNED_INTEGER).setTokenPos(p[1].pos)
        )
        
    p[0] = p[2]

def p_unmatchedStatementBody(p):
    """
    unmatchedStatementBody : unmatchedConditionalStatement
    """
    p[0] = p[1]

def p_statementLabel(p):
    """
    statementLabel : UNSIGNED_INTEGER COLON
                   | empty
    """
    if (p[1] != None): p[0] = p.slice[1]
    else: p[0] = p[1]

# def p_statementBody(p):
#     """
#     statementBody : simpleStatement
#                   | structuredStatement
#     """
#                 #   | empty
#     p[0] = p[1]

#region -------------- Section 9.1 --------------
def p_simpleStatement(p):
    """
    simpleStatement : assignmentStatement
                    | procedureStatement
                    | gotoStatement
                    | empty
    """
    p[0] = p[1]

def p_assignmentStatement(p):
    """
    assignmentStatement : assignmentStatementHead OP_ASSIGN expression
    """
    p[0] = ast.AssignmentStatementNode(p[1], p[3]).setStartTokenPos(p[1].pos).setEndTokenPos(p[3].pos)

def p_assignmentStatementHead(p):
    """
    assignmentStatementHead : variable
    """
                            # | IDENTIFIER
    if (isinstance(p[1], ast.Node)): p[0] = p[1]
    else: p[0] = ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos)

def p_procedureStatement(p):
    """
    procedureStatement : IDENTIFIER procedureStatementTail
    """
    p[0] = ast.ProcedureStatementNode(ast.IdentifierNode(p[1]).setTokenPos(p.slice[1].pos), p[2]) \
        .setStartTokenPos(p.slice[1].pos)
    if (p[2] != None): p[0].setEndTokenPos(p[2].pos)

# NOTE: WriteParameterList ommited due to the behavior on the File Type being ommited on this implementation.
def p_procedureStatementTail(p):
    """
    procedureStatementTail : actualParameterList
                           | empty
    """
    p[0] = p[1]

def p_gotoStatement(p):
    """
    gotoStatement : KW_GOTO UNSIGNED_INTEGER
    """
    p[0] = ast.GotoStatementNode(ast.NumberNode(p[2], ast.NumberKind.UNSIGNED_INTEGER).setTokenPos(p.slice[2].pos)) \
        .setStartTokenPos(p.slice[1].pos).setEndTokenPos(p.slice[2].pos)
#endregion -------------- Section 9.1 --------------

#region -------------- Section 9.2 --------------
# def p_structuredStatement(p):
#     """
#     structuredStatement : compoundStatement
#                         | conditionalStatement
#                         | repetitiveStatement
#                         | withStatement
#     """
#     p[0] = p[1]
def p_matchedStructuredStatement(p):
    """
    matchedStructuredStatement : compoundStatement
                               | matchedConditionalStatement
                               | repetitiveStatement
                               | withStatement
    """
    p[0] = p[1]

#region ------- Section 9.2.2 -------
# def p_conditionalStatement(p):
#     """
#     conditionalStatement : ifStatement
#                          | caseStatement
#     """
#     p[0] = p[1]

def p_matchedConditionalStatement(p):
    """
    matchedConditionalStatement : matchedIfStatement
                                | caseStatement
    """
    p[0] = p[1]

def p_unmatchedConditionalStatement(p):
    """
    unmatchedConditionalStatement : unmatchedIfStatement
    """
    p[0] = p[1]

# def p_ifStatement(p):
#     """
#     ifStatement : KW_IF booleanExpression KW_THEN statement ifStatementTail
#     """
#     p[0] = ast.ConditionalStatementNode(p[2], p[4], p[5]).setStartTokenPos(p.slice[1].pos)
#     if (p[5] != None): p[0].setEndTokenPos(p[5].pos)
#     else: p[0].setEndTokenPos(p[4].pos)

# def p_ifStatementTail(p):
#     """
#     ifStatementTail : KW_ELSE statement
#                     | empty
#     """
#     if (p[1] == None): p[0] = None
#     else: p[0] = p[2].setStartTokenPos(p.slice[1].pos)

def p_matchedIfStatement(p):
    """
    matchedIfStatement : KW_IF booleanExpression KW_THEN matchedStatement KW_ELSE matchedStatement
    """
    p[0] = ast.ConditionalStatementNode(p[2], p[4], p[6]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[6].pos)

def p_unmatchedIfStatement(p):
    """
    unmatchedIfStatement : KW_IF booleanExpression KW_THEN statement
                         | KW_IF booleanExpression KW_THEN matchedStatement KW_ELSE unmatchedStatement
    """
    if (len(p) == 5):
        p[0] = ast.ConditionalStatementNode(p[2], p[4], None).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[4].pos)
    else:
        p[0] = ast.ConditionalStatementNode(p[2], p[4], p[6]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[6].pos)

def p_caseStatement(p):
    """
    caseStatement : KW_CASE ordinalExpression KW_OF caseStatementBody caseStatementTail
    """
    p[0] = ast.CaseStatementNode(p[2], p[4]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[5].pos)
def p_caseStatement_error(p):
    """
    caseStatement : KW_CASE error KW_OF caseStatementBody caseStatementTail
                  | KW_CASE ordinalExpression KW_OF error caseStatementTail
    """
    t = None
    if (p.slice[2].type == "error"): t = p[2]
    else: t = p[4]

    popDiagnostic()
    syn_error(t, DiagnosticType.UNEXPECTED_TOKEN, { "token": t.type })

def p_caseStatementBody(p):
    """
    caseStatementBody : caseStatementBody SEMICOLON case
                      | case
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_case(p):
    """
    case : caseHeading COLON statement
    """
    p[0] = ast.CaseNode(p[1], p[3]).setStartTokenPos(p[1][0].pos).setEndTokenPos(p[3].pos)
def p_case_error(p):
    """
    case : caseHeading COLON error
    """
    # Same diagnostic, so there's no need to pop and re-append what will end up as the exact same thing.
    # popDiagnostic()
    # syn_error(p[3], DiagnosticType.UNEXPECTED_TOKEN, { "token": p[3].type })

def p_caseHeading(p):
    """
    caseHeading : caseHeading COMMA constElem
                | constElem
    """
    if (len(p) == 4): p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_caseStatementTail(p):
    """
    caseStatementTail : SEMICOLON KW_END
                      | KW_END
    """
    p[0] = p.slice[-1]
#endregion ------- Section 9.2.2 -------

#region ------- Section 9.2.3 -------
def p_repetitiveStatement(p):
    """
    repetitiveStatement : whileStatement
                        | repeatStatement
                        | forStatement
    """
    p[0] = p[1]

def p_whileStatement(p):
    """
    whileStatement : KW_WHILE booleanExpression KW_DO statement
    """
    p[0] = ast.WhileStatementNode(p[2], p[4]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[4].pos)

def p_repeatStatement(p):
    """
    repeatStatement : KW_REPEAT statementSequence KW_UNTIL booleanExpression
    """
    # In this part, a trailing semicolon IS allowed, however, the grammar will yield an empty element which will not
    # be present if the trailing semicolon is ommited. If the last element is None, pop it.
    if (p[2][-1] == None): p[2].pop()
    p[0] = ast.RepeatStatementNode(p[4], p[2]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[4].pos)

def p_forStatement(p):
    """
    forStatement : KW_FOR IDENTIFIER OP_ASSIGN ordinalExpression forStatementTail
    """
    tail = p[5]
    if (tail == None): return None

    p[0] = ast.ForStatementNode(
        ast.IdentifierNode(p[2]).setTokenPos(p.slice[2].pos), 
        p[4], 
        ast.ForTraversalMode.fromKeyword(tail[0].type),
        tail[1], 
        tail[2]
    ).setStartTokenPos(p.slice[1].pos).setEndTokenPos(tail[0].pos)
def p_forStatement_error(p):
    """
    forStatement : KW_FOR error OP_ASSIGN ordinalExpression forStatementTail
                 | KW_FOR IDENTIFIER OP_ASSIGN error forStatementTail
    """
    # t = None
    # if (p.slice[2].type == "error"): t = p[2]
    # else: t = p[4]

    # popDiagnostic()
    # syn_error(t, DiagnosticType.UNEXPECTED_TOKEN, { "token": t.type })

def p_forStatementTail(p):
    """
    forStatementTail : KW_TO ordinalExpression KW_DO statement
                     | KW_DOWNTO ordinalExpression KW_DO statement
    """
    p[0] = (p.slice[1], p[2], p[4])
def p_forStatementTail_error(p):
    """
    forStatementTail : KW_TO error KW_DO statement
                     | KW_DOWNTO error KW_DO statement
                     | KW_TO ordinalExpression KW_DO error
                     | KW_DOWNTO ordinalExpression KW_DO error
    """
    pass
#endregion ------- Section 9.2.3 -------

#region ------- Section 9.2.4 -------
def p_withStatement(p):
    """
    withStatement : KW_WITH recordVariableList KW_DO statement
    """
    p[0] = ast.WithStatementNode(p[2], p[4]).setStartTokenPos(p.slice[1].pos).setEndTokenPos(p[4].pos)
def p_withStatement_error(p):
    """
    withStatement : KW_WITH error KW_DO statement
                  | KW_WITH recordVariableList KW_DO error
    """
    pass

def p_recordVariableList(p):
    """
    recordVariableList : recordVariableList COMMA variable
                       | variable
    """
    if (len(p) == 4): p[0] = p[1] + [p[3].setStaticType(ast.VariableStaticType.VARIABLE_ST_RECORD)]
    else: p[0] = [p[1].setStaticType(ast.VariableStaticType.VARIABLE_ST_RECORD)]
#endregion ------- Section 9.2.4 -------
#endregion -------------- Section 9.2 --------------
#endregion ============== Section R9 ==============

def p_empty(p):
    """
    empty :
    """
    pass

def p_error(t):
    print("ERR:", t)

    if t == None:
        # Here, I cheat by fetching the lexer directly, in order to get the last position the lexer has processed, due 
        #   to being unable to fetch it from the token, as it is None.
        diag = emitDiagnostic(
            lexer, 
            DiagnosticType.UNEXPECTED_EOF, 
            DiagnosticKind.ERROR, 
            {},
            TokenPos(lexer, lexer.lexpos, lexer.lexpos)
        )
        print(
            f"\x1b[31mSYNTAX ERROR @{lexer.lexpos}:" \
            f"\x1b[0m {diag.toString(lexer, emitMark = False, emitPos = False)}"
        )
    else:
        print("NERR:", t.lexpos, t.pos)
        syn_error(t, DiagnosticType.UNEXPECTED_TOKEN, { "token": t.type })

def syn_error(t, dType, dArgs):
    caller = getframeinfo(stack()[1][0])

    lex = getattr(t, "lexer", lexer)

    diag = emitDiagnostic(
            lex, 
            dType, 
            DiagnosticKind.ERROR, 
            dArgs,
            t.pos
    )
    print(
        f"\x1b[31m[{caller.filename}:{caller.lineno}] SYNTAX ERROR @{t.lexpos}:\x1b[0m" \
        f" {diag.toString(lex, emitMark = False, emitPos = False)}"
    )

#region ------- Diagnostics -------
# This function emits a syntatic diagnostic. Diagnostics are defined on the property "diagnostics" on the parser.
def emitDiagnostic(
    l, 
    dtype: DiagnosticType, 
    dkind: DiagnosticKind = DiagnosticKind.INFO,
    args = {}, 
    pos: TokenPos = None
):
    _pos = TokenPos(l) if pos == None else pos
    rcStartPos = _pos.start
    rcEndPos = _pos.end

    diag = Diagnostic(DiagnosticSource.SYNANAL, dtype, dkind, rcStartPos, rcEndPos, args)
    parser.diagnostics.append(diag)
    parser._diagnosticTrace.append(diag)

    return diag

# This function removes the latest diagnostic from the parser list. Used on resynchronization rules for more specialized
#   per-rule error handling.
def popDiagnostic():
    return parser.diagnostics.pop()
#endregion ------- Diagnostics -------

#region ------- Parser Utils -------
def advanceUntil(cond, p = None):
    if (p == None): p = parser

    tok = p.token()
    trace("Eval skip:", tok)
    while (tok != None):
        if cond(tok): 
            trace("Break")
            break
        trace("Skipping.")
        tok = p.token()

    # parser.errok()

def advanceUntilSemicolon():
    advanceUntil(lambda t: t.type == 'SEMICOLON')

def trace(*args):
    if (parser.options["verbose"]): print(*args)
#endregion ------- Parser Utils -------

parser = yacc.yacc()
parser.diagnostics = []
parser._diagnosticTrace = []
parser.options = {
    "verbose": True
}
parser.backtracks = {}

