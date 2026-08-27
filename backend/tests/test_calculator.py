"""
Tests for Calculator Tool (Safe AST evaluation) per spec §9.3 & §25.1
"""

import pytest
from app.tools.calculator import calculator


def test_calculator_basic_arithmetic():
    res = calculator.invoke({"expression": "2 + 3 * 4"})
    assert "14" in res


def test_calculator_power_and_functions():
    res = calculator.invoke({"expression": "sqrt(144) + 2 ** 3"})
    assert "20" in res


def test_calculator_division_by_zero():
    res = calculator.invoke({"expression": "10 / 0"})
    assert "Error" in res or "zero" in res.lower()


def test_calculator_blocks_arbitrary_code():
    res = calculator.invoke({"expression": "__import__('os').system('ls')"})
    assert "Error" in res
