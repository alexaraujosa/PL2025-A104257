from __future__ import annotations
from enum import Enum, auto
import os

import compiler.ast as ast
from compiler.sastate import *
from compiler.symbols import *
from compiler.runtime.builtin import *

_LABEL_ID = -1
def getLabelId():
    global _LABEL_ID
    _LABEL_ID = _LABEL_ID + 1
    return _LABEL_ID

_ACTIVATABLE_MAP = {}
def addActivatable(name: str, bld: "CodeTree"):
    _ACTIVATABLE_MAP[name] = bld

def getActivatable(name: str) -> "CodeTree":
    return _ACTIVATABLE_MAP[name]

class CodeID(Enum):
    # Integer Arithmetic
    ADD = auto(),
    SUB = auto(),
    MUL = auto(),
    DIV = auto(),
    MOD = auto(),
    NOT = auto(),
    INF = auto(),
    INFEQ = auto(),
    SUP = auto(),
    SUPEQ = auto(),

    # Real Arithmetic
    FADD = auto(),
    FSUB = auto(),
    FMUL = auto(),
    FDIV = auto(),
    FINF = auto(),
    FSIN = auto(),
    FCOS = auto(),
    FINFEQ = auto(),
    FSUP = auto(),
    FSUPEQ = auto(),

    # String Ops
    CONCAT = auto(),
    CHRCODE = auto(),
    STRLEN = auto(),
    CHARAT = auto(),

    # Binary Ops
    CHECK = auto(),
    AND = auto(),
    OR = auto(),
    EQUAL = auto(),

    # Conversion
    ATOI = auto(),
    ATOF = auto(),
    ITOF = auto(),
    FTOI = auto(),
    STRI = auto(),
    STRF = auto(),

    # Data Manip
    PUSHI = auto(),
    PUSHN = auto(),
    PUSHF = auto(),
    PUSHS = auto(),
    PUSHG = auto(),
    PUSHL = auto(),
    PUSHSP = auto(),
    PUSHFP = auto(),
    PUSHGP = auto(),
    PUSHST = auto(),
    LOAD = auto(),
    LOADN = auto(),
    DUP = auto(),
    DUPN = auto(),

    # Dielete
    POP = auto(),
    POPN = auto(),

    # OpStack Manip
    STOREL = auto(),
    STOREG = auto(),
    STORE = auto(),
    STOREN = auto(),
    SWAP = auto(),

    # Heap ops
    # NOTE: Would be used for records, but I doubt I will have the time to implement them.
    ALLOC = auto(),
    ALLOCN = auto(),
    FREE = auto(),
    POPST = auto(),

    # I/O
    WRITEI = auto(),
    WRITEF = auto(),
    WRITES = auto(),
    WRITELN = auto(),
    WRITECHR = auto(),
    READ = auto(),

    # Control
    PUSHA = auto(),
    JUMP = auto(),
    JZ = auto(),
    CALL = auto(),
    RETURN = auto(),
    START = auto(),
    NOP = auto(),
    ERR = auto(),
    STOP = auto(),

    _LABEL = auto(),
    _SUBTREE = auto(),

# Stack is described through a sequence of tuples (CodeID, [args])
CodePoint = (CodeID, list)

class CodeTree:
    def __init__(self):
        self._labelId = getLabelId()

        self.stack: list[CodePoint] = []
        self._varMap: dict[str, int] = {}
        self._varId = 0

        self._argMap: dict[str, int] = {}
        self._argId = 0

        self._builtin = None

    @classmethod
    def builtin(cls, cb):
        ins = cls()
        ins._builtin = cb
        return ins

    def __repr__(self, level = 0):
        noffset = ' ' * (level + 1)
        res = "Tree\n"
        res += f"{noffset}|- Args {self._argId}\n"
        for i in self._argMap:
            res += f"{noffset}| |- {i}: {self._argMap[i]}\n"
        res += f"{noffset}|- Vars {self._varId}\n"
        for i in self._varMap:
            res += f"{noffset}| |- {i}: {self._varMap[i]}\n"
        res += f"{noffset}|- Stack\n"
        for i in self.stack:
            if (i[0] == CodeID._SUBTREE):
                res += f"{noffset}| |- {i[1][0].__repr__(level + 2)}"
            else:
                res += f"{noffset}| |- {i[0]} {i[1]}\n"
        res += f"{noffset}\\---------------------\n"

        return res
                
    def _inst(self, p: CodeID, args: []):
        self.stack.append((p, args))

    def _mono(self, id: CodeID):
        self.stack.append((id, []))

    def nop(self):
        self.stack.append((CodeID.NOP, []))
    
    def int(self, i: int):
        self.stack.append((CodeID.PUSHI, [i]))

    # Arguments are passed in-order in the negative indexes in relation to the FP. Insert their ids by their 
    # reverse order.
    def loadArgs(self, args: list[ast.ParameterSpecificationNode], arglen: int):
        self._argId = arglen
        for arg in args:
            for iden in arg.identifiers:
                self._argMap[iden] = -self._argId
                self._argId = self._argId - 1
        return self

    # Optimally, should only be used at the start.
    def allocVariable(self, name: str, size: int = 1):
        self.stack.append((CodeID.PUSHN, [size]))
        self._varMap[name] = self._varId
        self._varId = self._varId + size
        return self

    def setVariable(self, name: str):
        self.stack.append((CodeID.STOREL, [self._varMap[name]]))

    def getVariable(self, name: str, offset = 0):
        # ind = self._varMap[name]
        ind = self._argMap.get(name, self._varMap.get(name, 0) + offset)
        self.stack.append((CodeID.PUSHL, [ind]))
        return self

    # Dynamically sets the value of a variable. Requires that the desired offset be known beforehand.
    def setVariableDyn(self, name: str):
        # self.stack.append((CodeID.PUSHFP, []))
        # self.stack.append((CodeID.SWAP, []))
        # self.stack.append((CodeID.PUSHI, [self._varMap[name]]))
        # self.stack.append((CodeID.ADD, []))
        # self.stack.append((CodeID.STOREN, []))

        self.stack.append((CodeID.PUSHFP, []))
        self.stack.append((CodeID.PUSHI, [self._varMap[name]]))
        self.stack.append((CodeID.PUSHSP, []))
        self.stack.append((CodeID.LOAD, [-2]))
        self.stack.append((CodeID.STOREN, []))
        self.stack.append((CodeID.POP, [1]))

    # Dynamically gets the value of a variable. Requires that the desired offset be known beforehand.
    def getVariableDyn(self, name: str):
        # ind = self._argMap.get(name, -0xD1EA55801E)

        # if (ind == -0xD1EA55801E):
        #     self.stack.append((CodeID.PUSHFP, []))
        #     self.stack.append((CodeID.SWAP, []))
        #     self.stack.append((CodeID.PUSHI, [self._varMap[name]]))
        #     self.stack.append((CodeID.ADD, []))
        #     self.stack.append((CodeID.LOAD, [0]))
        # else:
        #     self.stack.append((CodeID.PUSHL, [ind]))

        ind = self._argMap.get(name, self._varMap.get(name, 0))
        self.stack.append((CodeID.PUSHI, [ind]))
        self._mono(CodeID.ADD)

        self.stack.append((CodeID.PUSHFP, []))
        self.stack.append((CodeID.SWAP, []))
        self.stack.append((CodeID.LOAD, [0]))

        return self

    def markLabel(self, label: int):
        self.stack.append((CodeID._LABEL, [label]))

    # Here, we assume the parameters were already passed in the correct order.
    def call(self, name: str, typeHints = []):
        act = getActivatable(name)
        if (act._builtin): 
            if (act._builtin(self, typeHints)):
                self._mono(CodeID.CALL)
        else: 
            self.stack.append((CodeID.PUSHA, [act._labelId]))
            self._mono(CodeID.CALL)

    def goto(self, label: int):
        self.stack.append((CodeID.JUMP, [label]))

    def jz(self, label: int):
        self.stack.append((CodeID.JZ, [label]))

def variableAccess(bld: CodeTree, n: ast.VariableNode, setMode = False, _apply = True):
    match (n.kind):
        case ast.VariableKind.VARIABLE_ENTIRE:
            # print("MOTHERFUCKING VARIABLE:", n)
            # _nv = SA_STATE["scopes"][0].getSymbolByNameAndKind(n.value)
            # nv = _nv if _nv else n.value

            if (_apply):
                # if (setMode): bld.setVariable(n.value)
                # else: bld.getVariable(n.value)
                if (setMode): bld.setVariable(n.value)
                else: bld.getVariable(n.value)
            else:
                return (n.value, 0)
        case ast.VariableKind.VARIABLE_COMPONENT:
            if (n.ist(ast.IndexedVariableNode)):
                base = variableAccess(bld, n.value, setMode, False)
                lb = emitExpression(bld, n.lbindex)
                # hb = None
                # if (n.hbindex): 
                #     hb = emitExpression(bld, n.hbindex)
                #     bld._mono(CodeID.ADD)

                # print("WHAT THE FUCK IS THIS VARIABLE ACCESS:", n.value.value)
                # print("FUCKING INDEXED VARIABLE ACCESS:", base, lb)
                # print("FUCKING INDEXED VARIABLE ACCESS TREE:", bld)

                if (setMode): bld.setVariableDyn(n.value.value)
                else: bld.getVariableDyn(n.value.value)

_OP_MAP_INT = {
    # Arithmetic Operators
    ast.OpKind.OP_ADD: CodeID.ADD,
    ast.OpKind.OP_SUB: CodeID.SUB,
    ast.OpKind.OP_MUL: CodeID.MUL,
    ast.OpKind.OP_DIV: CodeID.DIV,
    ast.OpKind.OP_MOD: CodeID.MOD,

    # Relational Operators
    ast.OpKind.OP_EQ: CodeID.EQUAL,
    # OP_NEQ: CodeID.NEQ,
    ast.OpKind.OP_LT: CodeID.INF,
    ast.OpKind.OP_LTE: CodeID.INFEQ,
    ast.OpKind.OP_GT: CodeID.SUP,
    ast.OpKind.OP_GTE: CodeID.SUPEQ,
    # OP_IN: CodeID.IN,
}

_OP_MAP_REAL = {
    # Arithmetic Operators
    ast.OpKind.OP_ADD: CodeID.FADD,
    ast.OpKind.OP_SUB: CodeID.FSUB,
    ast.OpKind.OP_MUL: CodeID.FMUL,
    ast.OpKind.OP_DIV: CodeID.FDIV,
    ast.OpKind.OP_MOD: CodeID.MOD,

    # Relational Operators
    ast.OpKind.OP_EQ: CodeID.EQUAL,
    ast.OpKind.OP_LT: CodeID.FINF,
    ast.OpKind.OP_LTE: CodeID.FINFEQ,
    ast.OpKind.OP_GT: CodeID.FSUP,
    ast.OpKind.OP_GTE: CodeID.FSUPEQ,
}

_OP_MAP_COMMON = {
    # Logical Operators
    ast.OpKind.OP_OR: CodeID.OR,
    ast.OpKind.OP_AND: CodeID.AND,
}
def emitExpression(bld: CodeTree, n: ast.ExpressionLikeNode):
    # print("FUCKING EXPRESSION:", bld, n)
    if (n.ist(ast.ExpressionNode)):
        if (n.lhs != None and n.rhs != None):
            emitExpression(bld, n.lhs)
            emitExpression(bld, n.rhs)

            # if (n.staticType == ast.ExpressionStaticType.EXP_BOOLEAN):
            #     op = _OP_MAP_COMMON[n.op.value]
            #     bld._mono(op)
            # elif (n.staticType == ast.ExpressionStaticType.EXP_INTEGER):
            #     op = _OP_MAP_INT[n.op.value]
            #     bld._mono(op)
            # else:
            #     op = _OP_MAP_REAL[n.op.value]
            #     bld._mono(op)

            # print("WHAT FUCKING OPERATION:", n.staticType, n.op.value)
            if (n.staticType == ast.ExpressionStaticType.EXP_INTEGER):
                # op = _OP_MAP_INT[n.op.value]
                op = _OP_MAP_COMMON.get(n.op.value, _OP_MAP_INT.get(n.op.value))
                bld._mono(op)
            else:
                # op = _OP_MAP_REAL[n.op.value]
                op = _OP_MAP_COMMON.get(n.op.value, _OP_MAP_REAL.get(n.op.value))
                bld._mono(op)
        elif (n.lhs != None):
            emitExpression(bld, n.lhs)
        elif (n.rhs != None):
            bld._inst(CodeID.PUSHI, [0])
            bld._mono(_OP_MAP_INT[n.op.value]) # SHOULD only be the unary plus and unary minus operators.
            emitExpression(bld, n.rhs)
    elif (n.ist(ast.ElementDescriptionNode)):
        pass # TODO: Set initialization
    elif (n.ist(ast.SetConstructorNode)):
        pass # TODO: Set initialization
    elif (n.ist(ast.FunctionDesignatorNode)):
        for param in n.params.value:
            emitExpression(bld, param)

        bld.call(n.key.value, n.params.value)
    else:
        if (n.value.ist(ast.UnsignedConstantNode)):
            if (n.value.value.ist(ast.NumberNode)):
                if (n.value.value.isInt()): bld._inst(CodeID.PUSHI, [n.value.value.value])
                else: bld._inst(CodeID.PUSHF, [n.value.value.value])
            elif (n.value.value.ist(ast.StringNode)):
                bld._inst(CodeID.PUSHS, [f"\"{n.value.value.value}\""])
            elif (n.value.value.ist(ast.IdentifierNode)):
                bld.getVariable(n.value.value.value)
            else:
                pass # TODO: SpecialSymbolNode
        elif (n.value.ist(ast.VariableNode)):
            _nv = SA_STATE["scopes"][0].getSymbolByNameAndKind(n.value.value)
            if (_nv):
                if (isinstance(_nv.value, EnumeratedTypeSymbolValue)):
                    bld._inst(CodeID.PUSHI, [_nv.value._ord])
            else:
                variableAccess(bld, n.value)
        else:
            bld.getVariable(n.value.value)

def emitStatement(bld: CodeTree, n: ast.StatementNode):
    if (n._label != None): bld.markLabel(n._label.value)

    if (n.ist(ast.AssignmentStatementNode)):
        emitExpression(bld, n.value)
        variableAccess(bld, n.key, True)
    elif (n.ist(ast.ProcedureStatementNode)):
        for param in n.params.value:
            emitExpression(bld, param)

        bld.call(n.key.value, n.params.value)
    elif (n.ist(ast.GotoStatementNode)):
        bld.goto(n.label.value)
    elif (n.ist(ast.CompoundStatementNode)):
        for stmt in n.value:
            emitStatement(bld, stmt)
    elif (n.ist(ast.ConditionalStatementNode)):
        # print("FUCKING CONDITIONAL:", bld, n)
        emitExpression(bld, n.cond)
        # print("FUCKING CONDITIONAL COND RESULT:", bld)

        el = getLabelId()
        fl = getLabelId()
        bld._inst(CodeID.JZ, [el])

        # If clause
        emitStatement(bld, n.ifStmt)
        bld.goto(fl)

        # Else clause
        bld.markLabel(el)
        if (n.elseStmt != None): emitStatement(bld, n.elseStmt)

        bld.markLabel(fl)

    elif (n.ist(ast.CaseStatementNode)):
        pass # TODO: Not enough time
    elif (n.ist(ast.WhileStatementNode)):
        if (n._label != None): l = n._label.value
        else:
            l = getLabelId()
            bld.markLabel(l)

        el = getLabelId()

        emitExpression(bld, n.cond)
        bld._inst(CodeID.JZ, [el])
        emitStatement(bld, n.body)

        bld.markLabel(el)
        bld.nop()
    elif (n.ist(ast.RepeatStatementNode)):
        pass # TODO: Not enough time
    elif (n.ist(ast.ForStatementNode)):
        # print("MOTHERFUCKING EMIT STATEMENT:", n)
        # print("MOTHERFUCKING TREE:", bld)

        emitExpression(bld, n.initial)
        # variableAccess(bld, n.controlVar, True)
        bld.setVariable(n.controlVar.value)

        _counter = f"@FSN_{getLabelId()}"

        bld.allocVariable(_counter, 1)
        emitExpression(bld, n.final)
        bld.int(1)
        bld._mono(CodeID.ADD)
        bld.setVariable(_counter)

        sl = getLabelId()
        bld.markLabel(sl)
        emitStatement(bld, n.body)

        travMode = n.traversalMode
        # bld.getVariable(_counter)
        # bld.int(1)
        bld.getVariable(n.controlVar.value)
        bld.int(1)
        if (travMode == ast.ForTraversalMode.FOR_TO): bld._mono(CodeID.ADD)
        else: bld._mono(CodeID.SUB)

        bld._inst(CodeID.DUP, [1])
        bld.setVariable(n.controlVar.value)
        bld.getVariable(_counter)
        bld._mono(CodeID.EQUAL)
        bld.jz(sl)


        # el = getLabelId()
        # bld.jz(el)
        # bld.markLabel(el)
        # print("MOTHERFUCKING TREE 2:", bld)

def emitActivatable(obld: CodeTree, n: ProcedureOrFunctionSymbolValue):
    if (n.body == None): return None # Forward declaration

    bld = CodeTree()
    obld._inst(CodeID._SUBTREE, [bld])
    bld.loadArgs(n.parent.heading.params, len(n.params))

    bld.allocVariable(n.parent.heading.name) # Allocate return value
    # # print("EA FUCKING STARTING TREE:", bld)
    
    for nvar in n.body.variables.value:
        for key in nvar.keys:
            # # print("EA FUCKING KEY:", key)
            bld.allocVariable(key.value)

    emitStatement(bld, n.body.stmt)

def __builtin_write(ln: bool, bld: CodeTree, typeHints):
    # print("MOTHERFUCKING BUILTIN WRITE:", ln, typeHints)

    if (typeHints[0].value.ist(ast.UnsignedConstantNode)):
        if (typeHints[0].value.value.ist(ast.NumberNode)):
            if (typeHints[0].value.value.isInt()): bld._mono(CodeID.WRITEI)
            else: bld._mono(CodeID.WRITEF)
        else: 
            bld._mono(CodeID.WRITES)
    elif (typeHints[0].value.ist(ast.IdentifierNode)):
        bld._mono(CodeID.WRITES)
    else:
        variableAccess(bld, typeHints[0].value)
        bld._mono(CodeID.WRITEI)

    if (ln == True): bld._mono(CodeID.WRITELN)


def __builtin_atoi(bld: CodeTree, typeHints):
    bld.stack.pop()
    bld._mono(CodeID.ATOI)

def emitBuiltin(bld: CodeTree):
    root: SymbolTable = SA_STATE["scopes"][0] 
    procedures = root.getSymbolsByKind(SymbolKind.SYM_ACTIVATABLE, True)

    addActivatable("ReadLn", CodeTree.builtin(lambda bld, _ : bld._inst(CodeID.READ, []) ))
    addActivatable("Write", CodeTree.builtin(lambda b, t: __builtin_write(False, b, t)))
    addActivatable("WriteLn", CodeTree.builtin(lambda b, t: __builtin_write(True, b, t)))
    addActivatable("Length", CodeTree.builtin(lambda bld, _ : bld._mono(CodeID.STRLEN)))
    addActivatable("Atoi", CodeTree.builtin(lambda b, t: __builtin_atoi(b, t)))


    # print("FUCKING ACTIVATABLES:", _ACTIVATABLE_MAP)

def emitCode(pout: ast.ProgramNode, outFile):
    bld = CodeTree()

    # Load builtins.
    emitBuiltin(bld)

    # Built-in Table does not have a real presence. Skip it and go to the user root.
    root: SymbolTable = SA_STATE["scopes"][1] 

    # Process root block
    if (pout.body.variables):
        for nvar in pout.body.variables.value:
            # dtype = root.getSymbolByNameAndKind()
            # print("LE FUCKEN VARIABLE:", nvar)
            for key in nvar.keys:
                bld.allocVariable(key.value)

    emitStatement(bld, pout.body.stmt)

    # Process all procedures
    procedures = root.getSymbolsByKind(SymbolKind.SYM_ACTIVATABLE, True)
    for proc in procedures:
        emitActivatable(bld, proc.value)

    # print("FINAL CODE STRUCT:", bld)
    code = transformCode(bld)
    # print("FINAL MOTHERFUCKING CODE:\n", code)

    if (not os.path.exists(os.path.dirname(outFile))): os.mkdir(os.path.dirname(outFile))
    with open(outFile, "w+") as f:
        f.write(code)

def transformCode(bld: CodeTree):
    code = ""

    for p in bld.stack:
        match (p[0]):
            case CodeID._LABEL:
                code += f"L{p[1][0]}: "
            case CodeID._SUBTREE:
                code += transformCode(p[1][0])
            case CodeID.JZ:
                code += f"JZ L{p[1][0]}"
            case CodeID.JUMP:
                code += f"JUMP L{p[1][0]}"
            case _:
                code += f"{p[0].name} "
                if (len(p[1]) > 0): code += " ".join(map(lambda e: f"{e}", p[1]))
        code += "\n"

    return code
