#
# This module contains the internal state of the Semantic Analyser (semanaler.py). It was extracted because the Symbol 
# / Symbol Table requires it, and they had to be extracted into their own module because the builtin symbols are defined
# on their own module.
#
from inspect import getframeinfo, stack

import compiler.ast as ast
from compiler.diag import Diagnostic, DiagnosticType, DiagnosticKind, DiagnosticSource

SA_STATE = {
    "diagnostics": [],
    "debug": False,

    "scopes": []
}

def reset():
    SA_STATE = {
        "diagnostics": [],
        "debug": False,

        "scopes": []
    }

#region -------------- Diagnostics --------------
class SemanticError(Exception):
    diag: Diagnostic
    def __init__(self, n: ast.Node, dType: DiagnosticType, dArgs, _emit = True):
        if (n != None): self.diagnostic = sem_error(n, dType, dArgs, _emit)

    @classmethod
    def empty(cls):
        return cls(None, None, None)

    @classmethod
    def noemit(cls, n: ast.Node, dType: DiagnosticType, dArgs):
        return cls(n, dType, dArgs, False)

def sem_error(n: ast.Node, dType: DiagnosticType, dArgs, emit = True):
    caller = getframeinfo(stack()[1][0])

    diag = emitDiagnostic(
        n, 
        dType, 
        DiagnosticKind.ERROR, 
        dArgs,
        emit
    )

    if (emit):
        header = f"[{caller.filename}:{caller.lineno}] " if SA_STATE["debug"] else ""
        print(
            f"\x1b[31m{header}SEMANTIC ERROR {n.pos.fullString}:\x1b[0m" \
            f" {diag.toString(None, emitMark = False, emitPos = False)}"
        )

    return diag

def sem_warn(n: ast.Node, dType: DiagnosticType, dArgs, emit = True):
    caller = getframeinfo(stack()[1][0])

    diag = emitDiagnostic(
        n, 
        dType, 
        DiagnosticKind.WARN, 
        dArgs,
        emit
    )

    if (emit):
        header = f"[{caller.filename}:{caller.lineno}] " if SA_STATE["debug"] else ""
        print(
            f"\x1b[33m{header}SEMANTIC WARNING {n.pos.fullString}:\x1b[0m" \
            f" {diag.toString(None, emitMark = False, emitPos = False)}"
        )

    return diag

# This function emits a semantic diagnostic. Diagnostics are defined on the property "diagnostics" on SA_STATE.
def emitDiagnostic(
    node: ast.Node,
    dtype: DiagnosticType, 
    dkind: DiagnosticKind = DiagnosticKind.INFO,
    args = {},
    addToState = True
):
    rcStartPos = node.pos.getStart()
    rcEndPos = node.pos.getEnd()

    diag = Diagnostic(DiagnosticSource.SEMANAL, dtype, dkind, rcStartPos, rcEndPos, args)
    if (addToState): SA_STATE["diagnostics"].append(diag)

    return diag

def getDiagnostics() -> list[Diagnostic]:
    return SA_STATE["diagnostics"]
#endregion -------------- Diagnostics --------------

