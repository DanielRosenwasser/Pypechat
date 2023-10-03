from typing import NotRequired, TypedDict

# A program consists of a sequence of function calls that are evaluated in order.
Program = TypedDict("Program", {
    "@steps": list["FunctionCall"]
})

# A function call specifies a function name and a list of argument expressions. Arguments may contain
# nested function calls and result references.
FunctionCall = TypedDict("FunctionCall", {
    # Name of the function
    "@func": str,
    # Arguments for the function, if any.
    # Parameters following a * cannot be added to this.
    "@args": NotRequired[list["Expression"]],
    # Named arguments for the function, if appropriate.
    # Parameters preceding a / cannot be added to this.
    "@kwargs": NotRequired[dict[str, "Expression"]],
})

# A simple value is a str, a float, a bool, None, a dict, or a list. Function calls and result
# references can be nested in objects and arrays.
SimpleValue = str | int | float | bool | None | dict[str, "Expression"] | list["Expression"]

# A result reference represents the value of an expression from a preceding step.
ResultReference = TypedDict("ResultReference", {
    # Index of the previous expression in the "@steps" array
    "@ref": int,
})

# An expression is a simple value, a function call, or a reference to the result of a preceding expression.
Expression = SimpleValue | FunctionCall | ResultReference