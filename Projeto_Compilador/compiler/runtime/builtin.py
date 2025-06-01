#
# This module contaiuns the built-in library loaded by default for all programs processed by this compiler. It contains
# definitions for primitive types, such as Real, Integer, Boolean and Char, and built-in functions.
#

from __future__ import annotations
import operator as o
from math import *

from compiler.sastate import *
from compiler.symbols import *
import compiler.ast as ast
from compiler.diag import Diagnostic, DiagnosticType, DiagnosticKind, DiagnosticSource

#region -------------- Independent Constants --------------
# The Max Integer supported is implementation-defined, according to the spec. Even though the EWVM, being written in
# JS, supports 64 bit integers, I'm using 32 bits as the max because fuck it, I'm the one writing this, I'm the one who
# calls the shots. Also, I've seen the horrors inside that code base, and I'm going to abide by JS's MAX_SAFE_INTEGER
# just to be safe.
_MAX_INTEGER = 0x7fffffff
_INTEGER_STEP = 1

# Similarly to the Max Integer, the Max Real is implementation-defined, according to the spec. In the same note, the 
# EWVM, being written in JS, represents numbers as binary64, however, I'm limiting reals here to 32-bit floats for
# consistency with integers. Additionally, I also define the step for the reals
_MAX_REAL    = 1.0e+38
_REAL_STEP   = 1.0e-6
#endregion -------------- Independent Constants --------------

class BuiltInNode(ast.Node):
    def __init__(self, value = None):
        super().__init__(value)
        self.makeBuiltIn(self)

    # def __getattribute__(self, name):
    #     return None

    def __repr__(self, _ = None):
        return "<builtin>"

    @classmethod
    def typeEquals(self, other):
        return isinstance(other, self)

    @classmethod
    def makeBuiltIn(cls, node: ast.Node):
        node.__builtin__ = 0xD1EA7011C3

#region -------------- Section R6.1.2 --------------
class _NumericalNode(BuiltInNode):
    def __init__(self, lb, hb, step, ttype, fdiv, nkind):
        super().__init__()
        self.lb = lb
        self.hb = hb
        self.step = step
        self.ttype = ttype
        self.fdiv = fdiv
        self.nkind = nkind

    def __repr__(self, _ = None):
        return f"<builtin _NumericalNode>" # If you find in the terminal, WHAT IN THE NAME OF FUCK DID YOU DO?

    def ord(self, value):
        return self.ttype(value)

    def pred(self, value):
        result = value - self.step
        return max(self.lb, result)

    def succ(self, value):
        result = value + self.step
        return min(self.hb, result)

    #region ------- Arithmetic Operations -------
    def op_uplus(self, a: ast.NumberNode):
        return self._op(a, o.pos)

    def op_uminus(self, a: ast.NumberNode):
        return self._op(a, o.neg)

    def op_add(self, a: ast.NumberNode, b: ast.NumberNode):
        return self._op(a, o.add, b)

    def op_sub(self, a: ast.NumberNode, b: ast.NumberNode):
        return self._op(a, o.sub, b)

    def op_mul(self, a: ast.NumberNode, b: ast.NumberNode):
        return self._op(a, o.mul, b)

    def op_div(self, a: ast.NumberNode, b: ast.NumberNode):
        if self.toNative(b) == 0.0: raise SemanticError.noemit(b, DiagnosticType.ZERO_DIV, {})
        return self._op(a, self.fdiv, b)

    def op_abs(self, a: ast.NumberNode, b: ast.NumberNode):
        return self._op(a, o.abs, b)
    #endregion ------- Arithmetic Operations -------

    #region ------- Relational Operations -------
    def op_eq(self, a: ast.NumberNode, b: ast.NumberNode):
        return self._bop(a, o.eq, b)

    def op_neq(self, a: ast.NumberNode, b: ast.NumberNode):
        return self._bop(a, o.ne, b)

    def op_lt(self, a: ast.NumberNode, b: ast.NumberNode):
        return self._bop(a, o.lt, b)
        
    def op_lte(self, a: ast.NumberNode, b: ast.NumberNode):
        return self._bop(a, o.le, b)
        
    def op_gt(self, a: ast.NumberNode, b: ast.NumberNode):
        return self._bop(a, o.gt, b)
        
    def op_gte(self, a: ast.NumberNode, b: ast.NumberNode):
        return self._bop(a, o.ge, b)
    #endregion ------- Relational Operations -------

    def inBounds(self, value: float) -> bool:
        return self.lb <= value <= self.hb and not isinf(value) and not isnan(value)

    def toNative(self, value: ast.NumberNode):
        return self.ttype(value.value)

    def fromNative(self, value):
        # return ast.NumberNode(value, self.nkind)
        return value

    # Arithmetic Operation
    def _op(self, a: ast.NumberNode, op, b: ast.NumberNode = None):
        if (b == None):
            return self._clamp(BuiltInNode(op(self.toNative(a))).setTokenPos(a.pos))
        else:
            return self._clamp(
                BuiltInNode(op(self.toNative(a), self.toNative(b))).setStartTokenPos(a.pos).setEndTokenPos(a.pos)
            )

    # Binary Operation
    def _bop(self, a: ast.NumberNode, op, b: ast.NumberNode = None):
        if (b == None):
            return op(self.toNative(a))
        else:
            return op(self.toNative(a), self.toNative(b))

    def _clamp(self, value: BuiltInNode) -> float:
        if isnan(value.value): raise SemanticError.noemit(value, DiagnosticType.NAN_RESULT, {})
        if isinf(value.value): raise SemanticError.noemit(value, DiagnosticType.INFINITY_RESULT, {})
        return min(max(value.value, self.lb), self.hb)

class _Real(_NumericalNode):
    def __init__(self):
        super().__init__(-_MAX_REAL, _MAX_REAL, _REAL_STEP, float, o.truediv, ast.NumberKind.UNSIGNED_REAL)

    def __repr__(self, _ = None):
        return f"<builtin Real>"

class _Integer(_NumericalNode):
    def __init__(self):
        super().__init__(-_MAX_INTEGER, _MAX_INTEGER, _INTEGER_STEP, int, o.floordiv, ast.NumberKind.UNSIGNED_INTEGER)

    def __repr__(self, _ = None):
        return f"<builtin Integer>"

    def op_sqr(self, a: ast.NumberNode):
        return self._op(self.toNative(a), o.pow, 2)

    def op_trunc(self, a: ast.NumberNode):
        return self._op(self.toNative(a), trunc)

    def op_round(self, a: ast.NumberNode):
        return self._op(self.toNative(a), round)

class _Boolean(ast.EnumeratedTypeNode):
    def __init__(self):
        super().__init__([
            ast.IdentifierNode("false"),
            ast.IdentifierNode("true")
        ])
        BuiltInNode.makeBuiltIn(self)

    def __repr__(self, _ = None):
        return f"<builtin Boolean>"

    def op_not(self, a: str) -> bool:
        return not self.toNative(a)

    def op_and(self, a: str, b: str) -> bool:
        return self.toNative(a) and self.toNative(b)

    def op_or(self, a: str, b: str) -> bool:
        return self.toNative(a) or self.toNative(b)

    #region ------- Relational Operations -------
    # Equivalence
    def op_eq(self, a: str, b: str) -> float:
        return self.toNative(a) == self.toNative(b)

    # XOR
    def op_neq(self, a: str, b: str) -> float:
        # P | Q | P <> Q
        # 1 | 1 |   0
        # 1 | 0 |   1
        # 0 | 1 |   1
        # 0 | 0 |   0
        return o.xor(self.toNative(a), self.toNative(b))

    def op_lt(self, a: str, b: str) -> float:
        return self.toNative(a) < self.toNative(b)
        
    # Implication
    def op_lte(self, a: str, b: str) -> float:
        av = self.toNative(a)
        bv = self.toNative(b)

        # P | Q | Q <= P
        # 1 | 1 |   1
        # 1 | 0 |   0
        # 0 | 1 |   1
        # 0 | 0 |   1
        if (av and not b): return False
        else: return True
        
    def op_gt(self, a: str, b: str) -> float:
        return self.toNative(a) > self.toNative(b)
        
    def op_gte(self, a: str, b: str) -> float:
        return self.toNative(a) >= self.toNative(b)
    #endregion ------- Relational Operations -------

    #region ------- Predefined Operations -------
    def op_odd(self, a: ast.NumberNode) -> bool:
        if (not a.isInt()): return False
        return a.value % 2 == 0
    #endregion ------- Predefined Operations -------

    def toNative(self, value: "false" | "true"):
        return True if (value == "true") else False

    def fromNative(self, value: bool):
        return "true" if value else "false"

class _Char(BuiltInNode):
    def __repr__(self, _ = None):
        return f"<builtin Char>"

    def chr(self, value: ast.NumberNode):
        return chr(__BUILTIN_INTEGER__.toNative(value))

    def ord(self, value: ast.IdentifierNode):
        return self.toNative(value)

    def pred(self, value: ast.IdentifierNode):
        return str(max(0, self.toNative(value) - 1))

    def succ(self, value: ast.IdentifierNode):
        return str(min(255, self.toNative(value) + 1))

    #region ------- Arithmetic Operations -------
    def op_uplus(self, a: ast.IdentifierNode):
        return self._op(a, o.pos)

    def op_uminus(self, a: ast.IdentifierNode):
        return self._op(a, o.neg)

    def op_add(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        return self._op(a, o.add, b)

    def op_sub(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        return self._op(a, o.sub, b)

    def op_mul(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        return self._op(a, o.mul, b)

    def op_div(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        if self.toNative(b) == 0.0: raise SemanticError.noemit(b, DiagnosticType.ZERO_DIV, {})
        return self._op(a, self.fdiv, b)

    def op_abs(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        return self._op(a, o.abs, b)
    #endregion ------- Arithmetic Operations -------

    #region ------- Relational Operations -------
    def op_eq(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        return self._op(a, o.eq, b)

    def op_neq(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        return self._op(a, o.ne, b)

    def op_lt(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        return self._op(a, o.lt, b)
        
    def op_lte(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        return self._op(a, o.le, b)
        
    def op_gt(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        return self._op(a, o.gt, b)
        
    def op_gte(self, a: ast.IdentifierNode, b: ast.IdentifierNode):
        return self._op(a, o.ge, b)
    #endregion ------- Relational Operations -------

    def toNative(self, value: ast.IdentifierNode):
        return ord(value.value)

    def fromNative(self, value: int):
        return ast.IdentifierNode(chr(value))
        # return chr(value)

    # Arithmetic Operation
    def _op(self, a: ast.IdentifierNode, op, b: ast.IdentifierNode = None):
        if (b == None):
            return self.fromNative(op(self.toNative(a)))
        else:
            return self.fromNative(op(self.toNative(a), self.toNative(b)))

class _String(BuiltInNode):
    def __init__(self, value: str = ""):
        self.value = ""

    def __repr__(self, _ = None):
        return f"<builtin String '{self.value}'>"

    def charAt(self, i: int):
        return __BUILTIN_CHAR__.ord(self.value[i])

class _Nil(BuiltInNode):
    def __repr__(self, _ = None):
        return f"<builtin Nil>"

class _Any(BuiltInNode):
    def __repr__(self, _ = None):
        return f"<builtin Any>"

    def typeEquals(self, other):
        return True

class _ReadLn(BuiltInNode):
    def __init__(self):
        self.params = [Symbol(SymbolKind.SYM_PARAM, "input", __BUILTIN_STRING__)]

    def __repr__(self, _ = None):
        return f"<builtin Read>"

class _Write(BuiltInNode):
    def __init__(self, withLn = False):
        self.params = [Symbol(SymbolKind.SYM_PARAM, "input", __BUILTIN_ANY__)]
        self.withLn = withLn

    def __repr__(self, _ = None):
        return f"<builtin WriteLn>"
        return f"<builtin Read>"

class _Length(BuiltInNode):
    def __init__(self):
        self.params = [Symbol(SymbolKind.SYM_PARAM, "input", __BUILTIN_STRING__)]

    def __repr__(self, _ = None):
        return f"<builtin Length>"

class _Atoi(BuiltInNode):
    def __init__(self):
        self.params = [Symbol(SymbolKind.SYM_PARAM, "input", __BUILTIN_STRING__)]

    def __repr__(self, _ = None):
        return f"<builtin Atoi>"
#endregion -------------- Section R6.1.2 --------------

#region -------------- System Constants --------------
__BUILTIN__ = BuiltInNode()
__BUILTIN_REAL__ = _Real()
__BUILTIN_INTEGER__ = _Integer()
__BUILTIN_BOOLEAN__ = _Boolean()
__BUILTIN_CHAR__ = _Char()
__BUILTIN_STRING__ = _String()
__BUILTIN_NIL__ = _Nil()
__BUILTIN_ANY__ = _Any()
__BUILTIN_READLN__ = _ReadLn()
__BUILTIN_WRITE__ = _Write()
__BUILTIN_WRITELN__ = _Write(True)
__BUILTIN_LENGTH__ = _Length()
__BUILTIN_ATOI__ = _Atoi()
__BUILTIN_SYMTABLE__ = SymbolTable([
    Symbol(SymbolKind.SYM_TYPEDEF, "Real", __BUILTIN_REAL__),
    Symbol(SymbolKind.SYM_TYPEDEF, "Integer", __BUILTIN_INTEGER__),
    Symbol(SymbolKind.SYM_TYPEDEF, "Boolean", __BUILTIN_BOOLEAN__),
    Symbol(SymbolKind.SYM_TYPEDEF, "Char", __BUILTIN_CHAR__),
    Symbol(SymbolKind.SYM_TYPEDEF, "String", __BUILTIN_STRING__),
    Symbol(SymbolKind.SYM_TYPEDEF, "Nil", __BUILTIN_NIL__),
    # Symbol(SymbolKind.SYM_TYPEDEF, "Any", __BUILTIN_ANY__),
    Symbol(SymbolKind.SYM_TYPELIT, "false", EnumeratedTypeSymbolValue(__BUILTIN_BOOLEAN__, 0)),
    Symbol(SymbolKind.SYM_TYPELIT, "true", EnumeratedTypeSymbolValue(__BUILTIN_BOOLEAN__, 1)),
    Symbol(SymbolKind.SYM_ACTIVATABLE, "ReadLn", __BUILTIN_READLN__),
    Symbol(SymbolKind.SYM_ACTIVATABLE, "Write", __BUILTIN_WRITE__),
    Symbol(SymbolKind.SYM_ACTIVATABLE, "WriteLn", __BUILTIN_WRITELN__),
    Symbol(SymbolKind.SYM_ACTIVATABLE, "Length", __BUILTIN_LENGTH__),
    Symbol(SymbolKind.SYM_ACTIVATABLE, "Atoi", __BUILTIN_ATOI__),
])

BUILTINS = {
    "_": __BUILTIN__,
    "Real": __BUILTIN_REAL__,
    "Integer": __BUILTIN_INTEGER__,
    "Boolean": __BUILTIN_BOOLEAN__,
    "Char": __BUILTIN_CHAR__,
    "String": __BUILTIN_STRING__,
    "Nil": __BUILTIN_NIL__,
    "Any": __BUILTIN_ANY__,
    "ReadLn": __BUILTIN_READLN__,
    "Write": __BUILTIN_WRITE__,
    "WriteLn": __BUILTIN_WRITELN__,
    "Atoi": __BUILTIN_ATOI__,
}
#endregion -------------- System Constants --------------

def registerBuiltin():
    SA_STATE["scopes"].append(__BUILTIN_SYMTABLE__)
    SymbolTable._scopeStack.append(__BUILTIN_SYMTABLE__)