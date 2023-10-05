from dataclasses import dataclass
import json
import tempfile
from textwrap import dedent
from typing import Generic, Protocol, TypeVar, cast
from typing_extensions import override

import mypy.api

import program.schema

T = TypeVar("T", covariant=True)

@dataclass
class Success(Generic[T]):
    value: T

@dataclass
class Failure:
    message: str

Result = Success[T] | Failure

class Model(Protocol):
    def complete(self, input: str) -> Result[str]:
        ...

# TODO: just use the object_hook and some custom __str__s on `json.loads`
def expr_to_text(expr: program.schema.Expression, for_program) -> str:
    match expr:
        case { "@ref": int(index) } if for_program:
            return f"STEP{index + 1}"
        case { "@ref": index } if for_program:
            # TODO: provide an error while generating the program in these cases
            return f"NON_INTEGRAL_REF"
        case { "@func": _ } if for_program:
            return call_to_text(cast(program.schema.FunctionCall, expr))
        case list():
            elements_str = ", ".join(expr_to_text(item, for_program) for item in expr)
            return f"[{elements_str}]"
        case dict():
            elements_strs: list[str] = []
            for key, value in expr.items():
                k_str = json.dumps(key) # no need to handle all expressions as keys
                v_str = expr_to_text(value, for_program)
                elements_strs.append(f"{k_str}: {v_str}")
            elements_str = ", ".join(elements_strs)
            return f"{{{elements_str}}}"
        case bool() | int() | float() | None:
            return str(expr)
        case str():
            return json.dumps(expr)
        case _:
            print(type(expr))
            print("UNEXPECTED")
            raise TypeError()

def call_to_text(call: program.schema.FunctionCall) -> str:
    func_name = call["@func"]
    arg_strs: list[str] = []

    if "@args" in call and call["@args"]:
        args = call["@args"]
        for arg in args:
            arg_strs.append(expr_to_text(arg, for_program=True))

    if "@kwargs" in call and call["@kwargs"]:
        kwargs = call["@kwargs"]
        for k, v in kwargs.items():
            arg_strs.append(f"{k}={expr_to_text(v, for_program=True)}")

    all_args_str = ", ".join(arg_strs)

    return f"api.{func_name}({all_args_str})"

def program_to_text(p: program.schema.Program):
    steps = p["@steps"]
    step_strs: list[str] = []
    for i, call in enumerate(steps, 1):
        step_strs.append(f"\n    STEP{i} = {call_to_text(call)}")

    step_strs.append(f"\n    return STEP{len(steps)}")
    all_steps_str = "".join(step_strs)

    return f"def fn(api: API):{all_steps_str}"

class _SingleFileChecker:
    f = tempfile.NamedTemporaryFile(mode="r+", encoding="utf8", delete=False)
    def __init__(self) -> None:
        mypy.api.run_dmypy(["run"])
        mypy.api.run_dmypy(["check", self.f.name])

    def __del__(self) -> None:
        mypy.api.run_dmypy(["stop", self.f.name])
        self.f.close()

    def check(self, file_contents: str) -> Result[None]:
        self.f.truncate(0)
        self.f.seek(0)
        self.f.write(file_contents)
        self.f.write("\n")
        self.f.flush()
        mypy_stdout, _mypy_stderr, exit_status = mypy.api.run_dmypy(["check", self.f.name])
        if exit_status != 0:
            return Failure(mypy_stdout)
        return Success(None)


@dataclass
class TypedDictValidator(Generic[T]):
    schema: str
    type_name: str
    _checker = _SingleFileChecker()

    def validate(self, json_text: str) -> Result[T]:
        program_text = None
        try:
            typed_dict = json.loads(json_text)
            expr_text = expr_to_text(typed_dict, for_program=False)
            program_text = f"{self.schema}\nTESTED_VAR: {self.type_name} = {expr_text}"
            check_result = self._checker.check(program_text)
        except Exception as err:
            err_text = f"{str(err)}\nJSON Text was:\n{json_text}\nand constructed program was:\n{program_text or 'NOT_SET'}"
            return Failure(err_text)
        if isinstance(check_result, Success):
            return Success(typed_dict)
        err_text = f"JSON Text was:\n{json_text}\nand constructed program was:\n{program_text or 'NOT_SET'}\n\nCheck result was {check_result.message}"
        return Failure(err_text)

@dataclass
class TypedDictTranslator(Generic[T]):
    model: Model
    validator: TypedDictValidator[T]

    _max_repair_attempts = 3

    def translate(self, request: str) -> Result[T]:
        request = self._create_request_prompt(request)
        num_repairs_attempted = 0
        while True:
            text_response = self.model.complete(request)
            if isinstance(text_response, Failure):
                return text_response

            text_response = text_response.value
            first_curly = text_response.find("{")
            last_curly = text_response.rfind("}") + 1
            error_message: str
            if 0 <= first_curly < last_curly:
                trimmed_response = text_response[first_curly:last_curly]
                result = self.validator.validate(trimmed_response)
                if isinstance(result, Success):
                    return result
                error_message = result.message
            else:
                error_message = "Response did not contain any test resembling JSON."
            # print(f"FAILURE FROM RESPONSE:\n```\n{text_response}\n```")
            if num_repairs_attempted >= self._max_repair_attempts:
                return Failure(error_message)
            num_repairs_attempted += 1
            request = f"{text_response}\n{self._create_repair_prompt(error_message)}"

    def _create_request_prompt(self, intent: str) -> str:
        prompt = \
            F"""
            You are a service that translates user requests into JSON objects of type "${self.validator.type_name}" according to the following Python definitions:
            ```
            {self.validator.schema}
            ```
            The following is a user request:
            '''
            {intent}
            '''
            The following is the user request translated into a JSON object with 2 spaces of indentation and no properties with the value undefined:
            """
        return dedent(prompt)

    def _create_repair_prompt(self, validation_error: str) -> str:
        prompt = \
            F"""
            The above JSON object is invalid for the following reason:
            '''
            {validation_error}
            '''
            The following is a revised JSON object:
            """
        return dedent(prompt)

@dataclass
class ProgramValidator:
    schema: str
    _checker = _SingleFileChecker()

    def validate(self, json_text: str) -> Result[program.schema.Program]:
        program_text = None
        try:
            typed_dict = json.loads(json_text)
            program_text = program_to_text(typed_dict)
            program_text = f"{self.schema}\n{program_text}"
            check_result = self._checker.check(program_text)
        except Exception as err:
            err_text = f"{str(err)}\nJSON Text was:\n{json_text}\nand constructed program was:\n{program_text or 'NOT_SET'}"
            return Failure(err_text)
        if isinstance(check_result, Success):
            return Success(typed_dict)
        err_text = f"JSON Text was:\n{json_text}\nand constructed program was:\n{program_text or 'NOT_SET'}\n\nCheck result was {check_result.message}"
        return Failure(err_text)

with open(program.schema.__file__, "r") as f:
    program_schema = f.read()

@dataclass
class ProgramTranslator(TypedDictTranslator[program.schema.Program]):
    model: Model
    validator: ProgramValidator

    @override
    def _create_request_prompt(self, intent: str) -> str:
        prompt = \
            F"""
            You are a service that translates user requests into programs represented as JSON using the following Python definitions:
            ```
            {program_schema}
            ```
            The programs can call functions from the API defined in the following Python:
            {self.validator.schema}
            The following is a user request:
            '''
            {intent}
            '''
            The following is the user request translated into a JSON object with 2 spaces of indentation and no properties with the value undefined:
            """
        return dedent(prompt)

    @override
    def _create_repair_prompt(self, validation_error: str) -> str:
        prompt = \
            F"""
            The above JSON program is invalid for the following reason:
            '''
            {validation_error}
            '''
            The following is a revised JSON program object:
            """
        return dedent(prompt)
