
from abc import ABC
from typing import Any, Literal, Protocol, overload

class Table(ABC):
    ...

class API(Protocol):
    """
    An API for working with data tables.
    """
    def read_csv(self, filename: str) -> Table:
        """Reads a CSV file from a path and returns a table"""
        ...
    def write_csv(self, filename: str, table: Table) -> None:
        """Writes a table to a CSV file"""
        ...
    def get_column_names(self, table: Table) -> list[str]:
        """Returns the column names of a table"""
        ...
    def get_column(self, table: Table, column_name: str) -> list[Any]:
        """Returns all of the values of a given column"""
        ...
    def set_column(self, table: Table, column_name: str, column: list[Any]) -> Table:
        """Adds or sets a column, returns the given table."""
        ...
    def remove_column(self, table: Table, column_name: str) -> Table:
        """Removes a column from the given table and returns the table"""
        ...
    def add_row(self, table: Table, row: list[Any]) -> Table:
        """Adds a row to the given table and returns the table"""
        ...
    def remove_rows_by_index(self, table: Table, row_index: int | list[int]) -> Table:
        """Removes a row at an index or a set of indices and returns the given table"""
        ...
    def drop_rows(self, table: Table, rows: list[bool]) -> Table:
        """Keeps only the rows that match the given list of booleans and returns the table"""
        ...
    def keep_rows(self, table: Table, rows: list[bool]) -> Table:
        """Keeps only the rows that match the given list of booleans and returns the table"""
        ...
    def equals(self, table: Table, column_name: str, value: Any) -> list[bool]:
        """Returns a list of booleans indicating whether the given column equals the given value"""
        ...
    def not_equals(self, table: Table, column_name: str, value: Any) -> list[bool]:
        """Returns a list of booleans indicating whether the given column does not equal the given value"""
        ...
    def group_by(self, table: Table, column_name: str) -> Table:
        ...
    def numeric_map(self, table: Table, column_name: str, op: Literal["+", "-", "*", "/", "**"], operand: int | float) -> list[int | float]:
        """Performs a numeric operation on every value in a column and returns a list of the results"""
        ...
    @overload
    def str_map(self, table: Table, column_name: str, op: Literal["trim", "trim_start", "trim_end"]) -> list[str]:
        """Performs a string-based operation on every value in a column and returns a list of the results"""
        ...
    @overload
    def str_map(self, table: Table, column_name: str, op: Literal["slice"], start: int, end: int) -> list[str]:
        """Performs a string-based operation on every value in a column and returns a list of the results"""
        ...
