const NODE_BASE_KEYS = ["types", "pos", "value"];

//#region ============== Element Helpers ==============
function createFieldElem(key, qualifiedKey, value, parentElement) {
    const fieldElem = document.createElement("div");
    fieldElem.classList.add("field");
    fieldElem.setAttribute("name", key);

    const nameElem = document.createElement("div");
    nameElem.classList.add("field-name");
    nameElem.innerText = `${qualifiedKey}:`;

    const valueElem = document.createElement("div");
    valueElem.classList.add("field-value");
    if (Array.isArray(value)) {
        const ul = document.createElement("ul");
        for (const v of value) {
            const li = document.createElement("li");
            li.innerText = v;
            ul.append(li);
        }

        valueElem.append(ul);
    } else {
        valueElem.innerText = value;
    }

    fieldElem.append(nameElem);
    fieldElem.append(valueElem);

    parentElement.append(fieldElem);
    return fieldElem;
}

function createErrorFieldElem(err, parentElement) {
    const errElem = createFieldElem("error", "Error", err, parentElement);
    errElem.classList.add("error"); // , "standalone"

    parentElement.append(errElem);
    return errElem;
}

function createPropElem(key, qualifiedKey, value, parentElement, nested, collapsed) {
    const propElem = document.createElement("div");
    propElem.classList.add("prop");
    if (nested) propElem.classList.add("no-border", "no-chevron");
    propElem.setAttribute("name", key);

    const nameElem = document.createElement("div");
    nameElem.classList.add("prop-name");
    nameElem.innerText = `${qualifiedKey}:`;

    const bodyElem = document.createElement("div");
    bodyElem.classList.add("prop-body");
    if (collapsed) bodyElem.classList.add("no-border", "collapsed");

    propElem.append(nameElem);
    propElem.append(bodyElem);

    if (value !== undefined) {
        for (const key in value) {
            // If value[key] is a nested object, it should be handled by a recursive call to createPropElem by the
            // parent. It would overcomplicate the everliving shit out of the logic for this function if I handled
            // it implicitly.
            createFieldElem(key, value[key]);
        }
    }

    parentElement.append(propElem);
    return {
        base: propElem,
        name: nameElem,
        body: bodyElem
    };
}

function createASTNodeElem(nested = false) {
    const nodeElem = document.createElement("div");
    nodeElem.classList.add("ast-node");
    if (nested) nodeElem.classList.add("no-border", "no-chevron");

    const typeElem = document.createElement("div");
    typeElem.classList.add("type");
    typeElem.setAttribute("name", "type");

    const bodyElem = document.createElement("div");
    bodyElem.classList.add("body");
    bodyElem.setAttribute("name", "body");

    nodeElem.append(typeElem);
    nodeElem.append(bodyElem);

    return {
        base: nodeElem,
        type: typeElem,
        body: bodyElem
    };
}

function createASTErrorNodeElem(name, err, parentElement, nested) {
    const nodeElem = createASTNodeElem(nested);

    const errElem = createFieldElem("error", "Error", err, nodeElem.body);
    errElem.classList.add("error")

    parentElement.append(nodeElem.base);
    return nodeElem;
}
//#endregion ============== Element Helpers ==============


//#region ============== Node Processors Helpers ==============
/**
 * 
 * @param {object} node 
 * @param {object} nodeElem 
 * @param {string} key The property key on the node.
 * @param {string} qualifiedKey The formatted label to be shown on the AST node.
 * @param {(e: ReturnType<typeof createPropElem>, value: object) => void} callback Callback to add values to the prop.
 * @returns 
 */
function addNodePropOrError(node, nodeElem, key, qualifiedKey, callback) {
    const propElem = createPropElem(key, qualifiedKey, undefined, nodeElem, false, true);
    if (node[key] === undefined || node[key] === null) {
        createErrorFieldElem(`Missing property: ${key}`, propElem.body);
    } else {
        callback(propElem, node[key]);
        return propElem;
    }
}

/**
 * 
 * @param {object} node 
 * @param {object} nodeElem 
 * @param {string} key The property key on the node.
 * @param {string} qualifiedKey The formatted label to be shown on the AST node.
 * @param {(e: ReturnType<typeof createPropElem>, value: object) => void | undefined} callback 
 *  Callback to add values to the prop.
 * @returns 
 */
function addNodeSubnodeOrError(node, nodeElem, key, qualifiedKey, noexpand, callback) {
    return addNodePropOrError(node, nodeElem, key, qualifiedKey, (e, v) => {
        if (callback) callback(e, v);
        else e.body.append(processNode(v, noexpand).base)
    });
}
/**
 * 
 * @param {object} node 
 * @param {object} nodeElem 
 * @param {string} key The property key on the node.
 * @param {string} qualifiedKey The formatted label to be shown on the AST node.
 * @param {(e: ReturnType<typeof createPropElem>, value: object) => void | undefined} callback 
 *  Callback to add values to the prop.
 * @returns 
 */
function addNodeSubnodeOptional(node, nodeElem, key, qualifiedKey, noexpand, callback) {
    if (!node[key]) {
        const fieldElem = createFieldElem(key, qualifiedKey, "null", nodeElem);
        // fieldElem.classList.add("standalone");
    } else {
        const propElem = createPropElem(key, qualifiedKey, undefined, nodeElem, false, true);
        // propElem.body.append(processNode(node[key], true).base);
        if (callback) callback(propElem, node[key]);
        else propElem.body.append(processNode(node[key], noexpand).base);
        return propElem;
    }
}

function addNodeFieldOrError(node, nodeElem, key, qualifiedKey, value = undefined) {
    if (node[key] === undefined || node[key] === null) {
        return createErrorFieldElem(`Missing property: ${key}`, nodeElem);
    } else {
        const _value = value === undefined ? node[key] : value;
        return createFieldElem(key, qualifiedKey, _value, nodeElem);
    }
}

function addNodeFieldOptional(node, nodeElem, key, qualifiedKey, value = undefined) {
    if (node[key] === undefined || node[key] === null) {
        return createFieldElem(key, qualifiedKey, "null", nodeElem);
    } else {
        const _value = value === undefined ? node[key] : value;
        return createFieldElem(key, qualifiedKey, _value, nodeElem);
    }
}
//#endregion ============== Node Processors Helpers ==============

//#region ============== Node Processors ==============
function _processDefaultNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "value", "Value");
}

const NumberNodeKind = {
    1: "UNSIGNED_REAL",
    2: "UNSIGNED_INTEGER",
    3: "SIGNED_REAL",
    4: "SIGNED_INTEGER",
};
function processNumberNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "value", "Value");
    addNodeFieldOrError(node, nodeElem, "kind", "Kind", `${NumberNodeKind[node.kind]} (${node.kind})`);
}

function processUnsignedConstantNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true);
}

const SpecialSymbolKind = {
    1: "SS_NIL",
};
function processSpecialSymbolNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "value", "Value", `${SpecialSymbolKind[node.value]} (${node.value})`);
}

function processLabelDeclarationNode(node, nodeElem) {
    // addNodeFieldOrError(node, nodeElem, "value", "Value");
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true, (e, v) => {
        for (const key of v) {
            e.body.append(processNode(key, false).base)
        }
    });
}

//#region -------------- Section 3.C --------------
function processConstantDefinitionNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "type", "Type");
    addNodeFieldOrError(node, nodeElem, "key", "Key");
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true);
}

function processConstantDefinitionPartNode(node, nodeElem) {
    // addNodeFieldOrError(node, nodeElem, "type", "Type");
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, true).base)
        }
    });
}
//#endregion -------------- Section 3.C --------------

//#region -------------- Section 3.D --------------
const TypeKind = {
    1: "TYPE_UNKNOWN",
    2: "TYPE_SIMPLE",
    3: "TYPE_STRUCTURED",
    4: "TYPE_POINTER",
    5: "TYPE_IDENTIFIER",
};

function processTypeIdentifierNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Type Root", `${TypeKind[node.kind]} (${node.kind})`);
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true);
}

//#region ------- Simple Types -------
function processEnumeratedTypeNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Type Root", `${TypeKind[node.kind]} (${node.kind})`);
    // addNodeFieldOrError(node, nodeElem, "value", "Fields");
    addNodeSubnodeOrError(node, nodeElem, "value", "Fields", true, (e, v) => {
        for (const field of v) {
            if (!field) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(field, false).base)
        }
    });
}

function processSubrangeTypeNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Type Root", `${TypeKind[node.kind]} (${node.kind})`);
    addNodeSubnodeOrError(node, nodeElem, "start", "Start", true);
    addNodeSubnodeOrError(node, nodeElem, "end", "End", true);
}
//#endregion ------- Simple Types -------

//#region ------- Structured Types -------
function processArrayTypeNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Type Root", `${TypeKind[node.kind]} (${node.kind})`);
    addNodeFieldOrError(node, nodeElem, "packed", "Packed");
    // addNodeFieldOrError(node, nodeElem, "type", "Base Type");
    addNodeSubnodeOrError(node, nodeElem, "basetype", "Base Type", true);
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, false).base)
        }
    });
}

//#region ---- Record Type ----
function processRecordSectionNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "basetype", "Base Type", true);
    addNodeSubnodeOrError(node, nodeElem, "identifiers", "Identifiers", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, false).base)
        }
    });
}

function processRecordVariantCaseNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "consts", "Identifiers", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, false).base)
        }
    });
    addNodeSubnodeOptional(node, nodeElem, "fixedPart", "Fixed Fields", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, false).base)
        }
    });
    addNodeSubnodeOptional(node, nodeElem, "variantPart", "Variant Field", true);
}

function processRecordVariantNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "basetype", "Base Type", true);
    // addNodeSubnodeOrError(node, nodeElem, "identifier", "Identifier", true);
    addNodeFieldOrError(node, nodeElem, "identifier", "Identifier");
    addNodeSubnodeOrError(node, nodeElem, "cases", "Cases", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, false).base)
        }
    });
}

function processRecordTypeNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Type Root", `${TypeKind[node.kind]} (${node.kind})`);
    addNodeFieldOrError(node, nodeElem, "packed", "Packed");
    addNodeSubnodeOptional(node, nodeElem, "fixedPart", "Fixed Fields", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, false).base)
        }
    });
    addNodeSubnodeOptional(node, nodeElem, "variantPart", "Variant Field", true);
}
//#endregion ---- Record Type ----

function processSetTypeNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Type Root", `${TypeKind[node.kind]} (${node.kind})`);
    addNodeFieldOrError(node, nodeElem, "packed", "Packed");
    addNodeSubnodeOrError(node, nodeElem, "basetype", "Base Type", true);
}
//#endregion ------- Structured Types -------

//#region ------- Pointer Types -------
function processPointerTypeNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Type Root", `${TypeKind[node.kind]} (${node.kind})`);
    addNodeSubnodeOrError(node, nodeElem, "basetype", "Base Type", true);
}
//#endregion ------- Pointer Types -------

function processTypeDefinitionNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "key", "Key");
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true);
}

function processTypeDefinitionPartNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, false).base)
        }
    });
}
//#endregion -------------- Section 3.D --------------

//#region -------------- Section 3.E --------------
function processVariableDeclarationNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "keys", "Keys", true, (e, v) => {
        for (const key of v) {
            e.body.append(processNode(key, false).base)
        }
    });    
    addNodeSubnodeOrError(node, nodeElem, "value", "Type", true);
}

function processVariableDeclarationPartNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, true).base)
        }
    });
}
//#endregion -------------- Section 3.E --------------


//#region -------------- Section 11 --------------
function processIndexTypeSpecificationNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "name", "Key");
    addNodeFieldOrError(node, nodeElem, "lb", "Lower Bound");
    addNodeFieldOrError(node, nodeElem, "hb", "Higher Bound");
}

function processConformantArraySchema(node, nodeElem) {
    if (node.type === "PackedConformantArraySchemaNode") processPackedConformantArraySchemaNode(node, nodeElem);
    else if (node.type === "UnpackedConformantArraySchemaNode") processUnpackedConformantArraySchemaNode(node, nodeElem);
}
function processPackedConformantArraySchemaNode(node, nodeElem) {
    createFieldElem("packed", "Packed", true, nodeElem);
    addNodeFieldOrError(node, nodeElem, "name", "Name");
    addNodeSubnodeOrError(node, nodeElem, "specification", "Specification", true);
}
function processUnpackedConformantArraySchemaNode(node, nodeElem) {
    createFieldElem("packed", "Packed", false, nodeElem);
    addNodeFieldOrError(node, nodeElem, "name", "Name");
    addNodeSubnodeOrError(node, nodeElem, "specification", "Specification", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, true).base)
        }
    });
}

function processParameterSpecificationNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "identifiers", "Identifiers");
    addNodeFieldOrError(node, nodeElem, "variable", "Variable");
    // addNodeSubnodeOrError(node, nodeElem, "basetype", "Base Type", true , (e, v) => {
    //     if (v.type === "TypeIdentifierNode") {
    //         e.body.append(processNode(constant, true).base)
    //     } else {
    //         processConformantArraySchema(v, e);
    //     }
    // });
    addNodeSubnodeOrError(node, nodeElem, "basetype", "Base Type", true);
}

function processActualParameterListNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true, (e, v) => {
        for (const stmt of v) {
            if (!stmt) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(stmt, true).base)
        }
    });
}
//#region ------- Procedure -------
function processProcedureHeadingNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "name", "Name");
    addNodeSubnodeOptional(node, nodeElem, "params", "Parameters", true, (e, v) => {
        for (const param of v) {
            if (!param) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(param, true).base)
        }
    });
}

function processProcedureDeclarationNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "heading", "Heading", true);
    addNodeSubnodeOrError(node, nodeElem, "body", "Body", true);
}
//#endregion ------- Procedure -------

//#region ------- Function -------
function processFunctionHeadingNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "name", "Name");
    addNodeSubnodeOptional(node, nodeElem, "params", "Parameters", true, (e, v) => {
        for (const param of v) {
            if (!param) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(param, true).base)
        }
    });
    addNodeSubnodeOptional(node, nodeElem, "rettype", "Return Type", true);
}

function processFunctionDeclarationNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "heading", "Heading", true);
    addNodeSubnodeOrError(node, nodeElem, "body", "Body", true);
}
//#endregion ------- Function -------

function processProcedureAndFunctionDeclarationPartNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true, (e, v) => {
        for (const constant of v) {
            if (!constant) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(constant, false).base)
        }
    });
}
//#endregion -------------- Section 11 --------------

//#region -------------- Section R7 --------------
const VariableKind = {
    1: "VARIABLE_UNKNOWN",
    2: "VARIABLE_ENTIRE",
    3: "VARIABLE_COMPONENT",
    4: "VARIABLE_IDENTIFIED",
};
const VariableStaticType = {
    1: "VARIABLE_ST_UNKNOWN",
    2: "VARIABLE_ST_ARRAY",
    3: "VARIABLE_ST_RECORD",
    4: "VARIABLE_ST_POINTER",
};

function _processVariableNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Kind", true, `${VariableKind[node.kind]} (${node.kind})`);
    addNodeFieldOptional(
        node, nodeElem, 
        "staticType", "Static Type", true, 
        `${VariableStaticType[node.kind]} (${node.kind})`
    );
}

function processEntireVariableNode(node, nodeElem) {
    _processVariableNode(node, nodeElem);
    addNodeFieldOrError(node, nodeElem, "value", "Value");
}

function processIndexedVariableNode(node, nodeElem) {
    _processVariableNode(node, nodeElem);
    addNodeSubnodeOrError(node, nodeElem, "lbindex", "Low Index");
    addNodeSubnodeOptional(node, nodeElem, "hbindex", "High Index");
    addNodeSubnodeOrError(node, nodeElem, "value", "Value");
}

function processFieldDesignatorNode(node, nodeElem) {
    _processVariableNode(node, nodeElem);
    addNodeSubnodeOrError(node, nodeElem, "key", "Key");
    addNodeSubnodeOrError(node, nodeElem, "value", "Value");
}

function processIdentifiedVariableNode(node, nodeElem) {
    _processVariableNode(node, nodeElem);
    addNodeSubnodeOrError(node, nodeElem, "value", "Value");
}
//#endregion -------------- Section R7 --------------

//#region -------------- Section R8 --------------
const OpKind = {
    1: "OP_ADD",
    2: "OP_SUB",
    3: "OP_MUL",
    4: "OP_DIV",
    5: "OP_MOD",
    6: "OP_OR",
    7: "OP_AND",
    8: "OP_EQ",
    9: "OP_NEQ",
    10: "OP_LT",
    11: "OP_LTE",
    12: "OP_GT",
    13: "OP_GTE",
    14: "OP_IN",
};

const ExpressionKind = {
    1: "EXP_UNARY",
    2: "EXP_BINARY"
};

const ExpressionStaticType = {
    1: "EXP_ORDINAL",
};

function processOpNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "value", "Value", `${OpKind[node.value]}`);
}

function processExpressionLikeNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Expression Kind", `${ExpressionKind[node.kind]}`);
    addNodeFieldOptional(node, nodeElem, "staticType", "Static Type", `${ExpressionStaticType[node.staticType]}`);
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true);
}

function processExpressionNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Expression Kind", `${ExpressionKind[node.kind]}`);
    addNodeFieldOptional(node, nodeElem, "staticType", "Static Type", `${ExpressionStaticType[node.staticType]}`);
    // addNodeFieldOrError(node, nodeElem, "op", "Operation", `${OpKind[node.op.value]}`);
    addNodeSubnodeOrError(node, nodeElem, "op", "Operation", false);
    addNodeSubnodeOptional(node, nodeElem, "lhs", "Left-hand Side", false);
    addNodeSubnodeOptional(node, nodeElem, "rhs", "Right-hand Side", false);
}

function processElementDescriptionNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "start", "Start", false);
    addNodeSubnodeOptional(node, nodeElem, "end", "End", false);
}

function processSetConstructorNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "value", "Value", true, (e, v) => {
        for (const stmt of v) {
            if (!stmt) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(stmt, true).base)
        }
    });
}

function processFunctionDesignatorNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "kind", "Expression Kind", `${ExpressionKind[node.kind]}`);
    addNodeFieldOptional(node, nodeElem, "staticType", "Static Type", `${ExpressionStaticType[node.staticType]}`);
    addNodeSubnodeOptional(node, nodeElem, "key", "Key", true);
    addNodeSubnodeOptional(node, nodeElem, "params", "Params", true);
}
//#endregion -------------- Section R8 --------------

//#region -------------- Section R9 --------------
//#region ------- Section 9.1 -------
function processAssignmentStatementNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "_label", "Label");
    addNodeSubnodeOrError(node, nodeElem, "key", "Key", true);
    addNodeSubnodeOrError(node, nodeElem, "value", "Value", true);
}

function processProcedureStatementNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "_label", "Label");
    addNodeSubnodeOrError(node, nodeElem, "key", "Key", true);
    addNodeSubnodeOptional(node, nodeElem, "value", "Value", true);
}

function processGotoStatementNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "_label", "Label");
    addNodeSubnodeOrError(node, nodeElem, "value", "Label", true);
}
//#endregion ------- Section 9.1 -------

//#region ------- Section 9.2 -------
function processCompoundStatementNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "_label", "Label");
    addNodeSubnodeOptional(node, nodeElem, "value", "Value", true, (e, v) => {
        for (const stmt of v) {
            if (!stmt) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(stmt, false).base)
        }
    });
}

function processConditionalStatementNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "_label", "Label");
    addNodeSubnodeOrError(node, nodeElem, "cond", "Condition", true);
    addNodeSubnodeOrError(node, nodeElem, "ifStmt", "True Branch", true);
    addNodeSubnodeOptional(node, nodeElem, "elseStmt", "False Branch", true);
}

function processCaseStatementNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "_label", "Label");
    addNodeSubnodeOrError(node, nodeElem, "index", "Index", true);
    addNodeSubnodeOrError(node, nodeElem, "cases", "Cases", true, (e, v) => {
        for (const stmt of v) {
            if (!stmt) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(stmt, false).base)
        }
    });
}

function processCaseNode(node, nodeElem) {
    addNodeSubnodeOrError(node, nodeElem, "heading", "Heading", true, (e, v) => {
        for (const stmt of v) {
            if (!stmt) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(stmt, false).base)
        }
    });
    addNodeSubnodeOrError(node, nodeElem, "body", "Body", true);
}

function processWhileStatementNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "_label", "Label");
    addNodeSubnodeOrError(node, nodeElem, "cond", "Condition", true);
    addNodeSubnodeOrError(node, nodeElem, "body", "Body", true);
}

function processRepeatStatementNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "_label", "Label");
    addNodeSubnodeOrError(node, nodeElem, "cond", "Condition", true);
    addNodeSubnodeOptional(node, nodeElem, "body", "Body", true, (e, v) => {
        for (const stmt of v) {
            if (!stmt) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(stmt, false).base)
        }
    });
}

const ForTraversalMode = {
    1: "FOR_TO",
    2: "FOR_DOWNTO",
};
function processForStatementNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "_label", "Label");
    addNodeSubnodeOrError(node, nodeElem, "controlVar", "Control Variable", true);
    addNodeSubnodeOrError(node, nodeElem, "initial", "Initial Value", true);
    addNodeFieldOrError(node, nodeElem, 
        "traversalMode", "Traversal Mode", 
        `${ForTraversalMode[node.traversalMode]} (${node.traversalMode})`
    );
    addNodeSubnodeOrError(node, nodeElem, "final", "Final Value", true);
    addNodeSubnodeOrError(node, nodeElem, "body", "Body", true);
}

function processWithStatementNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "_label", "Label");
    addNodeSubnodeOrError(node, nodeElem, "recVars", "Record Variables", true, (e, v) => {
        for (const stmt of v) {
            if (!stmt) createErrorFieldElem("Empty element.", e.body);
            else e.body.append(processNode(stmt, false).base)
        }
    });
    addNodeSubnodeOrError(node, nodeElem, "body", "Body", true);
}
//#endregion ------- Section 9.2 -------
//#endregion -------------- Section R9 --------------

function processBlockNode(node, nodeElem) {
    addNodeSubnodeOptional(node, nodeElem, "labels", "Labels");
    addNodeSubnodeOptional(node, nodeElem, "consts", "Constants");
    addNodeSubnodeOptional(node, nodeElem, "types", "Types");
    addNodeSubnodeOptional(node, nodeElem, "variables", "Variables");
    addNodeSubnodeOptional(node, nodeElem, "subfuncs", "Procedures & Functions");
    addNodeSubnodeOptional(node, nodeElem, "stmt", "Statements");
}

function processProgramHeadingNode(node, nodeElem) {
    addNodeFieldOrError(node, nodeElem, "name", "Program Name");
    addNodeFieldOrError(node, nodeElem, "externals", "Externals");
}

function processProgramNode(node, nodeElem) {
    const headingProp = createPropElem("heading", "Heading", undefined, nodeElem, false, true);
    if (!node.heading) {
        createErrorFieldElem("Program Heading is not defined.", headingProp.body);
    } else {
        headingProp.body.append(processNode(node.heading, true).base);
    }

    const bodyProp = createPropElem("body", "Body", undefined, nodeElem, false, true);
    bodyProp.body.append(processNode(node.body, true).base)
}
//#endregion ============== Node Processors ==============

function processNode(node, nested = false) {
    console.log("- Processing Node:", node.type, nested)

    // If the property 'value' is null on the object and additional properties are defined, it's a derived node that
    //   does not use the predefined property. Remove the property to remove clutter.
    if (node.value === null) {
        const keys = Object.keys(node);
        if (keys.length === NODE_BASE_KEYS.length && keys.every(k => NODE_BASE_KEYS.includes(k))) delete node.value;
    }

    const nodeElem = createASTNodeElem(nested);
    nodeElem.type.innerText = node.type;

    if (node.pos) {
        const posProp = createPropElem("pos", "Pos", undefined, nodeElem.body);
        const startPosProp = createPropElem("start", "Start", undefined, posProp.body);
        createFieldElem("1", "Row", node.pos.start[1], startPosProp.body);
        createFieldElem("2", "Column", node.pos.start[2], startPosProp.body);
        createFieldElem("0", "Index", node.pos.start[0], startPosProp.body);
        
        const endPosProp = createPropElem("end", "End", undefined, posProp.body);
        createFieldElem("1", "Row", node.pos.end[1], endPosProp.body);
        createFieldElem("2", "Column", node.pos.end[2], endPosProp.body);
        createFieldElem("0", "Index", node.pos.end[0], endPosProp.body);

    } else {
        const posProp = createPropElem("pos", "Pos", undefined, nodeElem.body);
        createErrorFieldElem("Node Position is not defined.", posProp.body);
    }

    switch (node.type) {
        case "StringNode": 
        case "IdentifierNode": {
            _processDefaultNode(node, nodeElem.body);
            break;
        }
        case "NumberNode": {
            processNumberNode(node, nodeElem.body);
            break;
        } 
        case "UnsignedConstantNode": {
            processUnsignedConstantNode(node, nodeElem.body);
            break;
        } 
        case "SpecialSymbolNode": {
            processSpecialSymbolNode(node, nodeElem.body);
            break;
        } 
        case "DirectiveNode": {
            _processDefaultNode(node, nodeElem.body);
            break;
        }
        case "LabelDeclarationNode": {
            processLabelDeclarationNode(node, nodeElem.body);
            break;
        }
        case "ConstantDefinitionNode": {
            processConstantDefinitionNode(node, nodeElem.body);
            break;
        }
        case "ConstantDefinitionPartNode": {
            processConstantDefinitionPartNode(node, nodeElem.body);
            break;
        }
        case "TypeIdentifierNode": {
            processTypeIdentifierNode(node, nodeElem.body);
            break;
        }
        //#region ------- Simple Types -------
        case "EnumeratedTypeNode": {
            processEnumeratedTypeNode(node, nodeElem.body);
            break;
        }
        case "SubrangeTypeNode": {
            processSubrangeTypeNode(node, nodeElem.body);
            break;
        }
        //#endregion ------- Simple Types -------
        //#region ------- Structured Types -------
        case "ArrayTypeNode": {
            processArrayTypeNode(node, nodeElem.body);
            break;
        }
        //#region ---- Record Type ----
        case "RecordSectionNode": {
            processRecordSectionNode(node, nodeElem.body);
            break;
        }
        case "RecordVariantCaseNode": {
            processRecordVariantCaseNode(node, nodeElem.body);
            break;
        }
        case "RecordVariantNode": {
            processRecordVariantNode(node, nodeElem.body);
            break;
        }
        case "RecordTypeNode": {
            processRecordTypeNode(node, nodeElem.body);
            break;
        }
        //#endregion ---- Record Type ----
        case "SetTypeNode": {
            processSetTypeNode(node, nodeElem.body);
            break;
        }
        //#endregion ------- Structured Types -------
        //#region ------- Pointer Types -------
        case "PointerTypeNode": {
            processPointerTypeNode(node, nodeElem.body);
            break;
        }
        //#endregion ------- Pointer Types -------
        case "TypeDefinitionNode": {
            processTypeDefinitionNode(node, nodeElem.body);
            break;
        }
        case "TypeDefinitionPartNode": {
            processTypeDefinitionPartNode(node, nodeElem.body);
            break;
        }
        case "VariableDeclarationNode": {
            processVariableDeclarationNode(node, nodeElem.body);
            break;
        }
        case "VariableDeclarationPartNode": {
            processVariableDeclarationPartNode(node, nodeElem.body);
            break;
        }
        //#region ------- Procedures and Functions -------
        case "IndexTypeSpecificationNode": {
            processIndexTypeSpecificationNode(node, nodeElem.body);
            break;
        }
        case "PackedConformantArraySchemaNode": {
            processPackedConformantArraySchemaNode(node, nodeElem.body);
            break;
        }
        case "UnpackedConformantArraySchemaNode": {
            processUnpackedConformantArraySchemaNode(node, nodeElem.body);
            break;
        }
        case "ParameterSpecificationNode": {
            processParameterSpecificationNode(node, nodeElem.body);
            break;
        }
        case "ActualParameterListNode": {
            processActualParameterListNode(node, nodeElem.body);
            break;
        }
        case "ProcedureHeadingNode": {
            processProcedureHeadingNode(node, nodeElem.body);
            break;
        }
        case "ProcedureDeclarationNode": {
            processProcedureDeclarationNode(node, nodeElem.body);
            break;
        }
        case "FunctionHeadingNode": {
            processFunctionHeadingNode(node, nodeElem.body);
            break;
        }
        case "FunctionDeclarationNode": {
            processFunctionDeclarationNode(node, nodeElem.body);
            break;
        }
        case "ProcedureAndFunctionDeclarationPartNode": {
            processProcedureAndFunctionDeclarationPartNode(node, nodeElem.body);
            break;
        }
        //#endregion ------- Procedures and Functions -------
        //#region ------- Section R7 -------
        case "EntireVariableNode": {
            processEntireVariableNode(node, nodeElem.body);
            break;
        }
        case "IndexedVariableNode": {
            processIndexedVariableNode(node, nodeElem.body);
            break;
        }
        case "FieldDesignatorNode": {
            processFieldDesignatorNode(node, nodeElem.body);
            break;
        }
        case "IdentifiedVariableNode": {
            processIdentifiedVariableNode(node, nodeElem.body);
            break;
        }
        //#endregion ------- Section R7 -------
        //#region ------- Section R8 -------
        case "OpNode": {
            processOpNode(node, nodeElem.body);
            break;
        }
        case "ExpressionLikeNode": {
            processExpressionLikeNode(node, nodeElem.body);
            break;
        }
        case "ExpressionNode": {
            processExpressionNode(node, nodeElem.body);
            break;
        }
        case "ElementDescriptionNode": {
            processElementDescriptionNode(node, nodeElem.body);
            break;
        }
        case "SetConstructorNode": {
            processSetConstructorNode(node, nodeElem.body);
            break;
        }
        case "FunctionDesignatorNode": {
            processFunctionDesignatorNode(node, nodeElem.body);
            break;
        }
        //#endregion ------- Section R8 -------
        //#region ------- Section R9 -------
        //#region ---- Section 9.1 ----
        case "AssignmentStatementNode": {
            processAssignmentStatementNode(node, nodeElem.body);
            break;
        }
        case "ProcedureStatementNode": {
            processProcedureStatementNode(node, nodeElem.body);
            break;
        }
        case "GotoStatementNode": {
            processGotoStatementNode(node, nodeElem.body);
            break;
        }
        //#endregion ---- Section 9.1 ----
        //#region ---- Section 9.2 ----
        case "CompoundStatementNode": {
            processCompoundStatementNode(node, nodeElem.body);
            break;
        }
        case "ConditionalStatementNode": {
            processConditionalStatementNode(node, nodeElem.body);
            break;
        }
        case "CaseStatementNode": {
            processCaseStatementNode(node, nodeElem.body);
            break;
        }
        case "CaseNode": {
            processCaseNode(node, nodeElem.body);
            break;
        }
        case "WhileStatementNode": {
            processWhileStatementNode(node, nodeElem.body);
            break;
        }
        case "RepeatStatementNode": {
            processRepeatStatementNode(node, nodeElem.body);
            break;
        }
        case "ForStatementNode": {
            processForStatementNode(node, nodeElem.body);
            break;
        }
        case "WithStatementNode": {
            processWithStatementNode(node, nodeElem.body);
            break;
        }
        //#endregion ---- Section 9.2 ----
        //#endregion ------- Section R9 -------
        case "BlockNode": {
            processBlockNode(node, nodeElem.body);
            break;
        }
        case "ProgramHeadingNode": {
            processProgramHeadingNode(node, nodeElem.body);
            break;
        }
        case "ProgramNode": {
            processProgramNode(node, nodeElem.body);
            break;
        }
        default: {
            createErrorFieldElem(`Unknown node type: ${node.type}`, nodeElem.body);
            // nodeElem.base.classList.remove("no-chevron");
        }
    }

    return nodeElem;
}

function processAST(input) {
    return processNode(input).base;
}

export {
    processAST
};