"""
ForgeX — Calculator Tool

Safe AST-based expression evaluator per spec §9.3.
Never uses eval(). Uses a restricted AST parser.
Built as a LangChain tool via @tool decorator.
"""

import ast
import math
import operator
from typing import Union

from langchain_core.tools import tool

from app.core.logging import get_logger

logger = get_logger("tools.calculator")

# Allowed binary operators
BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Allowed unary operators
UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Safe math functions and constants
SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval_node(node: ast.AST) -> Union[int, float]:
    """Recursively evaluate a safe AST node."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in BINARY_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        # Prevent excessively large exponents
        if op_type == ast.Pow and isinstance(right, (int, float)) and abs(right) > 1000:
            raise ValueError("Exponent too large (max 1000)")
        return BINARY_OPS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in UNARY_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return UNARY_OPS[op_type](_safe_eval_node(node.operand))
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCTIONS:
            func = SAFE_FUNCTIONS[node.func.id]
            if callable(func):
                args = [_safe_eval_node(arg) for arg in node.args]
                return func(*args)
            else:
                return func  # Constants like pi, e
        raise ValueError(f"Unsupported function: {getattr(node.func, 'id', 'unknown')}")
    elif isinstance(node, ast.Name):
        if node.id in SAFE_FUNCTIONS:
            val = SAFE_FUNCTIONS[node.id]
            if not callable(val):
                return val
        raise ValueError(f"Unsupported name: {node.id}")
    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


@tool
def calculator(expression: str) -> str:
    """Safely evaluate a mathematical expression. Supports arithmetic (+, -, *, /, **, %), 
    trigonometry (sin, cos, tan), logarithms (log, log10), square root (sqrt), 
    and constants (pi, e). Never executes arbitrary code.

    Args:
        expression: A mathematical expression to evaluate, e.g. "2 + 3 * 4", "sqrt(16)", "sin(pi/2)"
    """
    try:
        expression = expression.strip()
        if not expression:
            return "Error: Empty expression"

        if len(expression) > 500:
            return "Error: Expression too long (max 500 characters)"

        tree = ast.parse(expression, mode="eval")
        result = _safe_eval_node(tree)

        # Format result
        if isinstance(result, float) and result.is_integer():
            result = int(result)

        logger.info(f"Calculator: {expression} = {result}")
        return f"{expression} = {result}"

    except ZeroDivisionError:
        return f"Error: Division by zero in '{expression}'"
    except (ValueError, SyntaxError, TypeError) as e:
        logger.warning(f"Calculator error: {expression} -> {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected calculator error: {e}")
        return "Error: Calculation failed"
