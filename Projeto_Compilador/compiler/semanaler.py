from __future__ import annotations
from typing import overload, Any, Optional
from enum import Enum, auto
import traceback

import compiler.ast as ast
from compiler.sastate import *
from compiler.symbols import *
from compiler.runtime.builtin import *
from .diag import Diagnostic, DiagnosticType, DiagnosticKind, DiagnosticSource

#region ============== AST Utilities =============
def determineNodeBuiltInType(n: ast.Node, scope: SymbolTable, newKey = "@OT_UNKNOWN"):
    tNode = scope.resolvePossibleReference(n)

    if (tNode == None): 
        if (n.ist(ast.EnumeratedTypeNode)): assert s_enumeratedTypeDefinition(n, newKey)
        elif (n.ist(ast.SubrangeTypeNode)): assert s_subrangeTypeDefinition(n, newKey)
        else: return None

        return scope.getLatestSymbol()
    elif (isinstance(tNode, ast.Node)):
        if (tNode.ist(ast.NumberNode)):
            if (tNode.isInt()): return BUILTINS["Integer"]
            else: return BUILTINS["Real"]
    else:
        return tNode.value # It's a symbol, probably builtin. Return it's Node.

def resolveNodeConstantValue(n: ast.Node | Symbol):
    if (isinstance(n, Symbol)):
        if (n.kind == SymbolKind.SYM_CONST): return n.value
    # else:
    #     if (n.ist(ast.NumberNode)): return n.value
    return n
#endregion ============== AST Utilities =============

#region ============== AST Validators =============
#region ------- Compound Primitives -------
def s_directive(n: ast.DirectiveNode):
    match (n.value):
        case "forward":
            return True
        case _:
            raise SemanticError(n, DiagnosticType.UNKNOWN_DIRECTIVE, { "value": n.value })
#endregion ------- Compound Primitives -------

#region ------- Section 3 -------
# Section 3.A
def s_programHeading(n: ast.ProgramHeadingNode):
    # File types are not supported as of the time of writing, therefore it is not possible to verify the externals,
    # ergo the program heading is always valid.
    return True

def s_blockLabels(decLabels: ast.LabelDeclarationNode, defLabels: list[ast.NumberNode]):
    scope = SymbolTable.getCurrentScope()

    tdecLabels = []
    for label in decLabels.value:
        if scope.hasSymbol(label.value, SymbolKind.SYM_LABEL):
            sem_warn(label, DiagnosticType.DUPLICATE_LABEL, { "value": label.value })
        else:
            scope.addSymbol(Symbol(SymbolKind.SYM_LABEL, label.value))
            tdecLabels.append(label)

    declSet = set(tdecLabels)
    deflSet = set(defLabels)

    defNotDec = deflSet - declSet
    decNotDef = declSet - deflSet

    if (decNotDef):
        # There are labels declared that were not used. Warn and proceed.
        for l in decNotDef: sem_warn(l, DiagnosticType.UNUSED_LABEL, { "value": l.value })

    if (defNotDec):
        # There are labels used that were not declared. Error out.
        for l in defNotDec: sem_error(l, DiagnosticType.UNDECLARED_LABEL, { "value": l.value })
        raise SemanticError.empty()

    return True

def s_blockConstants(decConsts: ast.ConstantDefinitionPartNode):
    scope = SymbolTable.getCurrentScope()

    # TODO Assert the values actually exist (e.g. boolean literals, etc)
    for const in decConsts.value:
        if scope.hasSymbol(const.key, SymbolKind.SYM_CONST):
            raise SemanticError(const, DiagnosticType.DUPLICATE_CONST, { "value": const.key })
        else:
            scope.addSymbol(Symbol(SymbolKind.SYM_CONST, const.key, const.value))

    return True

#region ---- Section 3.D ----
def s_enumeratedTypeDefinition(n: ast.EnumeratedTypeNode, nkey: str):
    scope = SymbolTable.getCurrentScope()
    # parentSym = scope.getSymbolById(Symbol._ID)

    # scope.addSymbol(Symbol(SymbolKind.SYM_TYPEDEF, nkey, n.value))
    parentSym = scope.addSymbol(Symbol(SymbolKind.SYM_TYPEDEF, nkey, EnumeratedTypeSymbolValue(n, 0)))

    for t in n.value:
        if scope.hasSymbol(t.value):
            raise SemanticError(t, DiagnosticType.DUPLICATE_TYPE, { "value": t.value })
        else:
            scope.addSymbol(Symbol(SymbolKind.SYM_TYPELIT, t.value, parentSym))
    
    return True

def s_subrangeTypeDefinition(n: ast.SubrangeTypeNode, nkey: str):
    scope = SymbolTable.getCurrentScope()
    parentSym = scope.getSymbolById(Symbol._ID)

    if (isinstance(n, Symbol)): 
        raise SemanticError(BUILTINS["_"], DiagnosticType.TYPE_MISMATCH, { "aType": "OrdinalType", "bType": n.value })
    startValue = scope.resolvePossibleReference(n.start)
    startType = determineNodeBuiltInType(n.start, scope)
    if (startValue == None): raise SemanticError(n, DiagnosticType.UNDEFINED_REFERENCE, { "value": n.start.value })
    
    if (isinstance(n, Symbol)): 
        raise SemanticError(BUILTINS["_"], DiagnosticType.TYPE_MISMATCH, { "aType": "OrdinalType", "bType": n.value })
    endValue = scope.resolvePossibleReference(n.end)
    endType = determineNodeBuiltInType(n.start, scope)
    if (endValue == None): raise SemanticError(n, DiagnosticType.UNDEFINED_REFERENCE, { "value": n.end.value })
    if (startType != endType): 
        raise SemanticError(n, DiagnosticType.TYPE_MISMATCH, { "aType": startType, "bType": endType })

    # scope.removeSymbolById(parentSym.id)
    scope.addSymbol(Symbol(
        SymbolKind.SYM_TYPEDEF, 
        nkey, 
        SubrangeTypeSymbolValue(
            n, 
            resolveNodeConstantValue(startValue), 
            resolveNodeConstantValue(endValue), 
            startType
        )
    ))
    return True

def s_arrayTypeDefinition(n: ast.EnumeratedTypeNode, nkey: str):
    scope = SymbolTable.getCurrentScope()

    rangeSyms = []
    for ri in range(0, len(n.value)):
        r = scope.resolvePossibleReference(n.value[ri])
        if (r == None): raise SemanticError(n, DiagnosticType.UNDEFINED_REFERENCE, { "value": n.value[ri].value.value })
        
        if (isinstance(r, Symbol)): 
            rangeSyms.append(scope.resolvePossibleSymbolReference(r))
        else:
            if (r.ist(ast.OrdinalTypeNode)):
                if (r.ist(ast.EnumeratedTypeNode)): assert s_enumeratedTypeDefinition(r, f"@ART_{nkey}_{ri}")
                elif (r.ist(ast.SubrangeTypeNode)): assert s_subrangeTypeDefinition(r, f"@ART_{nkey}_{ri}")
            else: 
                raise SemanticError(r, DiagnosticType.TYPE_MISMATCH, { "aType": "Constant", "bType": r.kind })

            rangeSyms.append(scope.getLatestSymbol())

    scope.addSymbol(Symbol(
        SymbolKind.SYM_TYPEDEF, 
        nkey, 
        ArrayTypeSymbolValue(
            n, 
            rangeSyms,
            n.basetype
        )
    ))
    return True

def s_recordTypeDefinition(n: ast.RecordTypeNode, nkey: str, variant = False, variantKey = ""):
    scope = SymbolTable.pushScope()

    # Fixed Part
    fixedPart = {}
    if (n.fixedPart != None):
        for vpc in n.fixedPart:
            fsBaseType = determineNodeBuiltInType(vpc.basetype, scope)
    
            for iden in vpc.identifiers:
                if scope.hasSymbol(iden.value, SymbolKind.SYM_ANY, True):
                    raise SemanticError(vpc, DiagnosticType.DUPLICATE_IDENTIFIER, { "value": iden.value })
                else:
                    fixedPart[iden.value] = scope.addSymbol(Symbol(SymbolKind.SYM_ID, iden.value, fsBaseType))

    # Variant Part
    variantPart = {}
    if (n.variantPart != None):
        niden = n.variantPart.identifier
        if (niden != None):
            if scope.hasSymbol(niden, SymbolKind.SYM_ANY):
                raise SemanticError(vpc, DiagnosticType.DUPLICATE_IDENTIFIER, { "value": niden })
        else: niden = ast.IdentifierNode(f"@RTD_VPD_{nkey}")

        baseType = determineNodeBuiltInType(n.variantPart.basetype, scope)
        
        for vpi, vpc in enumerate(n.variantPart.cases):
            for iden in vpc.consts:
                if scope.hasSymbol(iden.value, SymbolKind.SYM_ANY):
                    raise SemanticError(vpc, DiagnosticType.DUPLICATE_IDENTIFIER, { "value": iden.value })
                else:
                    fixedPart[iden.value] = scope.addSymbol(Symbol(SymbolKind.SYM_ID, iden.value, fsBaseType))

            assert s_recordTypeDefinition(vpc, f"@RTD_VPN{variantKey}_{vpi}", True, f"{variantKey}_{vpi}")

    scope.addSymbol(Symbol(SymbolKind.SYM_RECORD, nkey, RecordTypeSymbolValue(n, fixedPart, variantPart)))
    SymbolTable.popScope()
    
    return True

def s_setTypeDefinition(n: ast.SetTypeNode, nkey: str):
    scope = SymbolTable.getCurrentScope()
    parentSym = scope.addSymbol(
        Symbol(SymbolKind.SYM_TYPEDEF, nkey, determineNodeBuiltInType(n, scope, f"@STD_{nkey}"))
    )
    
    return True

def s_pointerTypeDefinition(n: ast.PointerTypeNode, nkey: str):
    scope = SymbolTable.getCurrentScope()
    parentSym = scope.addSymbol(
        Symbol(SymbolKind.SYM_POINTER, nkey, determineNodeBuiltInType(n.basetype, scope))
    )
    
    return True

def s_typeIdentifier(n: ast.TypeIdentifierNode, nkey: str):
    scope = SymbolTable.getCurrentScope()
    scope.addSymbol(Symbol(SymbolKind.SYM_ALIAS, nkey, n.value.value))
    
    return True

def s_type(n, nkey: str):
    scope = SymbolTable.getCurrentScope()

    match (n.kind):
        case ast.TypeKind.TYPE_SIMPLE:
            if (n.ist(ast.EnumeratedTypeNode)): assert s_enumeratedTypeDefinition(n, nkey)
            elif (n.ist(ast.SubrangeTypeNode)): assert s_subrangeTypeDefinition(n, nkey)

            return scope.getLatestSymbol()
        case ast.TypeKind.TYPE_STRUCTURED:
            if (n.ist(ast.ArrayTypeNode)): assert s_arrayTypeDefinition(n, nkey)
            elif (n.ist(ast.RecordTypeNode)): assert s_recordTypeDefinition(n, nkey)
            elif (n.ist(ast.SetTypeNode)): assert s_setTypeDefinition(n, nkey)

            return scope.getLatestSymbol()
        case ast.TypeKind.TYPE_POINTER:
            if (n.ist(ast.PointerTypeNode)): assert s_pointerTypeDefinition(n, nkey)

            return scope.getLatestSymbol()
        case ast.TypeKind.TYPE_IDENTIFIER:
            if (not scope.hasSymbol(n.value.value, SymbolKind.SYM_ANY)):
                raise SemanticError(n, DiagnosticType.UNDEFINED_REFERENCE, { "value": n.value.value })
            return scope.getSymbolByNameAndKind(n.value.value, SymbolKind.SYM_ANY)
    
    return None
    
def s_typeDefinition(n: ast.TypeDefinitionNode):
    scope = SymbolTable.getCurrentScope()
    if scope.hasSymbol(n.key):
        raise SemanticError(n, DiagnosticType.DUPLICATE_TYPE, { "value": n.key })
        
    # scope.addSymbol(Symbol(SymbolKind.SYM_TYPEDEF, n.key, n.value.value))
    
    match (n.value.kind):
        case ast.TypeKind.TYPE_SIMPLE:
            if (n.value.ist(ast.EnumeratedTypeNode)): assert s_enumeratedTypeDefinition(n.value, n.key)
            elif (n.value.ist(ast.SubrangeTypeNode)): assert s_subrangeTypeDefinition(n.value, n.key)
        case ast.TypeKind.TYPE_STRUCTURED:
            if (n.value.ist(ast.ArrayTypeNode)): assert s_arrayTypeDefinition(n.value, n.key)
            elif (n.value.ist(ast.RecordTypeNode)): assert s_recordTypeDefinition(n.value, n.key)
            elif (n.value.ist(ast.SetTypeNode)): assert s_setTypeDefinition(n.value, n.key)
        case ast.TypeKind.TYPE_POINTER:
            if (n.value.ist(ast.PointerTypeNode)): assert s_pointerTypeDefinition(n.value, n.key)
        case ast.TypeKind.TYPE_IDENTIFIER:
            assert s_typeIdentifier(n.value, n.key)
    
    return True

def s_blockTypes(decTypes: ast.TypeDefinitionPartNode):
    scope = SymbolTable.getCurrentScope()

    for btype in decTypes.value:
        if scope.hasSymbol(btype.key):
            raise SemanticError(btype, DiagnosticType.DUPLICATE_TYPE, { "value": btype.key })
        else:
            assert s_typeDefinition(btype)

    return True
#endregion ---- Section 3.D ----

#region ---- Section 3.E ----
def s_blockVariables(decVariables: ast.VariableDeclarationPartNode):
    scope = SymbolTable.getCurrentScope()

    for i, bvar in enumerate(decVariables.value):
        sid = Symbol._getId()
        Symbol._rollbackId()
        typeSym = s_type(bvar.value, f"@BV_{sid}")

        for key in bvar.keys:
            if scope.hasSymbol(key.value):
                raise SemanticError(key, DiagnosticType.DUPLICATE_IDENTIFIER, { "value": key.value })

            scope.addSymbol(Symbol(SymbolKind.SYM_VAR, key.value, typeSym))
    

    return True
#endregion ---- Section 3.E ----

#region ---- Section 3.F ----
def s_procedureOrFunctionHeading(n: ast.ProcedureHeadingNode | ast.FunctionHeadingNode, nkey: str, recKey: str):
    scope = SymbolTable.pushScope(True)

    paramSyms = []
    if (n.params != None):
        for param in n.params:
            if (param.ist(ast.ParameterSpecificationNode)):
                typeSym = s_type(param.basetype, f"@PP_{nkey}")

                for key in param.identifiers:
                    if scope.hasSymbol(key, SymbolKind.SYM_ANY, True):
                        raise SemanticError(param, DiagnosticType.DUPLICATE_IDENTIFIER, { "value": key })
                    
                    sym = scope.addSymbol(Symbol(SymbolKind.SYM_PARAM, key, typeSym))
                    paramSyms.append(typeSym)
            else: 
                nestedSyms = s_procedureOrFunctionHeading(param, n.name, f"{recKey}_{recKey}")
                paramSyms = paramSyms + nestedSyms
                # typeSym = scope.getLatestSymbol()
                typeSym = None

            # scope.addSymbol(
            #     Symbol(SymbolKind.SYM_ACTIVATABLE, nkey, ProcedureOrFunctionParameterSymbolValue(param, typeSym))
            # )

    return paramSyms

# These fuckers are one and the same, except procedures have no return type and can be forward declared.
def s_procedureOrFunctionCommon(n: ast.ProcedureDeclarationNode | ast.FunctionDeclarationNode):
    scope = SymbolTable.getCurrentScope()

    if scope.hasSymbol(n.heading.name):
        raise SemanticError(n, DiagnosticType.DUPLICATE_IDENTIFIER, { "value": n.heading.name })

    parentSym = scope.addSymbol(Symbol(SymbolKind.SYM_ACTIVATABLE, n.heading.name))

    # Process Heading
    paramSyms = s_procedureOrFunctionHeading(n.heading, n.heading.name, f"@PP_{n.heading.name}")
    nscope = SymbolTable.getCurrentScope()
    nscope.addSymbol(parentSym)
    nscope._procedure = n.heading.name

    # print("LE FUCKING NSCOPE:", nscope)

    retType = None
    if (n.ist(ast.FunctionDeclarationNode)):
        retType = scope.resolvePossibleReference(n.heading.rettype)

    # Process Body
    if (n.body.ist(ast.BlockNode)):
        assert s_block(n.body)
        parentSym.value = ProcedureOrFunctionSymbolValue(n, paramSyms, retType, n.body)
    else:
        if (n.body.value == "Forward"): 
            # If I have time, I'll come back to this, but I don't think I'll even have time to fucking breathe, let 
            # alone handle this bullshit.
            parentSym.value = ProcedureOrFunctionSymbolValue(n, paramSyms, retType, None)
            pass
        else:
            raise SemanticError(n, DiagnosticType.UNKNOWN_DIRECTIVE, { "value": n.body.value })

    SymbolTable.popScope(True)

    # scope.addSymbol(parentSym)
    return True

def s_blockSubFuncs(decSubfuncs: ast.ProcedureAndFunctionDeclarationPartNode):
    scope = SymbolTable.getCurrentScope()

    for bsub in decSubfuncs.value:
        s_procedureOrFunctionCommon(bsub)

    return True
#endregion ---- Section 3.F ----

def s_block(n: ast.BlockNode):
    if (n.labels != None): assert s_blockLabels(n.labels, n.stmt.getLabels())
    if (n.consts != None): assert s_blockConstants(n.consts)
    if (n.types != None): assert s_blockTypes(n.types)
    if (n.variables != None): assert s_blockVariables(n.variables)
    if (n.subfuncs != None): assert s_blockSubFuncs(n.subfuncs)

    # print("FUCKING BLOCK SCOPES:", SA_STATE["scopes"])
    # assert s_assignmentStatement(n.stmt.value[2])
    assert s_compoundStatement(n.stmt)

    # TODO: RTFM and do the rest of the fucking owl.
    return True
#endregion ------- Section 3 -------

#region ------- Section R8 -------
def evaluateVariableType(n: ast.VariableNode):
    scope = SymbolTable.getCurrentScope()

    # print("FUCKING VARIABLE:", n)
    if (n.ist(ast.EntireVariableNode)):
        # print("FUCKING ENTIRE VARIABLE TYPE:", scope.resolvePossibleReference(n.value).value.value)
        return scope.resolvePossibleReference(n.value).value.value
    elif (n.ist(ast.IndexedVariableNode)):
        pass # TODO If I have the fucking time
    

def evaluateExpressionType(n: ast.ExpressionLikeNode):
    scope = SymbolTable.getCurrentScope()

    # print("FUCKING EXPRESSION TYPE:", n)
    if (n.ist(ast.ExpressionNode)):
        if (n.lhs != None): return evaluateExpressionType(n.lhs)
        else: return evaluateExpressionType(n.rhs)
    elif (n.ist(ast.FunctionDesignatorNode)):
        assert s_activation(n)
    else: # Actually an ExpressionLikeNode, not a descendent
        if (n.value.ist(ast.UnsignedConstantNode)):
            if (n.value.value.ist(ast.NumberNode)):
                return BUILTINS["Integer"] if n.value.value.isInt() else BUILTINS["Real"]
            elif (n.value.value.ist(ast.StringNode)): return BUILTINS["String"]
            elif (n.value.value.ist(ast.IdentifierNode)):
                return scope.resolvePossibleReference(n.value.value)
            else:
                return BUILTINS["Nil"]
        elif (n.value.ist(ast.VariableNode)):
            return evaluateVariableType(n.value)
        else: 
            return scope.resolvePossibleReference(n.value.value)

def s_expression(n: ast.ExpressionLikeNode):
    scope = SymbolTable.getCurrentScope()

    if (n.ist(ast.ExpressionNode)):
        if (n.lhs != None):
            lhsType = evaluateExpressionType(n.lhs)
            rhsType = evaluateExpressionType(n.rhs)
            if (not lhsType.value.typeEquals(rhsType.value)):
                raise SemanticError(
                    n, DiagnosticType.TYPE_MISMATCH, 
                    { "aType": actSym.value.params[i].value.value, "bType": exprParamType.value }
                )
    elif (n.ist(ast.FunctionDesignatorNode)):
        # if (not scope.hasSymbol(n.key.value, SymbolKind.SYM_ACTIVATABLE)):
        #     raise SemanticError(n, DiagnosticType.UNDECLARED_ACTIVATABLE, { "value": n.key.value })

        # actSym = scope.getSymbolByNameAndKind(n.key.value, SymbolKind.SYM_ACTIVATABLE)
        # # print("FUCKING FUNCTION:", actSym.value.params)
        # # print("FUCKING FUNCTION ACTIVATION:", n.params)

        # for i, param in enumerate(n.params.value):
        #     # print("EVALUATING THE FUCKING EXPRESSION PARAM:", param)
        #     exprParamType = evaluateExpressionType(param)
        #     # print("FUCKING EXPRESSION PARAM TYPE:", exprParamType)

        #     # print("FUCKING FUCK:", actSym.value.params[i].value.value, exprParamType)
        #     if (not actSym.value.params[i].value.value.typeEquals(exprParamType.value)):
        #         raise SemanticError(
        #             n, DiagnosticType.TYPE_MISMATCH, 
        #             { "aType": actSym.value.params[i].value.value, "bType": exprParamType.value }
        #         )
        assert s_activation(n)

    return True
#endregion ------- Section R8 -------

#region ------- Section R9 -------
def s_activation(n: ast.FunctionDesignatorNode):
    scope = SymbolTable.getCurrentScope()

    if (not scope.hasSymbol(n.key.value, SymbolKind.SYM_ACTIVATABLE)):
        raise SemanticError(n, DiagnosticType.UNDECLARED_ACTIVATABLE, { "value": n.key.value })

    actSym = scope.getSymbolByNameAndKind(n.key.value, SymbolKind.SYM_ACTIVATABLE)
    # print("FUCKING FUNCTION:", actSym.value.params)
    # print("FUCKING FUNCTION ACTIVATION:", n)

    for i, param in enumerate(n.params.value):
        # # print("EVALUATING THE FUCKING EXPRESSION PARAM:", param)
        exprParamType = evaluateExpressionType(param)
        # print("FUCKING EXPRESSION PARAM TYPE:", exprParamType)

        if (len(actSym.value.params) > 0):
            # print("FUCKING FUCK:", actSym.value.params[i].value, exprParamType, scope.resolvePossibleSymbolReference(exprParamType))
            if (not actSym.value.params[i].value.typeEquals(exprParamType)):
                raise SemanticError(
                    n, DiagnosticType.TYPE_MISMATCH, 
                    { "aType": actSym.value.params[i].value, "bType": exprParamType }
                )
    
    return True
    

def s_variableAccess(n: ast.VariableNode):
    scope = SymbolTable.getCurrentScope()
    
    match (n.kind):
        case ast.VariableKind.VARIABLE_ENTIRE:
            # Enable assignment to the identifier of the procedure itself.
            if (
                not scope.hasSymbol(n.value, SymbolKind.SYM_VAR) 
                and not (scope.hasSymbol(n.value, SymbolKind.SYM_ACTIVATABLE) and n.value == scope._procedure)
            ):
                raise SemanticError(n, DiagnosticType.UNDECLARED_VARIABLE, { "value": n.value })
        case ast.VariableKind.VARIABLE_COMPONENT:
            if (n.ist(ast.IndexedVariableNode)):
                base = s_variableAccess(n.value)
                assert base != None

                # Ensure base variable is an array type
                if (n.value.staticType != ast.VariableStaticType.VARIABLE_ST_ARRAY):
                    raise SemanticError(
                        n.key, DiagnosticType.INCOMPATIBLE_VARIABLE, 
                        { 
                            "expected": ast.VariableStaticType.VARIABLE_ST_ARRAY,
                            "actual": n.value.staticType
                        }
                    )

                # Ensure Low and High bound expressions
                # TODO
                
            else:
                key = None
                if (n.key.ist(ast.IdentifierNode)):
                    if (not scope.hasSymbol(n.key.value, SymbolKind.SYM_VAR)):
                        raise SemanticError(n.key, DiagnosticType.UNDECLARED_VARIABLE, { "value": n.key.value })

                    key = scope.resolvePossibleSymbolReference(
                        scope.getSymbolByNameAndKind(n.key.value, SymbolKind.SYM_VAR)
                    )
                else:
                    assert s_variableAccess(n.key)
                    key = n.keys
                
                # TODO: Assert and extract record type and assert that a property with that name exists.
        case ast.VariableKind.VARIABLE_IDENTIFIED:
            # TODO
            pass 

    return True          

def s_statement(n: ast.StatementNode):
    scope = SymbolTable.getCurrentScope()

    if (n._label and not scope.hasSymbol(n._label.value, SymbolKind.SYM_LABEL)):
        raise SemanticError(n, DiagnosticType.UNDECLARED_LABEL, { "value": n._label.value })

    return True

def s_assignmentStatement(n: ast.AssignmentStatementNode):
    scope = SymbolTable.getCurrentScope()

    # Process Label
    assert s_statement(n)

    key = None
    if (n.key.ist(ast.IdentifierNode)):
        if (not scope.hasSymbol(n.key.value, SymbolKind.SYM_VAR)):
                raise SemanticError(n, DiagnosticType.UNDECLARED_VARIABLE, { "value": n.key.value })
    else:
        assert s_variableAccess(n.key)

    assert s_expression(n.value)
    return True

def s_activationStatement(n: ast.ProcedureStatementNode):
    scope = SymbolTable.getCurrentScope()

    # Process Label
    assert s_statement(n)
    assert s_activation(n)
    return True

def s_gotoStatement(n: ast.GotoStatementNode):
    scope = SymbolTable.getCurrentScope()

    if (not scope.hasSymbol(n.value.value, SymbolKind.SYM_LABEL)):
                raise SemanticError(n, DiagnosticType.UNDECLARED_LABEL, { "value": n.value.value })

def s_compoundStatement(n: ast.CompoundStatementNode):
    for stmt in n.value:
        if (stmt.ist(ast.AssignmentStatementNode)): assert s_assignmentStatement(stmt)
        elif (stmt.ist(ast.ProcedureStatementNode)): assert s_activationStatement(stmt)
        elif (stmt.ist(ast.GotoStatementNode)): assert s_gotoStatement(stmt)

    return True

#endregion ------- Section R9 -------
#endregion ============== AST Validators =============

def analyzeSemantics(n: ast.ProgramNode):
    reset()
    registerBuiltin()

    try:
        SymbolTable.pushScope()
        assert s_programHeading(n.heading)
        assert s_block(n.body)

        # # print(SA_STATE["scopes"])
        # # print(SA_STATE["scopes"][1].__repr__(0, True))
        # print(*list(map(lambda s : s.__repr__(0, True), SA_STATE["scopes"])))

        # # print(SA_STATE["scopes"][0].syms[0].value.op_add(ast.NumberNode("123.4", ast.NumberKind.UNSIGNED_REAL), ast.NumberNode("456.6", ast.NumberKind.UNSIGNED_REAL)))
        # # print(SA_STATE["scopes"][0].syms[3].value.op_sub(ast.IdentifierNode("a"), ast.IdentifierNode("A")))
        # # print(SA_STATE["scopes"][0].syms[3].value.chr(ast.NumberNode(65, ast.NumberKind.UNSIGNED_INTEGER)))

        return True
    except Exception:
        if (SA_STATE["debug"]):
            print(f"\x1b[31mBASE SEMANTIC ERROR:\x1b[0m")
            traceback.print_exc()

        # Every time a SemanticError is initialized, it's corresponding diagnostic is automatically handled.
        # This try/match only prevents the exception from bubbling up further if it's not handled.
        return False
