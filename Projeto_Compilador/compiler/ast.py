from __future__ import annotations
from functools import reduce
from enum import Enum, auto
from typing import Union
import json
from .lexer import TokenPos

class NodePos:
    """
    Represents the location of this node on the source text.
    """
    def __init__(self, startPos, endPos, _rawStartPos = 0, _rawEndPos = 0):
        self._startPos = _rawStartPos
        self.startRow = startPos[0]
        self.startCol = startPos[1]

        self._endPos = _rawEndPos
        self.endRow = endPos[0]
        self.endCol = endPos[1]

    def getStart(self):
        return (self._startPos, self.startRow, self.startCol)

    def getEnd(self):
        return (self._endPos, self.endRow, self.endCol)

    def toJSON(self):
        return {
            "start": [self._startPos, self.startRow, self.startCol],
            "end": [self._endPos, self.endRow, self.endCol]
        }

    def setMonoPos(self, pos: (int, int, int)):
        self._startPos = pos[0]
        self.startRow = pos[1]
        self.startCol = pos[2]

        return self

    def setFullPos(self, start: (int, int, int), end: (int, int, int)):
        self._startPos = start[0]
        self.startRow = start[1]
        self.startCol = start[2]

        self._endPos = end[0]
        self.endRow = end[1]
        self.endCol = end[2]

        return self
    
    def setTokenPos(self, pos: TokenPos):
        self._startPos = pos._startPos
        self.startRow = pos.startRow
        self.startCol = pos.startCol

        self._endPos = pos._endPos
        self.endRow = pos.endRow
        self.endCol = pos.endCol
    
    def setStartTokenPos(self, pos: TokenPos):
        self._startPos = pos._startPos
        self.startRow = pos.startRow
        self.startCol = pos.startCol
    
    def setEndTokenPos(self, pos: TokenPos):
        self._endPos = pos._endPos
        self.endRow = pos.endRow
        self.endCol = pos.endCol

        return self
    
    def _startString(self):
        return f"{self.startRow}:{self.startCol}"
    startString = property(_startString)

    def _endString(self):
        return f"{self.endRow}:{self.endCol}"
    endString = property(_endString)

    def _fullString(self):
        return f"{self.startRow}:{self.startCol} - {self.endRow}:{self.endCol}"
    fullString = property(_fullString)

class Node:
    """
    Represents an abstract Node in an Abstract Syntax Tree. All nodes must derive from this base class.
    In order to assert for a specific node type in an AST-based rule, use Node#ist.

    By default, printing the value of a node will not reveal it's position nor the names of the parameters. 
    To show those properties, set the static attribute Node.verbose to True.
    """
    verbose = True

    def __init__(self, value = None, pos = ((0, 0), (0, 0))):
        self.value = value
        self.pos = NodePos(pos, pos)

    def _formatPos(self):
        if (self.verbose): return f"start={self.pos.startString}, end={self.pos.endString}"
        else: return ""

    def __repr__(self, level = 0):
        if (self.verbose): 
            return f"{type(self).__name__}(value={self.value}, {self._formatPos()})"
        else: 
            return f"{type(self).__name__}({self.value})"

    def toJSON(self):
        return {
            "type": type(self).__name__,
            "value": self.value, # Here I assume that nodes with non-overriden JSON parsers 
                                 #   will only use primitives as the value.
            "pos": self.pos.toJSON()
        }
    
    def toJSONString(self):
        return json.dumps(self.toJSON(), ensure_ascii=False)
    
    def ist(self, kind: "Node") -> bool:
        """
        Asserts if this node is an instance of a specific node type.
        """
        return isinstance(self, kind)

    def setMonoPos(self, pos: (int, int, int)):
        self.pos.setMonoPos(pos)
        return self

    def setFullPos(self, start: (int, int, int), end: (int, int, int)):
        self.pos.setFullPos(start, end)
        return self

    def setTokenPos(self, tokenPos):
        self.pos.setTokenPos(tokenPos)
        return self

    def setStartTokenPos(self, tokenPos):
        self.pos.setStartTokenPos(tokenPos)
        return self

    def setEndTokenPos(self, tokenPos):
        self.pos.setEndTokenPos(tokenPos)
        return self

#region ============== Compound Primitives =============
class SpecialSymbolKind(Enum):
    SS_NIL = auto()

class SpecialSymbolNode(Node):
    def __init__(self, value: SpecialSymbolKind):
        super().__init__(value)

    def __eq__(self, other):
        return isinstance(other, SpecialSymbolNode) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}value={self.value}" \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"

            return ret
        else: 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- {self.value}" \
                f"\n{' ' * (level * 2)})"
            
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": self.value.value
        }

class StringNode(Node):
    def __init__(self, value: str):
        super().__init__(None)
        self.value = value

    def __eq__(self, other):
        return isinstance(other, StringNode) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

class IdentifierNode(Node):
    def __init__(self, value: str):
        super().__init__(None)
        self.value = value

    def __eq__(self, other):
        return isinstance(other, IdentifierNode) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

class NumberKind(Enum):
    UNSIGNED_REAL = auto()
    UNSIGNED_INTEGER = auto()
    SIGNED_REAL = auto()
    SIGNED_INTEGER = auto()

class NumberNode(Node):
    def __init__(self, value: str, kind: NumberKind):
        super().__init__(None)
        self.kind = kind
        self.value = int(value) if self.isInt() else float(value)

    def __eq__(self, other):
        return isinstance(other, NumberNode) and self.value == other.value and self.kind == other.kind

    def __hash__(self):
        return hash(self.value) + hash(self.kind)

    def __repr__(self, level = 0):
        if (self.verbose): 
            return f"{type(self).__name__}(value={self.value}, " \
                f"kind={self.kind.name}({self.kind.value}), {self._formatPos()})"
        else: 
            return f"{type(self).__name__}({self.value}, {self.kind.name}({self.kind.value}))"

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "kind": self.kind.value,
        }

    # Turns an Unsigned Number into a signed number. Behavior is undefined when attempting to sign a signed number.
    # Op is the type of the LexToken object correspondent to an OP_PLUS or OP_MINUS instance.
    def sign(self, op: str):
        if (self.kind == NumberKind.UNSIGNED_INTEGER): self.kind = NumberKind.SIGNED_INTEGER
        elif (self.kind == NumberKind.UNSIGNED_REAL): self.kind = NumberKind.SIGNED_REAL

        if (op == "OP_MINUS"): self.value = -self.value

        return self

    def isSigned(self):
        return self.kind == NumberKind.SIGNED_REAL or self.kind == NumberKind.SIGNED_INTEGER

    def isInt(self):
        return self.kind == NumberKind.SIGNED_INTEGER or self.kind == NumberKind.UNSIGNED_INTEGER

    def signum(self):
        if (self.value > 0): return 1
        elif (self.value == 0): return 0
        else: return -1

class UnsignedConstantNode(Node):
    def __init__(self, value: NumberNode | StringNode | IdentifierNode | SpecialSymbolNode):
        super().__init__(value)
        self.setTokenPos(value.pos)

    def __eq__(self, other):
        return isinstance(other, Node) and other.ist(type(self.value)) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}value={self.value.__repr__(level + 1)}" \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"

            return ret
        else: 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- {self.value.__repr__(level + 1)}" \
                f"\n{' ' * (level * 2)})"
            
            return ret


    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": self.value.toJSON(),
        }

    def isSigned(self):
        return self.kind == NumberKind.SIGNED_REAL or self.kind == NumberKind.SIGNED_INTEGER

    def isInt(self):
        return self.kind == NumberKind.SIGNED_INTEGER or self.kind == NumberKind.UNSIGNED_INTEGER

    def signum(self):
        if (self.value > 0): return 1
        elif (self.value == 0): return 0
        else: return -1

class DirectiveNode(Node):
    def __init__(self, value: str):
        super().__init__(None)
        self.value = value

ConstantNode = NumberNode | IdentifierNode | StringNode
#endregion ============== Compound Primitives =============

# Section 3.A
class ProgramHeadingNode(Node):
    def __init__(self, name, externals):
        super().__init__(None)
        self.name = name
        self.externals = externals

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            return f"{type(self).__name__}(" \
                f"\n{noffset}name={self.name}," \
                f"\n{noffset}externals={repr(self.externals)}," \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
        else: 
            return f"{type(self).__name__}(" \
                f"\n{noffset}- {self.name}" \
                f"\n{noffset}- {self.externals}" \
                f"\n{' ' * (level * 2)})"

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "name": self.name,
            "externals": self.externals
        }

# Section 3.B
class LabelDeclarationNode(Node):
    def __init__(self, labels):
        super().__init__(None)
        self.value = labels

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": list(map(lambda c: c.toJSON(), self.value))
        }

#region ============== Section 3.C ==============
class ConstantDefinitionNode(Node):
    def __init__(self, key, value):
        super().__init__(None)
        self.key = key
        self.value = value

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            return f"{type(self).__name__}(" \
                f"\n{noffset}key={self.key}," \
                f"\n{noffset}value={self.value}," \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
        else: 
            return f"{type(self).__name__}(" \
                f"\n{noffset}{self.key}," \
                f"\n{noffset}{self.value}" \
                f"\n{' ' * (level * 2)})"

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "key": self.key,
            "value": self.value.toJSON()
        }

class ConstantDefinitionPartNode(Node):
    def __init__(self, constants: list[ConstantDefinitionNode]):
        super().__init__(None)
        self.value = constants

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            for c in self.value:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            for c in self.value:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": list(map(lambda c: c.toJSON(), self.value))
        }
#endregion ============== Section 3.C ==============

#region ============== Section 3.D ==============
class TypeKind(Enum):
    TYPE_UNKNOWN = auto()
    TYPE_SIMPLE = auto()
    TYPE_STRUCTURED = auto()
    TYPE_POINTER = auto()
    # Technically doesn't have independent nature in the spec, but it's categorization is Implementation-Defined, so I 
    # decided to promote it to it's own type kind.
    TYPE_IDENTIFIER = auto()

class TypeNode(Node):
    def __init__(self):
        super().__init__()
        self.kind = TypeKind.TYPE_UNKNOWN

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "kind": self.kind.value
        }

class TypeIdentifierNode(TypeNode):
    def __init__(self, value: IdentifierNode):
        super().__init__()
        self.kind = TypeKind.TYPE_IDENTIFIER
        self.value = value
        self.setTokenPos(value.pos)

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": self.value.toJSON()
        }


#region -------------- Simple Types --------------
class SimpleTypeNode(TypeNode):
    def __init__(self):
        super().__init__()
        self.kind = TypeKind.TYPE_SIMPLE

class OrdinalTypeNode(SimpleTypeNode):
    """
    Used exclusively for categorization purposes. Doesn't do jack shit on it's own and doesn't even have concrete
    representation on the AST.
    """
    def __init__(self):
        super().__init__()

class EnumeratedTypeNode(OrdinalTypeNode):
    def __init__(self, types: list[IdentifierNode]):
        super().__init__()
        self.value = types

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            for c in self.value:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                # ret += f"\n{noffset}- {c}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            for c in self.value:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                # ret += f"\n{noffset}- {c}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": list(map(lambda c: c.toJSON(), self.value))
        }
        # return base

class SubrangeTypeNode(OrdinalTypeNode):
    def __init__(self, start: Node, end: Node):
        super().__init__()
        self.start = start
        self.end = end

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- start={self.start}"
            ret += f"\n{noffset}- end={self.end}"
            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- {self.start}"
            ret += f"\n{noffset}- {self.end}"
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "start": self.start.toJSON(),
            "end": self.end.toJSON()
        }
        return base
#endregion -------------- Simple Types --------------

#region -------------- Structured Types --------------
class StructuredTypeNode(TypeNode):
    def __init__(self, packed: bool = False):
        super().__init__()
        self.kind = TypeKind.TYPE_STRUCTURED
        self.packed = packed

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "packed": self.packed
        }

class ArrayTypeNode(StructuredTypeNode):
    def __init__(self, values: list[SimpleTypeNode], basetype: SimpleTypeNode):
        super().__init__()
        self.value = values
        self.basetype = basetype

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- basetype={self.basetype.__repr__(level + 1)}"

            ret += f"\n{noffset}- value="
            for c in self.value:
                ret += f"\n{noffset}  - {c.__repr__(level + 2)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- {self.basetype.__repr__(level + 1)}"

            for c in self.value:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "basetype": self.basetype.toJSON(),
            "value": list(map(lambda c: c.toJSON(), self.value))
        }

class RecordSectionNode(Node):
    def __init__(self, identifiers: list[IdentifierNode], basetype: TypeNode):
        super().__init__()
        self.identifiers = identifiers
        self.basetype = basetype

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- basetype={self.basetype.__repr__(level + 1)}"

            ret += f"\n{noffset}- identifiers="
            for c in self.identifiers:
                ret += f"\n{noffset}  - {c.__repr__(level + 2)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- {self.basetype.__repr__(level + 1)}"

            for c in self.identifiers:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "basetype": self.basetype.toJSON(),
            "identifiers": list(map(lambda c: c.toJSON(), self.identifiers))
        }

class RecordVariantCaseNode(Node):
    def __init__(self, consts: list[Node], fixedPart: list[RecordSectionNode] = None, variantPart = None):
        super().__init__()
        self.consts = consts
        self.fixedPart = fixedPart
        self.variantPart = variantPart

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- consts="
            for c in self.consts:
                ret += f"\n{noffset}  - {c.__repr__(level + 2)}"

            if (self.fixedPart != None):
                ret += f"\n{noffset}- fixedPart="
                for c in self.fixedPart:
                    ret += f"\n{noffset}  - {c.__repr__(level + 2)}"
            else:
                ret += f"\n{noffset}- fixedPart=None"

            if (self.variantPart != None):
                ret += f"\n{noffset}- variantPart={self.variantPart.__repr__(level + 1)}"
            else:
                ret += f"\n{noffset}- variantPart=None"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            for c in self.consts:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"

            for c in self.fixedPart:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"

            if (self.variantPart != None):
                ret += f"\n{noffset}- {self.variantPart.__repr__(level + 1)}"
            else:
                ret += f"\n{noffset}- None"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "consts": list(map(lambda c: c.toJSON(), self.consts)),
            "fixedPart": list(map(lambda c: c.toJSON(), self.fixedPart)) if (self.fixedPart != None) else None,
            "variantPart": self.variantPart.toJSON() if (self.variantPart != None) else None
        }

class RecordVariantNode(Node):
    def __init__(self, identifier: str | None, basetype: TypeNode, cases: list[RecordVariantCaseNode]):
        super().__init__()
        self.identifier = identifier
        self.basetype = basetype
        self.cases = cases

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- basetype={self.basetype.__repr__(level + 1)}"

            if (self.identifier): ret += f"\n{noffset}- identifier={self.identifier}"
            else: ret += f"\n{noffset}- identifier=None"
            
            ret += f"\n{noffset}- cases="
            for c in self.cases:
                if (c == None): ret += f"\n{noffset}  - MALFORMED VALUE"
                else: ret += f"\n{noffset}  - {c.__repr__(level + 2)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- {self.basetype.__repr__(level + 1)}"

            if (self.identifier): ret += f"\n{noffset}- {self.identifier.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- None"

            for c in self.cases:
                ret += f"\n{noffset}  - {c.__repr__(level + 2)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "basetype": self.basetype.toJSON(),
            "identifier": self.identifier,
            "cases": list(map(lambda c: c.toJSON() if (c != None) else None, self.cases))
        }

class RecordTypeNode(StructuredTypeNode):
    def __init__(self, fixedPart: list[RecordSectionNode] = None, variantPart = None):
        super().__init__()
        self.fixedPart = fixedPart
        self.variantPart = variantPart

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            if (self.fixedPart != None):
                ret += f"\n{noffset}- fixedPart="
                for c in self.fixedPart:
                    ret += f"\n{noffset}  - {c.__repr__(level + 2)}"
            else:
                ret += f"\n{noffset}- fixedPart=None"

            if (self.variantPart != None):
                ret += f"\n{noffset}- variantPart={self.variantPart.__repr__(level + 1)}"
            else:
                ret += f"\n{noffset}- variantPart=None"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            for c in self.fixedPart:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"

            if (self.variantPart != None):
                ret += f"\n{noffset}- {self.variantPart.__repr__(level + 1)}"
            else:
                ret += f"\n{noffset}- None"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "fixedPart": list(map(lambda c: c.toJSON(), self.fixedPart)) if (self.fixedPart != None) else None,
            "variantPart": self.variantPart.toJSON() if (self.variantPart != None) else None
        }

class SetTypeNode(StructuredTypeNode):
    def __init__(self, basetype: OrdinalTypeNode):
        super().__init__()
        self.basetype = basetype

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- basetype={self.basetype.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- {self.basetype.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "basetype": self.basetype.toJSON()
        }

class FileTypeNode(StructuredTypeNode):
    def __init__(self, basetype: TypeNode):
        super().__init__()
        self.basetype = basetype

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- basetype={self.basetype.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- {self.basetype.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "basetype": self.basetype.toJSON()
        }
#endregion -------------- Structured Types --------------

#region -------------- Pointer Types --------------
class PointerTypeNode(TypeNode):
    def __init__(self, basetype: TypeNode):
        super().__init__()
        self.kind = TypeKind.TYPE_POINTER
        self.basetype = basetype

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- basetype={self.basetype.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- {self.basetype.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "basetype": self.basetype.toJSON()
        }
#endregion -------------- Pointer Types --------------

class TypeDefinitionNode(Node):
    def __init__(self, key, value):
        super().__init__(None)
        self.key = key
        self.value = value

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}key={self.key},"

            if self.value: ret += f"\n{noffset}value={self.value.__repr__(level + 1)},"
            else: ret += f"\n{noffset}- MALFORMED VALUE"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            
            return ret
        else: 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}{self.key},"

            # f"\n{noffset}{self.value.__repr__(level + 1)}" \
            if self.value: ret += f"\n{noffset}{self.value.__repr__(level + 1)},"
            else: ret += f"\n{noffset}- MALFORMED VALUE"

            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "key": self.key,
            "value": self.value.toJSON() if self.value else None
        }

class TypeDefinitionPartNode(Node):
    def __init__(self, types: list[TypeDefinitionNode]):
        super().__init__(None)
        self.value = types

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            if self.value:
                for c in self.value:
                    ret += f"\n{noffset}- {c.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- MALFORMED VALUE"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            for c in self.value:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": list(map(lambda c: c.toJSON(), self.value)) if self.value else None
        }
#endregion ============== Section 3.D ==============

#region ============== Section 3.E ==============

class VariableDeclarationNode(Node):
    def __init__(self, keys: list[IdentifierNode], value: TypeNode):
        super().__init__(None)
        self.keys = keys
        self.value = value

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}("

            ret += f"\n{noffset}keys=["
            for key in self.keys:
                f"\n{noffset}  - {key}"
            ret += f"\n{noffset}]"

            ret += f"\n{noffset}value={self.value.__repr__(level + 1)},"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            
            return ret
        else: 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}{self.key},"

            for key in self.keys:
                f"\n{noffset}  - {key}"
            ret += f"\n{noffset}{self.value.__repr__(level + 1)}" 

            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "keys": list(map(lambda c: c.toJSON(), self.keys)),
            "value": self.value.toJSON()
        }

class VariableDeclarationPartNode(Node):
    def __init__(self, variables: list[VariableDeclarationNode]):
        super().__init__(None)
        self.value = variables

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            if self.value:
                for c in self.value:
                    ret += f"\n{noffset}- {c.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- MALFORMED VALUE"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            for c in self.value:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": list(map(lambda c: c.toJSON(), self.value)) if self.value else None
        }

#region ============== Section 3.E ==============

#region ============== Section 11 ==============
#region -------------- Parameter Lists --------------
class IndexTypeSpecificationNode(Node):
    def __init__(self, lb, hb, name):
        super().__init__(None)
        self.lb = lb
        self.hb = hb
        self.name = name

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            return f"{type(self).__name__}(" \
                f"\n{noffset}name={self.name}," \
                f"\n{noffset}lb={self.lb}," \
                f"\n{noffset}hb={self.hb}," \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
        else: 
            return f"{type(self).__name__}(" \
                f"\n{noffset}- {self.name}" \
                f"\n{noffset}- {self.lb}" \
                f"\n{noffset}- {self.hb}" \
                f"\n{' ' * (level * 2)})"

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "name": self.name,
            "lb": self.lb,
            "hb": self.hb
        }

class PackedConformantArraySchemaNode(Node):
    def __init__(self, specification: IndexTypeSpecificationNode, name: TypeIdentifierNode):
        super().__init__(None)
        self.specification = specification
        self.name = name

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}("  \
                f"\n{noffset}name={self.name},"

            ret += f"\n{noffset}specification={c.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- {self.name}" \
                f"\n{noffset}- {c.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "name": self.name.toJSON(),
            "specification": self.specification.toJSON() if self.specification else None
        }

class UnpackedConformantArraySchemaNode(Node):
    def __init__(self, specifications: list[IndexTypeSpecificationNode], name: TypeIdentifierNode):
        super().__init__(None)
        self.specifications = specifications
        self.name = name

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}("  \
                f"\n{noffset}name={self.name},"

            ret += f"\n{noffset}specifications=["
            if self.specifications:
                for c in self.specifications:
                    ret += f"\n{noffset}- {c.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- MALFORMED VALUE"
            ret += f"\n{noffset}]"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- {self.name}"

            for c in self.value:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "name": self.name.toJSON(),
            "specifications": list(map(lambda c: c.toJSON(), self.specifications)) if self.specifications else None
        }

class ParameterSpecificationNode(Node):
    def __init__(
        self, 
        identifiers: list[IdentifierNode], 
        basetype: TypeIdentifierNode | PackedConformantArraySchemaNode | UnpackedConformantArraySchemaNode, 
        variable = False
    ):
        super().__init__(None)
        self.identifiers = identifiers
        self.basetype = basetype
        self.variable = variable

    def setVariable(self, variable: bool):
        self.variable = variable
        return self

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}("
            
            ret += f"\n{noffset}identifiers="
            for c in self.identifiers:
                ret += f"\n{noffset}  - {c}"
            
            ret += f"\n{noffset}basetype={self.basetype.__repr__(level + 1)}," \
                f"\n{noffset}variable={self.variable}" \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"

            return ret
        else: 
            ret = f"{type(self).__name__}("
                # f"\n{noffset}- {self.identifiers.__repr__(level + 1)}" \
            for c in self.identifiers:
                ret += f"\n{noffset}  - {c}"
            ret += f"\n{noffset}- {self.basetype.__repr__(level + 1)}" \
                f"\n{noffset}- {self.variable}" \
                f"\n{' ' * (level * 2)})"
            
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "identifiers": self.identifiers,
            "basetype": self.basetype.toJSON(),
            "variable": self.variable
        }

class ActualParameterListNode(Node):
    def __init__(self, params: list["ExpressionLikeNode"]):
        super().__init__(params)

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}("

            ret += f"\n{noffset}value="
            for c in self.value:
                ret += f"\n{noffset}  - {c.__repr__(level + 2)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"

            return ret
        else: 
            ret = f"{type(self).__name__}(" \

            for c in self.value:
                ret += f"\n{noffset}  - {c.__repr__(level + 2)}"

            ret += f"\n{' ' * (level * 2)})"

            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": list(map(lambda c: c.toJSON(), self.value)) if self.value else None
        }
#endregion -------------- Parameter Lists --------------

#region -------------- Procedure --------------
class ProcedureHeadingNode(Node):
    def __init__(self, name, params: list[ParameterSpecificationNode]):
        super().__init__(None)
        self.name = name
        self.params = params

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}name={self.name},"
            
            ret += f"\n{noffset}params="
            if (self.params):
                for c in self.params:
                    ret += f"\n{noffset}  - {c.__repr__(level + 2)}"
            else: ret += "N/A"
            
            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"

            return ret
        else: 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- {self.name}"
                # f"\n{noffset}- {self.params.__repr__(level + 1)}" \

            if (self.params):
                for c in self.params:
                    ret += f"\n{noffset}  - {c.__repr__(level + 2)}"

            ret += f"\n{' ' * (level * 2)})"

            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "name": self.name,
            "params": list(map(lambda c: c.toJSON(), self.params)) if self.params else None
        }

class ProcedureDeclarationNode(Node):
    def __init__(self, heading: ProcedureHeadingNode, body: "BlockNode" | DirectiveNode):
        super().__init__(None)
        self.heading = heading
        self.body = body

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            return f"{type(self).__name__}(" \
                f"\n{noffset}heading={self.heading.__repr__(level + 1)}," \
                f"\n{noffset}body={self.body.__repr__(level + 1)}," \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
        else: 
            return f"{type(self).__name__}(" \
                f"\n{noffset}- {self.heading.__repr__(level + 1)}" \
                f"\n{noffset}- {self.body.__repr__(level + 1)}" \
                f"\n{' ' * (level * 2)})"

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "heading": self.heading.toJSON(),
            "body": self.body.toJSON()
        }
#endregion -------------- Procedure --------------

#region -------------- Function --------------
class FunctionHeadingNode(Node):
    def __init__(self, name, params: list[ParameterSpecificationNode], rettype: TypeIdentifierNode):
        super().__init__(None)
        self.name = name
        self.params = params
        self.rettype = rettype

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}name={self.name},"
            
            ret += f"\n{noffset}params="
            if (self.params):
                for c in self.params:
                    ret += f"\n{noffset}  - {c.__repr__(level + 2)}"
            else: ret += "N/A"
            
            ret += f"\n{noffset}rettype={self.rettype}," \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"

            return ret
        else: 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- {self.name}"

            if (self.params):
                for c in self.params:
                    ret += f"\n{noffset}  - {c.__repr__(level + 2)}"

            ret += f"\n{noffset}{self.rettype}," \
                f"\n{' ' * (level * 2)})"

            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "name": self.name,
            "params": list(map(lambda c: c.toJSON(), self.params)) if self.params else None,
            "rettype": self.rettype.toJSON() if self.rettype else None
        }

class FunctionDeclarationNode(Node):
    def __init__(self, heading: FunctionHeadingNode, body: "BlockNode" | DirectiveNode):
        super().__init__(None)
        self.heading = heading
        self.body = body

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            return f"{type(self).__name__}(" \
                f"\n{noffset}heading={self.heading.__repr__(level + 1)}," \
                f"\n{noffset}body={self.body.__repr__(level + 1)}," \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
        else: 
            return f"{type(self).__name__}(" \
                f"\n{noffset}- {self.heading.__repr__(level + 1)}" \
                f"\n{noffset}- {self.body.__repr__(level + 1)}" \
                f"\n{' ' * (level * 2)})"

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "heading": self.heading.toJSON(),
            "body": self.body.toJSON()
        }
#endregion -------------- Function --------------

class ProcedureAndFunctionDeclarationPartNode(Node):
    def __init__(self, value: list[ProcedureDeclarationNode]):
        super().__init__(None)
        self.value = value

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            if self.value:
                for c in self.value:
                    ret += f"\n{noffset}- {c.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- MALFORMED VALUE"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            for c in self.value:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": list(map(lambda c: c.toJSON(), self.value)) if self.value else None
        }

#endregion ============== Section 11 ==============

#region ============== Section R7 ==============
class VariableKind(Enum):
    VARIABLE_UNKNOWN = auto()
    VARIABLE_ENTIRE = auto()
    VARIABLE_COMPONENT = auto()
    VARIABLE_IDENTIFIED = auto()
    # VARIABLE_BUFFER = auto()

class VariableStaticType(Enum):
    VARIABLE_ST_UNKNOWN = auto()
    VARIABLE_ST_ARRAY = auto()
    VARIABLE_ST_RECORD = auto()
    VARIABLE_ST_POINTER = auto()

class VariableNode(Node):
    def __init__(self):
        super().__init__()
        self.kind = VariableKind.VARIABLE_UNKNOWN
        self.staticType = None

    def setStaticType(self, staticType: VariableStaticType):
        self.staticType = staticType
        return self

    def setKind(self, kind: VariableKind):
        self.kind = kind
        return self

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "kind": self.kind.value,
            "staticType": self.staticType.value if self.staticType else None
        }

class EntireVariableNode(VariableNode):
    def __init__(self, value: str):
        super().__init__()
        self.kind = VariableKind.VARIABLE_ENTIRE
        self.value = value

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- value={self.value}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}("  \
                f"\n{noffset}- {self.value}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toIdentifierNode(self) -> IdentifierNode:
        return IdentifierNode(self.value).setTokenPos(self.pos)

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "kind": self.kind.value,
            "value": self.value
        }

class IndexedVariableNode(VariableNode):
    def __init__(self, value: VariableNode, lbindex: "ExpressionNode", hbindex: "ExpressionNode" | None):
        super().__init__()
        self.kind = VariableKind.VARIABLE_COMPONENT
        self.value = value.setStaticType(VariableStaticType.VARIABLE_ST_ARRAY)
        self.lbindex = lbindex
        self.hbindex = hbindex

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- kind={self.kind.value}" \
                f"\n{noffset}- value={self.value.__repr__(level + 1)}" \
                f"\n{noffset}- lbindex={self.lbindex.__repr__(level + 1)}"

            if self.hbindex:
                ret += f"\n{noffset}- hbindex={self.hbindex.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- hbindex=N/A"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}("  \
                f"\n{noffset}- {self.kind.value}" \
                f"\n{noffset}- {self.value.__repr__(level + 1)}" \
                f"\n{noffset}- {self.lbindex.__repr__(level + 1)}"

            if self.hbindex:
                ret += f"\n{noffset}- {self.hbindex.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- N/A"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "kind": self.kind.value,
            "value": self.value.toJSON(),
            "lbindex": self.lbindex.toJSON(),
            "hbindex": self.hbindex.toJSON() if self.hbindex else None
        }

class FieldDesignatorNode(VariableNode):
    def __init__(self, key: VariableNode | IdentifierNode, value: IdentifierNode):
        super().__init__()
        self.kind = VariableKind.VARIABLE_COMPONENT

        self.key = key
        if (key.ist(VariableNode)): key.setStaticType(VariableStaticType.VARIABLE_ST_RECORD)

        self.value = value

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- kind={self.kind.value}" \
                f"\n{noffset}- key={self.key.__repr__(level + 1)}"

            if self.value:
                ret += f"\n{noffset}- value={self.value.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- value=N/A"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}("  \
                f"\n{noffset}- {self.kind.value}" \
                f"\n{noffset}- {self.key.__repr__(level + 1)}"

            if self.value:
                ret += f"\n{noffset}- {self.value.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- N/A"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "kind": self.kind.value,
            "key": self.key.toJSON(),
            "value": self.value.toJSON() if self.value else None
        }

class IdentifiedVariableNode(VariableNode):
    def __init__(self, value: VariableNode):
        super().__init__()
        self.kind = VariableKind.VARIABLE_IDENTIFIED
        self.value = value.setStaticType(VariableStaticType.VARIABLE_ST_POINTER)

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- kind={self.kind.value}" \
                f"\n{noffset}- value={self.value.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}("  \
                f"\n{noffset}- {self.kind.value}" \
                f"\n{noffset}- {self.value.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "kind": self.kind.value,
            "value": self.value.toJSON()
        }
#endregion ============== Section R7 ==============

#region ============== Section R8 ==============
# As defined on Section R8.1, operand evaluation order is implementation-dependent. One can opt to evaluate 
#   left-to-right, in-to-out or any other combination. It's also a good point for optimization (e.g: 0 * anything)

class OpKind(Enum):
    # Arithmetic Operators
    OP_ADD = auto()
    OP_SUB = auto()
    OP_MUL = auto()
    OP_DIV = auto()
    OP_MOD = auto()

    # Logical Operators
    OP_OR = auto()
    OP_AND = auto()

    # Relational Operators
    OP_EQ = auto()
    OP_NEQ = auto()
    OP_LT = auto()
    OP_LTE = auto()
    OP_GT = auto()
    OP_GTE = auto()
    OP_IN = auto()

class OpNode(Node):
    def __init__(self, op: OpKind):
        super().__init__(op)

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}value={self.value}" \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"

            return ret
        else: 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- {self.value}" \
                f"\n{' ' * (level * 2)})"
            
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": self.value.value
        }

class ExpressionKind(Enum):
    EXP_UNARY = auto()
    EXP_BINARY = auto()

class ExpressionStaticType(Enum):
    EXP_ORDINAL = auto()
    EXP_BOOLEAN = auto()
    EXP_INTEGER = auto()

class ExpressionLikeNode(Node):
    def __init__(self, value: UnsignedConstantNode | VariableNode | IdentifierNode = None):
        super().__init__(value)
        self.kind = ExpressionKind.EXP_UNARY
        self.staticType = None

        if (value != None): self.setTokenPos(value.pos)
    
    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- kind={self.kind}"

            if self.value:
                ret += f"\n{noffset}- value={self.value.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- value=N/A"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}("  \
                f"\n{noffset}- {self.kind}"

            if self.value:
                ret += f"\n{noffset}- {self.value.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- N/A"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def setKind(self, kind: ExpressionKind):
        self.kind = kind
        return self

    def setStaticType(self, staticType: ExpressionStaticType):
        self.staticType = staticType
        return self

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "kind": self.kind.value,
            "value": self.value.toJSON() if self.value else None,
            "staticType": self.staticType.value if self.staticType else None
        }

class ExpressionNode(ExpressionLikeNode):
    def __init__(self, lhs: ExpressionLikeNode, op: OpNode, rhs: ExpressionLikeNode):
        super().__init__()
        self.kind = ExpressionKind.EXP_BINARY
        self.lhs = lhs
        self.op = op
        self.rhs = rhs
    
    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}("

            ret += f"\n{noffset}- kind={self.kind}"

            if (self.lhs): ret += f"\n{noffset}- lhs={self.lhs.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- lhs=N/A"

            ret += f"\n{noffset}- op={self.op.__repr__(level + 1)}"

            if (self.rhs): ret += f"\n{noffset}- rhs={self.rhs.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- rhs=N/A"
            
            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"

            return ret
        else: 
            ret = f"{type(self).__name__}("
            ret += f"\n{noffset}- {self.kind}"

            if (self.lhs): ret += f"\n{noffset}- {self.lhs.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- N/A"

            ret += f"\n{noffset}- {self.op.__repr__(level + 1)}"

            if (self.rhs): ret += f"\n{noffset}- {self.rhs.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- N/A"

            ret += f"\n{' ' * (level * 2)})"
            
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "lhs": self.lhs.toJSON() if self.lhs else None,
            "op": self.op.toJSON(),
            "rhs": self.rhs.toJSON() if self.rhs else None
        }

class ElementDescriptionNode(Node):
    def __init__(self, start: ExpressionLikeNode, end: ExpressionLikeNode | None):
        super().__init__()
        self.start = start
        self.end = end

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- start={self.start.__repr__(level + 1)}"

            if (self.end != None): ret += f"\n{noffset}- end={self.end.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- end=N/A"
            
            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- {self.start.__repr__(level + 1)}"

            if (self.end != None): ret += f"\n{noffset}- {self.end.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- N/A"

            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "start": self.start.toJSON(),
            "end": self.end.toJSON() if (self.end != None) else None
        }
        return base

class SetConstructorNode(Node):
    def __init__(self, value: list[ElementDescriptionNode]):
        super().__init__(None)
        self.value = value

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            if self.value:
                for c in self.value:
                    ret += f"\n{noffset}- {c.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- MALFORMED VALUE"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            for c in self.value:
                ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": list(map(lambda c: c.toJSON(), self.value)) if self.value else None
        }

class FunctionDesignatorNode(ExpressionLikeNode):
    def __init__(self, key: IdentifierNode, params: ActualParameterListNode | None):
        super().__init__()
        self.key = key
        self.params = params

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- key={self.key.__repr__(level + 1)}"

            if (self.params != None): ret += f"\n{noffset}- params={self.params.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- params=N/A"
            
            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 
            ret += f"\n{noffset}- {self.key.__repr__(level + 1)}"

            if (self.params != None): ret += f"\n{noffset}- {self.params.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- N/A"

            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "key": self.key.toJSON(),
            "params": self.params.toJSON() if (self.params != None) else None
        }
        return base
#endregion ============== Section R8 ==============

#region ============== Section R9 ==============
class StatementNode(Node):
    def __init__(self, value = None):
        super().__init__(value)
        self._label = None

    # Overridable method to get the labels defined within the statement. Compound statements override this method to
    # calculate the labels contained within.
    def getLabels(self) -> list[NumberNode]:
        if self._label:
            return [self._label]
        else:
            return []

    def setLabel(self, label: NumberNode):
        if (label != None):
            self._label = label
            self.setStartTokenPos(label.pos)

        return self

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "_label": self._label.toJSON() if (self._label) else None
        }

# As specified in Section 9.1.1, the value of the expression must be assignment-compatible, that is, it follows any of 
# the conditions defined in Section R6.5:
#   - The type of the key must equal to the resulting type of the expression value.
#   - The type of the key is Real and the resulting type of the expression value is Integer.
#   - The type of the key and the resulting type of the expression value are compatible ordinal types or compatible set
# types, and the type of the expression value belongs to the set of the key value, in the latter case.
#   - The type of the key and the resulting type of the expression value are compatible string types, that is, they both
# are character arrays with equal length.
class AssignmentStatementNode(StatementNode):
    def __init__(self, key: IdentifierNode | VariableNode, value: ExpressionNode):
        super().__init__(None)
        self.key = key
        self.value = value

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- key={self.key.__repr__(level + 1)}" \
                f"\n{noffset}- value={self.value.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- {self.key.__repr__(level + 1)}" \
                f"\n{noffset}- {self.value.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "key": self.key.toJSON(),
            "value": self.value.toJSON()
        }

# Essentially, this is a function call.
class ProcedureStatementNode(StatementNode):
    def __init__(self, key: IdentifierNode, params: ActualParameterListNode | None):
        super().__init__(None)
        self.key = key
        self.params = params

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- key={self.key.__repr__(level + 1)}"
            if (self.params != None): ret += f"\n{noffset}- params={self.params.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- {self.key.__repr__(level + 1)}"
            if (self.params != None): ret += f"\n{noffset}- {self.params.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "key": self.key.toJSON(),
            "value": self.params.toJSON() if (self.params) else None
        }

# As specified in Section 9.1.3, the label of a goto statement MUST follow at least one of the conditions:
#   - The label must exist in the Statement Sequence chain (see Section 9.2 and the Structured Statement section in 
# this module) that contains the current goto statement.
#   - The statement must not attempt to jump to a label that does not exist in the current scope or attempt to jump to 
# a label that was not declared on the current block (see Section 10.1).
class GotoStatementNode(StatementNode):
    def __init__(self, label: NumberNode):
        super().__init__(label)

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- value={self.value.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" \
                f"\n{noffset}- {self.value.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": self.value.toJSON()
        }

class CompoundStatementNode(StatementNode):
    def __init__(self, statements: list[StatementNode]):
        super().__init__(None)
        self.value = statements

    def getLabels(self):
        return list(reduce(lambda a, s : [*a, *s.getLabels()], self.value, []))

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            if self.value:
                for c in self.value:
                    if (c != None): ret += f"\n{noffset}- value={c.__repr__(level + 1)}"
                    else: ret += f"\n{noffset}- MALFORMED VALUE"
            else: ret += f"\n{noffset}- MALFORMED VALUE"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            for c in self.value:
                if (c != None): ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                else: ret += f"\n{noffset}- MALFORMED VALUE"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "value": list(map(lambda c: c.toJSON() if c else None, self.value)) if self.value else None
        }

class ConditionalStatementNode(StatementNode):
    def __init__(self, cond: ExpressionNode, ifStmt: StatementNode, elseStmt: StatementNode | None):
        super().__init__(None)
        self.cond = cond
        self.ifStmt = ifStmt
        self.elseStmt = elseStmt

    def getLabels(self):
        labels = [*self.ifStmt.getLabels()]
        if (self.elseStmt): labels = labels + self.elseStmt.getLabels()
        return labels

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- cond={self.cond.__repr__(level + 1)}"
            ret += f"\n{noffset}- ifStmt={self.ifStmt.__repr__(level + 1)}"

            if self.elseStmt:
                ret += f"\n{noffset}- elseStmt={self.elseStmt.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- elseStmt=N/A"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- {self.cond.__repr__(level + 1)}"
            ret += f"\n{noffset}- {self.ifStmt.__repr__(level + 1)}"

            if self.elseStmt:
                ret += f"\n{noffset}- {self.elseStmt.__repr__(level + 1)}"
            else: ret += f"\n{noffset}- N/A"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "cond": self.cond.toJSON(),
            "ifStmt": self.ifStmt.toJSON(),
            "elseStmt": self.elseStmt.toJSON() if (self.elseStmt) else None
        }

class CaseStatementNode(StatementNode):
    def __init__(self, index: ExpressionNode, cases: list[StatementNode]):
        super().__init__(None)
        self.index = index
        self.cases = cases

    def getLabels(self):
        return list(reduce(lambda a, s : [*a, *s.getLabels()], self.cases, []))

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- index={self.index.__repr__(level + 1)}"

            if self.cases:
                ret += f"\n{noffset}- cases="
                for c in self.cases:
                    if (c != None): ret += f"\n{noffset}  - {c.__repr__(level + 1)}"
                    else: ret += f"\n{noffset}- MALFORMED VALUE"
            else: ret += f"\n{noffset}- MALFORMED VALUE"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- {self.index.__repr__(level + 1)}"

            for c in self.value:
                if (c != None): ret += f"\n{noffset}- {c.__repr__(level + 1)}"
                else: ret += f"\n{noffset}- MALFORMED VALUE"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "index": self.index.toJSON(),
            "cases": list(map(lambda c: c.toJSON() if c else None, self.cases)) if self.cases else None
        }

class CaseNode(Node):
    def __init__(self, heading: list[Node], body: StatementNode):
        super().__init__(None)
        self.heading = heading
        self.body = body

    def getLabels(self):
        return self.body.getLabels()

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- heading="
            for h in self.heading:
                if (h != None): ret += f"\n{noffset}  - {h.__repr__(level + 1)}"
                else: ret += f"\n{noffset}- MALFORMED VALUE"

            ret += f"\n{noffset}- body={self.body.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            for h in self.value:
                if (h != None): ret += f"\n{noffset}- {h.__repr__(level + 1)}"
                else: ret += f"\n{noffset}- MALFORMED VALUE"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "heading": list(map(lambda c: c.toJSON() if c else None, self.heading)) if self.heading else None,
            "body": self.body.toJSON()
        }

class WhileStatementNode(StatementNode):
    def __init__(self, cond: ExpressionNode, body: StatementNode):
        super().__init__(None)
        self.cond = cond
        self.body = body

    def getLabels(self):
        return [*self.body.getLabels()]

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- cond={self.cond.__repr__(level + 1)}"
            ret += f"\n{noffset}- body={self.body.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- {self.cond.__repr__(level + 1)}"
            ret += f"\n{noffset}- {self.body.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "cond": self.cond.toJSON(),
            "body": self.body.toJSON()
        }

class RepeatStatementNode(StatementNode):
    def __init__(self, cond: ExpressionNode, body: list[StatementNode]):
        super().__init__(None)
        self.cond = cond
        self.body = body

    def getLabels(self):
        return list(reduce(lambda a, s : [*a, *s.getLabels()], self.body, []))

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- cond={self.cond.__repr__(level + 1)}"
            # ret += f"\n{noffset}- body={self.body.__repr__(level + 1)}"
            if self.body:
                ret += f"\n{noffset}- body="
                for c in self.body:
                    if (c != None): ret += f"\n{noffset}  - body={c.__repr__(level + 1)}"
                    else: ret += f"\n{noffset}  - MALFORMED VALUE"
            else: ret += f"\n{noffset}- MALFORMED VALUE"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- {self.cond.__repr__(level + 1)}"
            # ret += f"\n{noffset}- {self.body.__repr__(level + 1)}"
            if self.body:
                for c in self.body:
                    if (c != None): ret += f"\n{noffset}- body={c.__repr__(level + 1)}"
                    else: ret += f"\n{noffset}- MALFORMED VALUE"
            else: ret += f"\n{noffset}- MALFORMED VALUE"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "cond": self.cond.toJSON(),
            # "body": self.body.toJSON(),
            "body": list(map(lambda c: c.toJSON() if c else None, self.body)) if self.body else None
        }

class ForTraversalMode(Enum):
    FOR_TO = auto()
    FOR_DOWNTO = auto()

    @classmethod
    def fromKeyword(cls, kw):
        if (kw == "KW_TO"): return cls.FOR_TO
        elif (kw == "KW_DOWNTO"): return cls.FOR_DOWNTO
        else: return None

# According to section R9.2.3.3, the components of a for statement MUST abide by the following restrictions:
#   - The Control Variable must be local to the block the statement is in.
#   - The ordinal types of the Control Variable, Initial Value and Final Value MUST be compatible.
#   - All statements inside the body MUST NOT threaten the Control Variable. The Control Variable is threatened if:
#     - CV is the target of an Assignment Statement.
#     - CV is an actual variable parameter at any point in the direct statement chain of the body. TODO: Tf is this? R11.3.2.2
#     - CV is reused for another For Statement inside the body of the first.
#     - A Procedure of Function defined inside a block within the direct statement chain contains a statement that
# threatens CV.
#
# NOTE: Refer to section R9.2.3.3 for statement-equivalence examples for For Statements.
class ForStatementNode(StatementNode):
    def __init__(
        self, 
        controlVar: VariableNode, initial: ExpressionNode, 
        traversalMode: ForTraversalMode, final: ExpressionNode, body: StatementNode
    ):
        super().__init__(None)
        self.controlVar = controlVar
        self.initial = initial
        self.traversalMode = traversalMode
        self.final = final
        self.body = body

    def getLabels(self):
        return [*self.body.getLabels()]

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            ret += f"\n{noffset}- controlVar={self.controlVar.__repr__(level + 1)}"
            ret += f"\n{noffset}- initial={self.initial.__repr__(level + 1)}"
            ret += f"\n{noffset}- traversalMode={self.traversalMode}"
            ret += f"\n{noffset}- final={self.final.__repr__(level + 1)}"
            ret += f"\n{noffset}- body={self.body.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 
            
            ret += f"\n{noffset}- {self.controlVar.__repr__(level + 1)}"
            ret += f"\n{noffset}- {self.initial.__repr__(level + 1)}"
            ret += f"\n{noffset}- {self.traversalMode}"
            ret += f"\n{noffset}- {self.final.__repr__(level + 1)}"
            ret += f"\n{noffset}- {self.body.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "controlVar": self.controlVar.toJSON(),
            "initial": self.initial.toJSON(),
            "traversalMode": self.traversalMode.value,
            "final": self.final.toJSON(),
            "body": self.body.toJSON()
        }

class WithStatementNode(StatementNode):
    def __init__(self, recVars: list[VariableNode], body: StatementNode):
        super().__init__(None)
        self.recVars = recVars
        self.body = body

    def getLabels(self):
        return [*self.body.getLabels()]

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            ret = f"{type(self).__name__}(" 

            if self.recVars:
                ret += f"\n{noffset}- recVars="
                for c in self.recVars:
                    if (c != None): ret += f"\n{noffset}  - {c.__repr__(level + 1)}"
                    else: ret += f"\n{noffset}  - MALFORMED VALUE"
            else: ret += f"\n{noffset}- MALFORMED VALUE"
            ret += f"\n{noffset}- body={self.body.__repr__(level + 1)}"

            ret += f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
            return ret
        else: 
            ret = f"{type(self).__name__}(" 

            if self.recVars:
                for c in self.recVars:
                    if (c != None): ret += f"\n{noffset}- ={c.__repr__(level + 1)}"
                    else: ret += f"\n{noffset}- MALFORMED VALUE"
            else: ret += f"\n{noffset}- MALFORMED VALUE"
            ret += f"\n{noffset}- {self.body.__repr__(level + 1)}"
                
            ret += f"\n{' ' * (level * 2)})"
            return ret

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "recVars": list(map(lambda c: c.toJSON() if c else None, self.recVars)) if self.recVars else None,
            "body": self.body.toJSON()
        }
#endregion ============== Section R9 ==============

# Section 3
class BlockNode(Node):
    def __init__(
        self, 
        labels: LabelDeclarationNode, 
        consts: ConstantDefinitionPartNode,
        types: TypeDefinitionPartNode,
        variables: VariableDeclarationPartNode,
        subfuncs: ProcedureAndFunctionDeclarationPartNode,
        stmt: CompoundStatementNode
    ):
        super().__init__(None)
        self.labels = labels
        self.consts = consts
        self.types = types
        self.variables = variables
        self.subfuncs = subfuncs
        self.stmt = stmt

    def _getAttr(self, key, level):
        attr = getattr(self, key)
        return attr.__repr__(level + 1) if (attr != None) else "N/A"

    def __repr__(self, level = 1):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            return f"{type(self).__name__}(" \
                f"\n{noffset}labels={self._getAttr('labels', level)}," \
                f"\n{noffset}consts={self._getAttr('consts', level)}," \
                f"\n{noffset}types={self._getAttr('types', level)}," \
                f"\n{noffset}variables={self._getAttr('variables', level)}," \
                f"\n{noffset}subfuncs={self._getAttr('subfuncs', level)}," \
                f"\n{noffset}stmt={self._getAttr('stmt', level)}," \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
        else: 
            return f"{type(self).__name__}(" \
                f"\n{noffset}- {self._getAttr('labels', level)}" \
                f"\n{noffset}- {self._getAttr('consts', level)}" \
                f"\n{noffset}- {self._getAttr('types', level)}" \
                f"\n{noffset}- {self._getAttr('variables', level)}" \
                f"\n{noffset}- {self._getAttr('subfuncs', level)}" \
                f"\n{noffset}- {self._getAttr('stmt', level)}" \
                f"\n{' ' * (level * 2)})"

    def toJSON(self):
        base = super().toJSON()
        obj = {
            **base,
            "labels": self.labels.toJSON() if (self.labels != None) else None,
            "consts": self.consts.toJSON() if (self.consts != None) else None,
            "types": self.types.toJSON() if (self.types != None) else None,
            "variables": self.variables.toJSON() if (self.variables != None) else None,
            "subfuncs": self.subfuncs.toJSON() if (self.subfuncs != None) else None,
            "stmt": self.stmt.toJSON() if (self.stmt != None) else None
        }
        return obj

class ProgramNode(Node):
    def __init__(self, heading: ProgramHeadingNode, body: BlockNode):
        super().__init__(None)
        self.heading = heading
        self.body = body

    def __repr__(self, level = 0):
        noffset = ' ' * ((level + 1) * 2)

        if (self.verbose): 
            return f"{type(self).__name__}(" \
                f"\n{noffset}heading={self.heading.__repr__(level + 1)}," \
                f"\n{noffset}body={self.body.__repr__(level + 1)}," \
                f"\n{noffset}{self._formatPos()}" \
                f"\n{' ' * (level * 2)})"
        else: 
            return f"{type(self).__name__}(" \
                f"\n{noffset}- {self.heading.__repr__(level + 1)}" \
                f"\n{noffset}- {self.body.__repr__(level + 1)}" \
                f"\n{' ' * (level * 2)})"

    def toJSON(self):
        base = super().toJSON()
        return {
            **base,
            "heading": self.heading.toJSON(),
            "body": self.body.toJSON()
        }

        