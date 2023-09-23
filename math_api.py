from typing import Protocol

class API(Protocol):
    def add(self, x: float, y: float) -> float:
        ...
    def sub(self, x: float, y: float) -> float:
        ...
    def mul(self, x: float, y: float) -> float:
        ...
    def div(self, x: float, y: float) -> float:
        ...
    def exp(self, base: float, pow: float) -> float:
        ...