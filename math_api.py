from typing import Protocol

class API(Protocol):
    def add(self, x: float, y: float) -> float:
        """Add two numbers"""
        ...
    def sub(self, x: float, y: float) -> float:
        """Subtract two numbers"""
        ...
    def mul(self, x: float, y: float) -> float:
        """Multiple two numbers"""
        ...
    def div(self, x: float, y: float) -> float:
        """Divide two numbers"""
        ...
    def pow(self, base: float, exp: float) -> float:
        """Raise a base to a power."""
        ...
    def neg(self, x: float) -> float:
        """Negate a number"""
        ...
    def id(self, x: float) -> float:
        """Identity function"""
        ...
    def unknown(self, message: str) -> float:
        """Unknown request"""
        ...
