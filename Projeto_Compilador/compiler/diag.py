from enum import Enum, auto

class DiagnosticSource(Enum):
    LEXER   = auto(),
    SYNANAL = auto(),
    SEMANAL = auto(),
    OPTIM   = auto(),
    CODEGEN = auto()

class DiagnosticKind(Enum):
    INFO = auto()
    WARN = auto()
    ERROR = auto()
    CRITICAL = auto()

class DiagnosticType(Enum):
    #region -------------- Lexical Diagnostics --------------
    UNEXPECTED_CHARACTER = auto()
    NONTERMINATED_COMMENT = auto()
    MISMATCHED_COMMENT_DELIM = auto(),
    UNEXPECTED_EOF = auto(),
    #endregion -------------- Lexical Diagnostics --------------

    #region -------------- Syntatic Diagnostics --------------
    UNEXPECTED_TOKEN = auto(),
    INVALID_LABEL = auto(),
    # INVALID_CONSTANT_VALUE = auto(),
    INVALID_TYPE = auto(),
    UNTERMINATED_TYPE = auto(),
    MALTERMINATED_TYPE = auto(),
    RECORD_NO_FIXED_PART = auto(),
    INVALID_VARIABLE = auto(),
    #endregion -------------- Syntatic Diagnostics --------------

    #region -------------- Semantic Diagnostics --------------
    UNKNOWN_DIRECTIVE = auto(),
    UNDECLARED_LABEL = auto(),
    DUPLICATE_LABEL = auto(),
    UNUSED_LABEL = auto(),
    UNDECLARED_CONST = auto(),
    DUPLICATE_CONST = auto(),
    UNUSED_CONST = auto(),
    UNDECLARED_TYPE = auto(),
    DUPLICATE_TYPE = auto(),
    UNUSED_TYPE = auto(),

    ZERO_DIV = auto(),
    NAN_RESULT = auto(),
    INFINITY_RESULT = auto(),

    UNDEFINED_REFERENCE = auto(),
    TYPE_MISMATCH = auto(),
    DUPLICATE_IDENTIFIER = auto(),
    UNDECLARED_VARIABLE = auto(),
    INCOMPATIBLE_VARIABLE = auto(),
    UNDECLARED_ACTIVATABLE = auto(),
    #endregion -------------- Semantic Diagnostics --------------

DIAGNOSTIC_MESSAGES = {
    #region -------------- Lexical Diagnostics --------------
    DiagnosticType.UNEXPECTED_CHARACTER: "Unexpected character: {character}",
    DiagnosticType.NONTERMINATED_COMMENT: "Non-terminated comment",
    DiagnosticType.MISMATCHED_COMMENT_DELIM: "Mismatched comment delimiter. Expected '{expected}', got '{actual}'.",
    DiagnosticType.UNEXPECTED_EOF: "Unexpected End-Of-File.",
    #endregion -------------- Lexical Diagnostics --------------

    #region -------------- Syntatic Diagnostics --------------
    DiagnosticType.UNEXPECTED_TOKEN: "Unexpected token: {token}",
    DiagnosticType.INVALID_LABEL: "Invalid label: {value}",
    # DiagnosticType.INVALID_CONSTANT_VALUE: 
    #     "Invalid constant value type: {origType}. Expected NUMBER, IDENTIFIER or STRING.",
    DiagnosticType.INVALID_TYPE: "Invalid type: {value}",
    DiagnosticType.UNTERMINATED_TYPE: "Unterminated type.",
    DiagnosticType.MALTERMINATED_TYPE: "Type terminated with unknown separator. Expected '{expected}', got '{actual}'.",
    DiagnosticType.RECORD_NO_FIXED_PART: "Record must have a fixed part before a variant part.",
    DiagnosticType.INVALID_VARIABLE: "Invalid variable: {value}",
    #endregion -------------- Syntatic Diagnostics --------------

    #region -------------- Semantic Diagnostics --------------
    DiagnosticType.UNKNOWN_DIRECTIVE: "Unknown directive: {value}",
    DiagnosticType.UNDECLARED_LABEL: "Label not declared: {value}.",
    DiagnosticType.DUPLICATE_LABEL: "Label already declared: {value}.",
    DiagnosticType.UNUSED_LABEL: "Label not used: {value}.",
    DiagnosticType.UNDECLARED_CONST: "Constant not declared: {value}.",
    DiagnosticType.DUPLICATE_CONST: "Constant already declared: {value}.",
    DiagnosticType.UNUSED_CONST: "Constant not used: {value}.",
    DiagnosticType.UNDECLARED_TYPE: "Type not declared: {value}.",
    DiagnosticType.DUPLICATE_TYPE: "Type already declared: {value}.",
    DiagnosticType.UNUSED_TYPE: "Type not used: {value}.",

    DiagnosticType.ZERO_DIV: "Division by zero.",
    DiagnosticType.NAN_RESULT: "Operation resulted in NaN value.",
    DiagnosticType.INFINITY_RESULT: "Operation resulted in Infinity value.",

    DiagnosticType.UNDEFINED_REFERENCE: "Undefined reference: {value}.",
    DiagnosticType.TYPE_MISMATCH: "Type Mismatch. Expected {aType}, got {bType}.",
    DiagnosticType.DUPLICATE_IDENTIFIER: "Identifier already declared: {value}.",
    DiagnosticType.UNDECLARED_VARIABLE: "Variable not declared: {value}.",
    DiagnosticType.INCOMPATIBLE_VARIABLE: "Incompatible variable. Expected '{expected}', got '{actual}'.",
    DiagnosticType.UNDECLARED_ACTIVATABLE: "Procedure / Function not declared: {value}.",
    #endregion -------------- Semantic Diagnostics --------------
}

class Diagnostic:
    def __init__(self, 
        dSource: DiagnosticSource,
        dtype: DiagnosticType, 
        dkind: DiagnosticKind = DiagnosticKind.INFO, 
        dStartPos: (int, int, int) = (-1, -1, -1), 
        dEndPos: (int, int, int) = (-1, -1, -1), 
        args = {}
    ):
        self.msgTemplate = DIAGNOSTIC_MESSAGES[dtype]

        self.type = dtype
        self.kind = dkind
        self.source = dSource
        self.startPos = dStartPos
        self.endPos = dEndPos
        self.args = args
    
    def __repr__(self):
        return "".join([
            f"Diagnostic[S={self.source._name_},T={self.type._name_},K={self.kind._name_},"
            f"SP={self.startPos[1]}:{self.startPos[2]},EP={self.endPos[1]}:{self.endPos[2]},"
            f"A={repr(self.args)}]"
        ])

    def raw(self):
        return {
            "type": self.type,
            "kind": self.kind,
            "source": self.source,
            "startPos": self.startPos,
            "endPos": self.endPos,
            "args": self.args
        }

    def toString(self, l, **kwargs):
        doEmitMark = kwargs.get("emitMark", True)
        doEmitPos = kwargs.get("emitPos", True)
        doEmitSrc = kwargs.get("emitSource", False)

        ret = ""
        if (doEmitMark):
            match(self.kind):
                case DiagnosticKind.INFO:
                    ret += "\x1b[34mINFO\x1b[0m "
                case DiagnosticKind.WARN:
                    ret += "\x1b[33mWARN\x1b[0m "
                case DiagnosticKind.ERROR:
                    ret += "\x1b[31mERROR\x1b[0m "
                case DiagnosticKind.CRITICAL:
                    ret += "\x1b[41;97mCRITICAL\x1b[0m "

        if (doEmitSrc):
            match(self.source):
                case DiagnosticSource.LEXER:
                    ret += "<LEX> "
                case DiagnosticSource.SYNANAL:
                    ret += "<SYN> "
                case DiagnosticSource.SEMANAL:
                    ret += "<SEM> "
                case DiagnosticSource.OPTIM:
                    ret += "<OPT> "
                case DiagnosticSource.CODEGEN:
                    ret += "<GEN> "

        if (doEmitPos): ret += f"[{self.startPos[1]}:{self.startPos[2]} - {self.endPos[1]}:{self.endPos[2]}] "
        ret += self.msgTemplate.format(**self.args)

        return ret