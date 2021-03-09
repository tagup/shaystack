from datetime import datetime
from typing import Optional, Dict, Any, List, Union

from shaystack import parse_filter, HaystackType, Quantity
from shaystack.filter_ast import FilterNode, FilterUnary, FilterPath, FilterBinary
from ..jsondumper import dump_scalar as json_dump_scalar

_simple_ops = {
    "==": "$eq",
    "!=": "$ne",
    "and": "$and",
    "or": "$or",
}
_relative_ops = {
    "<": "$lt",
    "<=": "$lte",
    ">": "$gt",
    ">=": "$gte",
}


def _to_float(scalar: HaystackType) -> float:
    if isinstance(scalar, Quantity):
        return scalar.magnitude
    if isinstance(scalar, (int, float)):
        return scalar
    raise ValueError("Impossible to compare with not a numnber")  # FIXME


def _conv_filter(node: Union[FilterNode, HaystackType]) -> Union[Dict[str, Any], str]:
    if isinstance(node, FilterUnary):
        if node.operator == "has":
            return {"$cond": {"if": _conv_filter(node.right), "then": 1, "else": 0}}
        if node.operator == "not":
            right_expr = _conv_filter(node.right)
            if isinstance(node, FilterNode):
                return {"$not": _conv_filter(node.right)}
            else:
                return {"$cond": {"if": _conv_filter(node.right), "then": 0, "else": 1}}
    if isinstance(node, FilterPath):
        return '$' + node.paths[0]
    if isinstance(node, FilterBinary):
        if node.operator in _simple_ops:
            return {_simple_ops[node.operator]: [
                _conv_filter(node.left),
                _conv_filter(node.right),
            ]}
        if node.operator in _relative_ops:
            path = _conv_filter(node.left)
            to_double = {
                "$let": {
                    "vars": {
                        f"{path[1:]}_": {
                            "$regexFind": {
                                "input": f"{path}",
                                "regex": "n:([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\\d+)?)"
                            }
                        }
                    },
                    "in": {"$toDouble": {
                        "$arrayElemAt": [f"${path}_.captures", 0]
                    }}
                }
            }

            return {_relative_ops[node.operator]: [
                to_double,
                _to_float(node.right),
            ]}
        assert 0, "Invalid operator"  # FIXME
    else:
        return json_dump_scalar(node)


def _mongo_filter(grid_filter: Optional[str],
                  version: datetime,
                  limit: int = 0,
                  customer_id: str = '') -> List[Dict[str, Any]]:
    return [
        {
            "$match":
                {
                    "$expr": _conv_filter(parse_filter(grid_filter).head)
                }
        }
    ]
    return
