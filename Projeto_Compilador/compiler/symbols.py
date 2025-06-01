from __future__ import annotations
from typing import overload, Any, Optional
from enum import Enum, auto

import compiler.ast as ast
from compiler.sastate import *

class Reference_Error:
    def __init__(self, sym: "Symbol"):
        self.sym = sym

#region -------------- Symbol Values --------------
class SymbolValue:
    pass

class EnumeratedTypeSymbolValue(SymbolValue):
    def __init__(self, parent: ast.EnumeratedTypeNode, _ord: int):
        self.parent = parent
        self.values = parent.value
        self._ord = _ord

    def __repr__(self, level = 1):
        noffset = ' ' * ((level + 3) * 1)
        ret = f"{type(self).__name__}(" \
            f"\n{noffset}  parent={self.parent.__repr__(level + 3)}"

        ret += f"\n{noffset}  )\n{noffset}"
        return ret

    def ord(self, value) -> int:
        return self.values.index(IdentifierNode(value))

    def pred(self, ord):
        if (ord <= 0): return None
        else: return self.values[ord - 1]

    def succ(self, ord):
        if (ord >= len(self.values) - 1): return None
        else: return self.values[ord + 1]

class SubrangeTypeSymbolValue(SymbolValue):
    def __init__(self, parent: ast.SubrangeTypeNode, start, end, btype: ast.Node):
        self.parent = parent
        self.start = start
        self.end = end
        self.btype = btype

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)
        ret = f"{type(self).__name__}(" \
            f"id={type(self.parent).__name__}," \
            f"start={self.start}," \
            f"end={self.end}," \
            f"btype={self.btype},"

        ret += ")"
        return ret

class ArrayTypeSymbolValue(SymbolValue):
    def __init__(self, parent: ast.EnumeratedTypeNode, ranges: list, btype: ast.Node):
        self.parent = parent
        self.ranges = ranges
        self.btype = btype

    def __repr__(self, level = 1, resolveRefs = False):
        noffset = ' ' * ((level + 3) * 1)
        ret = f"{type(self).__name__}(" \
            f"\n{noffset}  parent={self.parent.__repr__(level + 3)}," \
            f"\n{noffset}  ranges=["

        for r in self.ranges:
            if (resolveRefs):
                ret += f"\n{noffset}    {r.__repr__(level + 3)},"
            else:
                ret += f"\n{noffset}    {r.getRefStr()},"
        ret += f"\n{noffset}  ]"

        ret += f"\n{noffset}  )\n{noffset}"
        return ret

class RecordTypeSymbolValue(SymbolValue):
    def __init__(self, parent: ast.RecordTypeNode, fixedPart: dict[str, "Symbol"], variantPart: dict[str, "Symbol"]):
        self.parent = parent
        self.fixedPart = fixedPart
        self.variantPart = variantPart

    def __repr__(self, level = 1, resolveRefs = False):
        noffset = ' ' * ((level + 3) * 1)
        ret = f"{type(self).__name__}(" \
            f"\n{noffset}  parent={self.parent.__repr__(level + 3)},"

        ret += f"\n{noffset}  fixedPart={{"
        for key in self.fixedPart:
            if (resolveRefs):
                ret += f"\n{noffset}     '{key}': {self.fixedPart[key].__repr__(level + 3)},"
            else:
                ret += f"\n{noffset}    '{key}': {self.fixedPart[key].getRefStr()},"
        ret += f"\n{noffset}  }}"

        ret += f"\n{noffset}  variantPart={{"
        for key in self.variantPart:
            if (resolveRefs):
                ret += f"\n{noffset}     '{key}': {self.variantPart[key].__repr__(level + 3)},"
            else:
                ret += f"\n{noffset}    '{key}': {self.variantPart[key].getRefStr()},"
        ret += f"\n{noffset}  }}"

        ret += f"\n{noffset}  )\n{noffset}"
        return ret

class ProcedureOrFunctionParameterSymbolValue(SymbolValue):
    def __init__(self, parent: ast.ParameterSpecificationNode, typeSym: "Symbol"):
        self.parent = parent
        self.typeSym = typeSym

    def __repr__(self, level = 1, resolveRefs = False):
        noffset = ' ' * ((level + 3) * 1)
        ret = f"{type(self).__name__}(" \
            f"\n{noffset}  parent={self.parent.__repr__(level + 3)},"

        if (resolveRefs): ret += f"typeSym={self.typeSym.__repr__()}"
        else: ret += f"typeSym={self.typeSym.getRefStr()}"

        ret += f"\n{noffset}  )\n{noffset}"
        return ret

class ProcedureOrFunctionSymbolValue(SymbolValue):
    def __init__(
        self, 
        parent: ast.ProcedureDeclarationNode | ast.FunctionDeclarationNode, 
        params: list["Symbol"], 
        retType,
        body: ast.BlockNode | None
    ):
        self.parent = parent
        self.params = params
        self.retType = retType
        self.body = body

    def __repr__(self, level = 1, resolveRefs = False):
        noffset = ' ' * ((level + 3) * 1)
        ret = f"{type(self).__name__}(" \
            f"\n{noffset}  parent={self.parent.__repr__(level + 3)},"

        ret += f"\n{noffset}  params=["
        for param in self.params:
            if (resolveRefs): ret += f"\n{noffset}     {param.__repr__(level + 3)},"
            else: ret += f"\n{noffset}    {param.getRefStr()},"
        ret += f"\n{noffset}  ],"

        if (self.retType != None):
            ret += f"\n{noffset}  retType={self.retType.__repr__()}"
        else:
            ret += f"\n{noffset}  retType=N/A"

        if (self.body != None):
            ret += f"\n{noffset}  body={self.body.__repr__(level + 3)}"
        else:
            ret += f"\n{noffset}  body=N/A"

        ret += f"\n{noffset}  )\n{noffset}"
        return ret
#endregion -------------- Symbol Values --------------

class SymbolKind(Enum):
    SYM_ANY = auto(),
    SYM_ID = auto(),
    SYM_VAR = auto(),
    SYM_PARAM = auto(),
    SYM_ALIAS = auto(),
    SYM_LABEL = auto(),
    SYM_CONST = auto(),
    SYM_RECORD = auto(),
    SYM_TYPEDEF = auto(),
    SYM_TYPELIT = auto(),
    SYM_POINTER = auto(),
    SYM_ACTIVATABLE = auto(),

class Symbol:
    def __init__(self, kind: SymbolKind, name, value = None):
        self.id = self._getId()
        self.kind = kind
        self.name = name
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Symbol) and self.id == other.id # For internal purposes (indexing, usually)

    def __repr__(self, level = 0, resolveRefs = False, nested = False):
        ret = f"{type(self).__name__}(" \
            f"id={self.id}," \
            f"kind={self.kind}," \
            f"name={self.name},"

        nest = resolveRefs and nested
        if (isinstance(self.value, ast.Node)): ret += f"value={self.value.__repr__(level + 2)}"
        elif (isinstance(self.value, Symbol)):
            if (resolveRefs): ret += f"value={self.value.__repr__(level + 1, nest, nest)}"
            else: ret += f"value={self.value.getRefStr()}"
        elif (isinstance(self.value, list)):
            ret += f"value=["
            for v in self.value:
                ret += f"\n        {v.__repr__()}"
            ret += f"\n    ]"
        else: ret += f"value={self.value}"

        ret += ")"

        return ret

    def getRefStr(self):
        return f"<Symbol @ {self.id} ({self.name})>"

    #region ------- Static -------
    _ID = 0

    @classmethod
    def _getId(cls):
        cls._ID = cls._ID + 1
        return cls._ID

    @classmethod
    def _rollbackId(cls):
        cls._ID = cls._ID - 1
        return cls._ID

    @classmethod
    def _fromId(cls, id):
        sym = cls(SymbolKind.SYM_ANY, "__INTERNAL__")
        cls._ID = cls._ID - 1
        sym.id = id

        return sym
    #endregion ------- Static -------

class SymbolTable:
    def __init__(self, syms: list[Symbol] = None, scopes: list["SymbolTable"] = None, parent: "SymbolTable" = None):
        self.id = self._getId()
        self.parent = parent

        if (syms == None): self.syms: list[Symbol] = []
        else: self.syms = [*syms]

        if (scopes == None): self.scopes: list["SymbolTable"] = []
        else: self.scopes = [*scopes]

        self._procedure = None

    #region ------- Assertions -------
    def hasSymbolId(self, id, local = False) -> bool:
        return any(sym.id == id for sym in self.syms) \
            or (not local and (self.parent.hasSymbolId(id, kind) if self.parent else False))

    def hasSymbol(self, name, kind: SymbolKind = SymbolKind.SYM_ANY, local = False) -> bool:
        if (kind == SymbolKind.SYM_ANY):
            return any(sym.name == name for sym in self.syms) \
                or (not local and (self.parent.hasSymbol(name, kind) if self.parent else False))
        else:
            return any(sym.kind == kind and sym.name == name for sym in self.syms) \
                or (not local and (self.parent.hasSymbol(name, kind) if self.parent else False))

    def hasSymbolValue(self, value, kind: SymbolKind = SymbolKind.SYM_ANY, local = False) -> bool:
        if (kind == SymbolKind.SYM_ANY):
            return any(sym.value == value for sym in self.syms) \
                or (not local and (self.parent.hasSymbolValue(value, kind) if self.parent else False))
        else:
            return any(sym.kind == kind and sym.value == value for sym in self.syms) \
                or (not local and (self.parent.hasSymbolValue(value, kind) if self.parent else False))
    #endregion ------- Assertions -------

    #region ------- Getters -------
    def getLatestSymbol(self) -> Symbol:
        return self.syms[-1]

    def getSymbolById(self, id, local = False) -> Symbol:
        ownSym = list(filter(lambda s: s.id == id, self.syms))
        if (len(ownSym) > 0): return ownSym[0]
        if (not local and self.parent != None): return self.parent.getSymbolById(id)
        return None

    def getSymbolByNameAndKind(self, name, kind: SymbolKind = SymbolKind.SYM_ANY, local = False) -> Symbol:
        if (kind == SymbolKind.SYM_ANY): ownSym = list(filter(lambda s: s.name == name, self.syms))
        else: ownSym = list(filter(lambda s: s.kind == kind and s.name == name, self.syms))

        if (len(ownSym) > 0): return ownSym[0]
        if (not local and self.parent != None): return self.parent.getSymbolByNameAndKind(name, kind)
        return None

    def getSymbolByValueAndKind(self, value, kind: SymbolKind = SymbolKind.SYM_ANY, local = False) -> Symbol:
        if (kind == SymbolKind.SYM_ANY): ownSym = list(filter(lambda s: s.value == value, self.syms))
        else: ownSym = list(filter(lambda s: s.kind == kind and s.value == value, self.syms))

        if (len(ownSym) > 0): return ownSym[0]
        if (not local and self.parent != None): return self.parent.getSymbolByValueAndKind(value, kind)
        return None

    def getSymbolsByKind(self, kind: SymbolKind, local = False):
        if (kind == SymbolKind.SYM_ANY): ownSym = self.syms
        else: ownSym = list(filter(lambda s: s.kind == kind, self.syms))

        if (not local and self.parent != None): pSym = self.parent.getSymbolsByKind(kind)
        else: pSym = []

        return ownSym + pSym

    def findScopeWithSymbolNameAndKind(
        self, 
        name: str, 
        kind: SymbolKind = SymbolKind.SYM_ANY
    ) -> Optional["SymbolTable"]:
        def search(scope: SymbolTable) -> Optional["SymbolTable"]:
            for sym in scope.syms.values():
                if (kind == SymbolKind.SYM_ANY or sym.kind == kind) and sym.name == name: return scope
            
            for child in scope.scopes:
                result = search(child)
                if result: return result
           
            return None

        root = self
        while root.parent is not None:
            root = root.parent

        return search(root)

    def resolveReference(self, ref: ast.IdentifierNode, kind: SymbolKind = SymbolKind.SYM_ANY):
        return self.getSymbolByNameAndKind(ref.value, kind)

    def resolvePossibleReference(self, ref: ast.Node):
        if (isinstance(ref, Symbol)): return self.resolvePossibleSymbolReference(ref)
        elif (isinstance(ref, str)): return self.getSymbolByNameAndKind(ref)
        elif (ref.ist(ast.IdentifierNode)): return self.resolvePossibleReference(self.resolveReference(ref))
        elif (ref.ist(ast.TypeIdentifierNode)): return self.resolvePossibleReference(self.resolveReference(ref.value))
        elif (ref.ist(ast.Node)): return ref
        else: return None

    def resolvePossibleSymbolReference(self, ref: Symbol):
        if (not isinstance(ref, Symbol)): return ref
        elif (ref.kind == SymbolKind.SYM_ALIAS): 
            sym = self.getSymbolByNameAndKind(ref.value)
            return self.resolvePossibleSymbolReference(sym)
        if (ref.kind == SymbolKind.SYM_TYPELIT): return ref.value
        elif (ref.kind == SymbolKind.SYM_CONST): return ref
        else: return ref
    #endregion ------- Assertions -------
    
    #region ------- Setters -------
    def addSymbol(self, sym: Symbol) -> Symbol:
        self.syms.append(sym)
        return sym

    def removeSymbolById(self, id: int):
        try:
            si = self.syms.index(Symbol._fromId(id))
            self.syms.pop(si)

            return True
        except:
            return False

    def addScope(self, scope: SymbolTable):
        self.scopes.append(scope)
    #endregion ------- Setters -------

    def __repr__(self, level = 0, resolveRefs = False, nested = False):
        noffset = ' ' * ((level + 1) * 2)
        ret = f"{type(self).__name__}(" \
            f"\n{noffset}id={self.id},"

        ret += f"\n{noffset}symbols=["
        if (self.syms):
            for sym in self.syms:
                if (resolveRefs):
                    nest = resolveRefs and nested
                    ret += f"\n{noffset}  - {sym.__repr__(level + 1, nest, nest)}"
                else:
                    ret += f"\n{noffset}  - {sym.getRefStr()}"
            ret += f"\n{noffset}]"
        else:
            ret += "]"

        ret += f"\n{noffset}scopes=["
        if (self.scopes):
            for scope in self.scopes:
                if (resolveRefs):
                    nest = resolveRefs and nested
                    ret += f"\n{noffset}  - {scope.__repr__(level + 2, nest, nest)}"
                else: 
                    ret += f"\n{noffset}  - {scope.getRefStr()}"
            ret += f"\n{noffset}]"
        else:
            ret += "]"

        if (self.parent):
            ret += f",\n{noffset}parent={self.parent.getRefStr()}"
        else:
            ret += f",\n{noffset}parent=N/A"

        ret += f"\n{' ' * (level * 2)})"

        return ret

    def getRefStr(self):
        return f"<SymbolTable @ {self.id}>"

    #region ------- Static -------
    _ID = 0
    _scopeStack = []

    @classmethod
    def _getId(cls):
        cls._ID = cls._ID + 1
        return cls._ID

    @classmethod
    def getCurrentScope(cls) -> SymbolTable:
        return cls._scopeStack[-1] if (len(cls._scopeStack) > 0) else None

    @classmethod
    def pushScope(cls, defer = False) -> SymbolTable:
        parent = cls.getCurrentScope()
        # scope = SymbolTable(None, None, parent)
        scope = SymbolTable(None, None, None)

        if (not defer): 
            if (parent != None): 
                parent.addScope(scope)
                scope.parent = parent
        else:
            scope.parent = SA_STATE["scopes"][0] # Ensure builtin is always present.
        
        SA_STATE["scopes"].append(scope)
        cls._scopeStack.append(scope)
        return scope

    @classmethod
    def popScope(cls, defer = False):
        scope = cls._scopeStack.pop()
        parent = cls.getCurrentScope()

        if (defer): 
            print("ALLAHU AKBAR OR SOME SHIT:", scope, parent)
            if (parent != None): 
                parent.addScope(scope)
                scope.parent = parent
    #endregion ------- Static -------