import inspect
import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import UnionType
from typing import Any, Optional, get_args, get_origin

from gql_client import Client

from ..config import Settings


@dataclass(frozen=True)
class OperationParam:
    name: str
    required: bool
    type_name: str
    input_type: str
    placeholder: str


@dataclass(frozen=True)
class Operation:
    name: str
    kind: str
    kind_label: str
    theme: str
    params: list[OperationParam]


def _normalize_annotation(annotation: Any) -> tuple[type | None, str]:
    if annotation is inspect._empty:
        return None, "any"

    origin = get_origin(annotation)
    if origin is None:
        if hasattr(annotation, "__name__"):
            return annotation, annotation.__name__
        return None, str(annotation)

    if origin in (Optional, UnionType) or str(origin).endswith("Union"):
        args = [arg for arg in get_args(annotation) if arg is not type(None)]  # noqa: E721
        if len(args) == 1:
            base_type, base_name = _normalize_annotation(args[0])
            return base_type, f"{base_name} | None"

    return None, str(annotation)


def _build_param(name: str, annotation: Any, required: bool) -> OperationParam:
    base_type, type_name = _normalize_annotation(annotation)
    lower_name = name.lower()

    if base_type is bool:
        input_type = "checkbox"
        placeholder = ""
    elif base_type in (int, float):
        input_type = "number"
        placeholder = type_name
    elif any(token in lower_name for token in ("tx", "raw", "payload", "data")):
        input_type = "textarea"
        placeholder = "json or string"
    else:
        input_type = "text"
        placeholder = type_name

    return OperationParam(
        name=name,
        required=required,
        type_name=type_name,
        input_type=input_type,
        placeholder=placeholder,
    )


def _kind_from_name(name: str) -> tuple[str, str, str]:
    if name.startswith("query_"):
        return "query", "Query", "blue"
    if name.startswith("mutation_"):
        return "mutation", "Mutation", "rose"
    return "operation", "Operation", "indigo"


class OperationsCatalog:
    def __init__(self) -> None:
        self._operations = self._discover_operations()

    def list_operations(self) -> list[Operation]:
        return list(self._operations.values())

    def get(self, name: str) -> Operation:
        if name not in self._operations:
            raise KeyError(f"Unknown operation: {name}")
        return self._operations[name]

    def _discover_operations(self) -> dict[str, Operation]:
        operations: dict[str, Operation] = {}
        for name, func in Client.__dict__.items():
            if name.startswith("_"):
                continue
            if not inspect.iscoroutinefunction(func):
                continue
            sig = inspect.signature(func)
            params: list[OperationParam] = []
            for param in sig.parameters.values():
                if param.name == "self":
                    continue
                if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                    continue
                required = param.default is inspect._empty
                params.append(_build_param(param.name, param.annotation, required))
            kind, kind_label, theme = _kind_from_name(name)
            operations[name] = Operation(
                name=name,
                kind=kind,
                kind_label=kind_label,
                theme=theme,
                params=params,
            )
        return dict(sorted(operations.items()))


class OperationRunner:
    def __init__(self, settings: Settings, catalog: OperationsCatalog) -> None:
        self._settings = settings
        self._catalog = catalog

    @property
    def settings(self) -> Settings:
        return self._settings

    async def run(self, name: str, form_data: Mapping[str, Any]) -> Any:
        operation = self._catalog.get(name)
        kwargs = self._build_kwargs(operation, form_data)
        async with Client(url=self._settings.graphql_url) as client:
            method = getattr(client, name)
            result = await method(**kwargs)
        return self._serialize(result)

    def _build_kwargs(
        self, operation: Operation, form_data: Mapping[str, Any]
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        for param in operation.params:
            if param.input_type == "checkbox":
                value = form_data.get(param.name)
                if value is None:
                    if param.required:
                        raise ValueError(f"{param.name} is required")
                    continue
                kwargs[param.name] = str(value).lower() in ("true", "1", "on", "yes")
                continue

            raw = form_data.get(param.name)
            if raw is None or str(raw).strip() == "":
                if param.required:
                    raise ValueError(f"{param.name} is required")
                continue

            text = str(raw).strip()
            kwargs[param.name] = self._coerce_value(text, param.type_name)
        return kwargs

    def _coerce_value(self, value: str, type_name: str) -> Any:
        if value.startswith("{") or value.startswith("["):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        if type_name.startswith("int"):
            try:
                return int(value)
            except ValueError:
                return value
        if type_name.startswith("float"):
            try:
                return float(value)
            except ValueError:
                return value
        return value

    def _serialize(self, result: Any) -> Any:
        if hasattr(result, "model_dump"):
            return result.model_dump()
        if hasattr(result, "dict"):
            return result.dict()
        return result
