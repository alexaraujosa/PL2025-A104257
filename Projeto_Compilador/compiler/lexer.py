from ply import lex
from enum import Enum, auto
from typing import Callable
from util.classUtil import externalinstancemethod
from .diag import Diagnostic, DiagnosticType, DiagnosticKind, DiagnosticSource

# Section 1.B 
#region ------- Keywords -------
# reserved = {
#     "and": "KW_AND",
#     "array": "KW_ARRAY",
#     "begin": "KW_BEGIN",
#     "case": "KW_CASE",
#     "const": "KW_CONST",
#     "div": "KW_DIV",
#     "do": "KW_DO",
#     "downto": "KW_DOWNTO",
#     "else": "KW_ELSE",
#     "end": "KW_END",
#     "file": "KW_FILE",
#     "for": "KW_FOR",
#     "function": "KW_FUNCTION",
#     "goto": "KW_GOTO",
#     "if": "KW_IF",
#     "in": "KW_IN",
#     "label": "KW_LABEL",
#     "mod": "KW_MOD",
#     "nil": "KW_NIL",
#     "not": "KW_NOT",
#     "of": "KW_OF",
#     "or": "KW_OR",
#     "packed": "KW_PACKED",
#     "procedure": "KW_PROCEDURE",
#     "program": "KW_PROGRAM",
#     "record": "KW_RECORD",
#     "repeat": "KW_REPEAT",
#     "set": "KW_SET",
#     "then": "KW_THEN",
#     "to": "KW_TO",
#     "type": "KW_TYPE",
#     "until": "KW_UNTIL",
#     "var": "KW_VAR",
#     "while": "KW_WHILE",
#     "with": "KW_WITH",
# }
#endregion ------- Keywords -------

tokens = [
    # Section 1.A
    "SEP",

    # Section 1.B 
    #region ------- Special Characters -------
    "OP_PLUS",     # +
    "OP_MINUS",    # -
    "OP_MULT",     # *
    "OP_DIV",      # /
    "DOT",         # .
    "COMMA",       # ,
    "COLON",       # :
    "SEMICOLON",   # ;
    "OP_EQ",       # =
    "OP_NEQ",      # <>
    "OP_LT",       # <
    "OP_LTE",      # <=
    "OP_GT",       # >
    "OP_GTE",      # >=
    "OP_ASSIGN", # :=
    "OP_RANGE",    # ..
    "OP_UPARROW",  # ↑ | @ | ^
    "LPAREN",      # (
    "RPAREN",      # )
    "LSBRACKET",   # [ | (.
    "RSBRACKET",   # ] | .)
    #endregion ------- Special Characters -------

    #region ------- Keywords -------
    "KW_AND",
    "KW_ARRAY",
    "KW_BEGIN",
    "KW_CASE",
    "KW_CONST",
    "KW_DIV",
    "KW_DO",
    "KW_DOWNTO",
    "KW_ELSE",
    "KW_END",
    "KW_FILE",
    "KW_FOR",
    "KW_FUNCTION",
    "KW_GOTO",
    "KW_IF",
    "KW_IN",
    "KW_LABEL",
    "KW_MOD",
    "KW_NIL",
    "KW_NOT",
    "KW_OF",
    "KW_OR",
    "KW_PACKED",
    "KW_PROCEDURE",
    "KW_PROGRAM",
    "KW_RECORD",
    "KW_REPEAT",
    "KW_SET",
    "KW_THEN",
    "KW_TO",
    "KW_TYPE",
    "KW_UNTIL",
    "KW_VAR",
    "KW_WHILE",
    "KW_WITH",
    #endregion ------- Keywords -------

    # Section 1.D
    # Hold specific global and local ordering constraints. See comment above their definition for more information.
    "UNSIGNED_REAL",
    "UNSIGNED_INTEGER",

    # Apparently, I hallucinated the fuck out of these two tokens, even though I could swear that I've seen them on the 
    # spec. What kind of Mandela Effect was this?
    # "SIGNED_REAL",
    # "SIGNED_INTEGER",
    
    "IDENTIFIER", # Section 1.C; Shadows Directive and possibly Label
    "STRING", # Section 1.E

    #  Section 1.A
    #   Comments do not appear in the token stream returned by the lexer.
    #   Comments are treated at lextime. If any errors are returned, they can be 
    #     accessed through the property "diagnostics" on the lexer.
    #region ------- Comment State -------
    "LBRACE",      # { | (*
    "RBRACE",      # } | *)
    "COMMENT_BODY",
    #endregion ------- Comment State -------
]
#  + list(reserved.values())

states = (
    ("comment", "exclusive"),
)

#region ------- Special Characters -------
t_OP_PLUS = r"\+"
t_OP_MINUS = r"-"
t_OP_MULT = r"\*"
t_OP_DIV = r"\\"
t_DOT = r"\."
t_COMMA = r","
t_COLON = r":"
t_SEMICOLON = r";"
t_OP_EQ = r"="
t_OP_NEQ = r"<>"
t_OP_LT = r"<"
t_OP_LTE = r"<="
t_OP_GT = r">"
t_OP_GTE = r">="
t_OP_ASSIGN = r":="
t_OP_RANGE = r"\.\."
t_OP_UPARROW = r"↑|@|\^"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LSBRACKET = r"\[|(?:\(\.)"
t_RSBRACKET = r"\]|(?:\.\))"
#endregion ------- Special Characters -------

# The following four tokens MUST be defined as functions, MUST be defined in the order UREAL -> UINT -> SREAL -> SINT
#   and MUST be defined before IDENFITIFER. Any other order will result in incorrect lexing.
# - If defined as constant regex strings, IDENTIFIER will take predecedence and will capture all numbers.
# - If IDENTIFIER is defined before the number tokens, the same will occur.
# - If INTEGERS are defined before REALS, the integer part of reals will be captured first and the 
#     decimal / exponential part will be captured as KW_DOT IDENTIFIER and IDENTIFIER, respectively.
def t_UNSIGNED_REAL(t):
    r"\d+(([.]\d*)?([eE][+-]?\d+)|[.]\d+([eE][+-]?\d+)?)"
    return t
def t_UNSIGNED_INTEGER(t):
    r"\d+"
    return t
# def t_SIGNED_REAL(t):
#     r"[+-]?\d+(([.]\d*)?([eE][+-]?\d+)|[.]\d+([eE][+-]?\d+)?)"
#     return t
# def t_SIGNED_INTEGER(t):
#     r"[+-]?\d+"
#     return t

#region ------- Section 1.B -------
# Reserved Keywords MUST be defined before IDENTIFIER, otherwise the later will capture all input before the former 
# have a chance to process the input.
def t_KW_AND(t):
    r"and\b"
    return t
def t_KW_ARRAY(t):
    r"array\b"
    return t
def t_KW_BEGIN(t):
    r"begin\b"
    return t
def t_KW_CASE(t):
    r"case\b"
    return t
def t_KW_CONST(t):
    r"const\b"
    return t
def t_KW_DIV(t):
    r"div\b"
    return t
def t_KW_DO(t):
    r"do\b"
    return t
def t_KW_DOWNTO(t):
    r"downto\b"
    return t
def t_KW_ELSE(t):
    r"else\b"
    return t
def t_KW_END(t):
    r"end\b"
    return t
def t_KW_FILE(t):
    r"file\b"
    return t
def t_KW_FOR(t):
    r"for\b"
    return t
def t_KW_FUNCTION(t):
    r"function\b"
    return t
def t_KW_GOTO(t):
    r"goto\b"
    return t
def t_KW_IF(t):
    r"if\b"
    return t
def t_KW_IN(t):
    r"in\b"
    return t
def t_KW_LABEL(t):
    r"label\b"
    return t
def t_KW_MOD(t):
    r"mod\b"
    return t
def t_KW_NIL(t):
    r"nil\b"
    return t
def t_KW_NOT(t):
    r"not\b"
    return t
def t_KW_OF(t):
    r"of\b"
    return t
def t_KW_OR(t):
    r"or\b"
    return t
def t_KW_PACKED(t):
    r"packed\b"
    return t
def t_KW_PROCEDURE(t):
    r"procedure\b"
    return t
def t_KW_PROGRAM(t):
    r"program\b"
    return t
def t_KW_RECORD(t):
    r"record\b"
    return t
def t_KW_REPEAT(t):
    r"repeat\b"
    return t
def t_KW_SET(t):
    r"set\b"
    return t
def t_KW_THEN(t):
    r"then\b"
    return t
def t_KW_TO(t):
    r"to\b"
    return t
def t_KW_TYPE(t):
    r"type\b"
    return t
def t_KW_UNTIL(t):
    r"until\b"
    return t
def t_KW_VAR(t):
    r"var\b"
    return t
def t_KW_WHILE(t):
    r"while\b"
    return t
def t_KW_WITH(t):
    r"with\b"
    return t
#region ------- Section 1.B -------

def t_IDENTIFIER(t): # Section 1.C
    r"[a-zA-Z0-9]+"
    # t.type = reserved.get(t.value, "IDENTIFIER")
    return t

# Section 1.E
# A string is defined as a sequence of characters enclosed between the character "'" (ASCII 39).
# The character "'" can be represented by escaping it using two "'" contiguously ("''"). Not to be confused with 
#   double quotes.
def t_STRING(t): 
    r"'(?P<content>(?:(?:'')|[^'])+)'"
    lines = t.value.count("\n")
    t.lexer.lineno += lines
    t.value = t.lexer.lexmatch.groupdict().get("content", t.value)
    return t

def t_SEP(t):
    r"[\n \t]+"

    # According to Section 1.A, whitespace is considered a symbol separator, but there is no distinction between them.
    #   Due to it's usefulness in other lexer operations, newlines will also trigger additional rules.
    #   Contiguous separators are collapsed under a single token. If there is a need to process which separators were
    #     captured, one should look at the value of the token.

    # for c in t.value:
    tvlen = len(t.value)
    for i in range(0, tvlen):
        c = t.value[i]
        if (c == "\n"):
            offset = t.lexer.lexpos - (tvlen - i)
            # print("NEWLINE", t.lexer.lineno, t.lexer.lexpos, offset, t.lexer._lastLineLexPos)
            t.lexer.lineno += 1
            t.lexer.lineLens.append(offset - t.lexer._lastLineLexPos)
            t.lexer._lastLineLexPos = offset

    return t

#region ============== Comment State ==============
# Used internally for diagnostics to distinguish the comment delimiters between MONO ('{', '}') and DUAL ('(*', '*)')
class CommentBraceKind(Enum):
    MONO = 1
    DUAL = 2

    @classmethod
    def getKind(cls, s):
        return cls.MONO if s == "{" or s == "}" else cls.DUAL

    def matches(self, s):
        return self._value_ == self.getKind(s)._value_

    def toString(self):
        return "}" if self == self.MONO else "*)"

# This rule stores metadata required during comment processing, which is cleaned up after the comment is closed:
#   - _braceKind: Indicates which Comment Brace Kind initiated the comment. Used only for diagnostics.
#   - _commentPos: Indicates the position at which the comment started. Used to retroactively recalculate the 
# line positions on the lexer (see lexer.lineLens).
# This rule changes the lexer state to "comment".
def t_LBRACE(t):
    r"\{|(?:\(\*)"
    t.lexer._braceKind = CommentBraceKind.getKind(t.value)
    t.lexer._commentPos = t.lexer.lexpos
    t.lexer.begin("comment")
    # return t

# The comment body is kept purely for internal usage, to calculate the line metadata retroactively. 
# It is not possible to access the comment body data beyond lextime.
def t_comment_COMMENT_BODY(t): # Section 1.A
    r"(?!(?:\*\))|})[\s\S]+?(?=\*\)|}|$)"
    t.lexer._commentBody = t.value

# This rule closes the comment and retroactively calculates the lengths of the lines within the comment body.
# Additionally, a diagnostic for mismatched comment delimiters is also evaluated here.
# The metadata defined by t_LBRACE is cleared at the end of this function and the lexer state is returned to INITIAL.
def t_comment_RBRACE(t):
    r"\}|(?:\*\))"

    cbLines = t.lexer._commentBody.split("\n")

    # If comment spans multiple lines, process them. Otherwise just advance the character counter.
    if (len(cbLines) != 1):
        for i in range(0, len(cbLines)):
            if (i == 0): # Comment probably started not at the beginning of the line. Handle it.
                t.lexer.lineLens.append(len(cbLines[i]) + (t.lexer._commentPos - t.lexer._lastLineLexPos) + 1)
                t.lexer._lastLineLexPos = t.lexer._commentPos + len(cbLines[i]) + 1
            elif (i == len(cbLines) - 1):
                # Early break. Let the t_ANY_NEWLINE rule handle the line.
                break
            else:
                t.lexer.lineLens.append(len(cbLines[i]) + 1)
                t.lexer._lastLineLexPos = t.lexer._lastLineLexPos + len(cbLines[i]) + 1
            
        t.lexer.lineno += len(cbLines) - 1
        t.lexer._lastLineLexPos += len(t.value) - 1
    else:
        t.lexer._lastLineLexPos = t.lexer._lastLineLexPos

    # According to Section 4, the definition of a comment defines that a comment is valid, even if it's delimiters
    #  are mismatched. For diagnostic purposes, mismatches are caught and reported, but do not halt.
    if (not t.lexer._braceKind.matches(t.value)): 
        comment_warn(
            t.lexer, 
            DiagnosticType.MISMATCHED_COMMENT_DELIM, 
            { "expected": t.lexer._braceKind.toString(), "actual": t.value }
        )

    t.lexer._braceKind = None
    t.lexer._commentPos = None
    t.lexer._commentBody = None
    t.lexer.begin("INITIAL")

# This rule triggers if a comment was opened, but never closed. When it is triggered, it will retroactively calculate
#   the line metadata captured by the comment body (in this specific case, the entire file after the comment starter),
#   mostly for diagnostic purposes.
# While this rule will emit an ERROR diagnostic, it is not a fatal error and the next phase can still attempt to process
#   the token stream without prejudice, as there might be a valid program before the comment.
def t_comment_eof(t):
    # Process caught lines for diagnostic
    cbLines = t.lexer._commentBody.split("\n")
    for i in range(0, len(cbLines)):
        if (i == 0): # Comment probably started not at the beginning of the line. Handle it.
            t.lexer.lineLens.append(len(cbLines[i]) + (t.lexer._commentPos - t.lexer._lastLineLexPos) + 1)
            t.lexer._lastLineLexPos = t.lexer._commentPos + len(cbLines[i]) + 1
        else:
            t.lexer.lineLens.append(len(cbLines[i]) + 1)
            t.lexer._lastLineLexPos = t.lexer._lastLineLexPos + len(cbLines[i]) + 1

    t.lexer.lineLens[-1] = t.lexer.lineLens[-1] + len(t.value)
    t.lexer.lineno += len(cbLines)
    t.lexer._lastLineLexPos += len(t.value)
    comment_error(t.lexer, DiagnosticType.NONTERMINATED_COMMENT, {})

t_comment_ignore = ""
def t_comment_error(t):
    diag = emitDiagnostic(t.lexer, DiagnosticType.UNEXPECTED_CHARACTER, DiagnosticKind.ERROR, { "character": repr(t.value[0]) })
    if (t.lexer.options["printDiags"]): 
    # if True:
        print(
            f"\x1b[31mLEXICAL ERROR #comment @{t.lexer.lexpos}:\x1b[0m " \
            f"{diag.toString(t.lexer, emitMark = False, emitPos = False)}"
        )
    t.lexer.skip(1)

def comment_warn(l, dType, dArgs = {}):
    diag = emitDiagnostic(
            l, 
            dType, 
            DiagnosticKind.WARN, 
            dArgs,
            l._commentPos,
            l.lexpos
    )
    if (l.options["printDiags"]): 
    # if True:
        print(f"\x1b[33mLEXICAL WARN @{l._commentPos}:\x1b[0m {diag.toString(l, emitMark = False, emitPos = False)}")

def comment_error(l, dType, dArgs = {}):
    diag = emitDiagnostic(
            l, 
            dType, 
            DiagnosticKind.ERROR, 
            dArgs,
            l._commentPos,
            l.lexpos
    )
    if (l.options["printDiags"]): 
    # if True:
        print(f"\x1b[31mLEXICAL ERROR @{l._commentPos}:\x1b[0m {diag.toString(l, emitMark = False, emitPos = False)}")
#endregion ============== Comment State ==============

# This rule triggers on any lexical error, usually an unrecognized character.
def t_error(t):
    diag = emitDiagnostic(t.lexer, DiagnosticType.UNEXPECTED_CHARACTER, DiagnosticKind.ERROR, { "character": repr(t.value[0]) })
    if (t.lexer.options["printDiags"]): 
        print(
            f"\x1b[31mLEXICAL ERROR @{t.lexer.lexpos}:\x1b[0m {diag.toString(t.lexer, emitMark = False, emitPos = False)}"
        )
    t.lexer.skip(1)

#region ------- Diagnostics -------
# This function emits a lexical diagnostic. Diagnostics are defined on the property "diagnostics" on the lexer.
def emitDiagnostic(
    l, 
    dtype: DiagnosticType, 
    dkind: DiagnosticKind = DiagnosticKind.INFO,
    args = {}, 
    dStartPos: int = None, 
    dEndPos: int = None
):
    tStartPos = dStartPos if (dStartPos != None) else l.lexpos
    tEndPos = dEndPos if (dEndPos != None) else l.lexpos
    rcStartPos = posToRowCol(l, tStartPos)
    rcEndPos = posToRowCol(l, tEndPos)

    diag = Diagnostic(DiagnosticSource.LEXER, dtype, dkind, rcStartPos, rcEndPos, args)
    l.diagnostics.append(diag)

    return diag
#endregion ------- Diagnostics -------

#region ------- Lexer Utils -------
class TokenPos:
    def __init__(self, l, startPos = 0, endPos = 0):
        self._startPos = startPos
        self._endPos = endPos
        
        (sr, sc) = posToRowCol(l, startPos)
        self.startRow = sr
        self.startCol = sc
        
        (er, ec) = posToRowCol(l, endPos)
        self.endRow = er
        self.endCol = ec

    def _getstart(self):
        return (self._startPos, self.startRow, self.startCol)
    start = property(_getstart)
    
    def _getend(self):
        return (self._endPos, self.endRow, self.endCol)
    end = property(_getend)

    def __repr__(self):
        return f"TokenPos[{self.startRow}:{self.startCol} - {self.endRow}:{self.endCol}]{{{self._startPos} - {self._endPos}}}"

def getCurLineLen(l):
    """
        Gets the length of the current line on the source text.
    """
    return l.lexpos - l._lastLineLexPos

def posToRowCol(l, pos):
    """
        Converts a global position offset on the source text to a (row, column) tuple.
        The row is 1-indexed, and the column is 0-indexed
    """
    acc = 0
    i = 0
    found = False
    for i in range(0, len(l.lineLens)):
        if (acc + l.lineLens[i] >= pos): 
            found = True
            break
        acc += l.lineLens[i]

    # If position is not on any of the previously recorded lines, it is on the current line. The line length hasn't
    #   been pushed to the lineLens list yet, so manually set it and get the position offset.
    if (not found):
        return (l.lineno, pos - l._lastLineLexPos)
    else:
        return (i + 1, pos - acc)
#endregion ------- Lexer Utils -------

#region ------- Lexer Build -------
lexer = lex.lex()
lexer._lastLineLexPos = 0
lexer.lineLens = []
lexer.diagnostics = []
lexer.options = {
    "printDiags": False
}
lexer._peek = None
lexer._cur = None
lexer._lastSep = None

# This function is attached to the lexer instance, and is used to finalize the lexical analysis phase.
# It adds the last buffered line length to the lineLens property and moves the character pointer to EOF.
# As of the time of writing this documentation, this results of this function are purely for diagnostic purposes.
@externalinstancemethod(lexer, "finish")
def _finish(self):
    self.lineLens.append(self.lexpos - self._lastLineLexPos)
    self._lastLineLexPos = self.lexpos

@externalinstancemethod(lexer, "getExtendedToken")
def _getExtendedToken(self):
    if (self._peek): 
        token = self._peek
        self._peek = None
    else:
        token = self.token() 

    while (True):
        if (token == None): break
        if (token.type == "SEP"): 
            token.pos = TokenPos(self, token.lexpos, token.lexpos + len(token.value))
            lexer._lastSep = token
            token = self.token()
            continue

        token.pos = TokenPos(self, token.lexpos, token.lexpos + len(token.value))
        # token.lexpos = self.lexpos
        break

    # print("GET FINAL:", token)
    self._cur = token
    return token

@externalinstancemethod(lexer, "peek")
def _peek(self):
    if (self._peek == None): self._peek = self.token()
    self._peek.pos = TokenPos(self, self._peek.lexpos, self._peek.lexpos + len(self._peek.value))
    return self._peek

@externalinstancemethod(lexer, "reset")
def _reset(self):
    self.lineno = 1
    self.lexpos = 0
    self._lastLineLexPos = 0
    self.lineLens = []
    self.diagnostics = []
#endregion ------- Lexer Build -------
