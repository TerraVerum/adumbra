import copy
import inspect
import typing as t

from fastapi import params
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

Model_T = t.TypeVar("Model_T", bound=BaseModel)


def update_none_values(model_a: Model_T, model_b: Model_T, copy=True) -> Model_T:
    """
    Update all None values in `model_a` with values from `model_b`.
    """
    if copy:
        model_a = model_a.model_copy()
    for field, value in model_a:
        if value is None:
            setattr(model_a, field, getattr(model_b, field))
    return model_a


def wrapped_model_fields(
    model_class: type[Model_T], field_wrapper: FieldInfo
) -> type[Model_T]:
    """
    Until https://github.com/fastapi/fastapi/pull/4573 or its equivalent is merged,
    pydantic cannot forward field args (such as description, constraints, etc.)
    to FastAPI. This means if a BaseModel is a dependency injected into a FastAPI
    endpoint, the endpoint's OpenAPI schema will not reflect the BaseModel's field
    metadata. We get around this by creating a BaseModel at runtime with exactly
    the same fields as the original, but with metadata assigned the way FastAPI
    expects. This can be used exactly the same way as the original BaseModel, but
    is only anticipated to work in simple cases.
    """
    out_fields = {}
    for name, info in model_class.model_fields.items():
        if isinstance(info.default, FieldInfo) and info.default.__module__.startswith(
            "fastapi"
        ):
            # The field is already a FastAPI field, so we don't need to wrap it (and doing so would avoid utilizing the field's metadata)
            out_fields[name] = t.Annotated[info.annotation, info]
            continue
        fastapi_field = copy.copy(field_wrapper)
        for key in info.__slots__:
            val = getattr(info, key)
            if key.startswith("_") or (val is None and key != "default"):
                continue
            setattr(fastapi_field, key, val)
        # Credit: https://github.com/fastapi/fastapi/issues/4700#issuecomment-1154140434
        # Wrap fields as the Request type to get OpenAPI-recognized fields
        out_fields[name] = t.Annotated[info.annotation, Field(fastapi_field)]
    depends_model = create_model(model_class.__name__ + "Depends", **out_fields)

    return t.cast(type[Model_T], depends_model)


class ModelDepends(params.Depends):
    def __init__(
        self,
        field_wrapper: FieldInfo | t.Callable[[], FieldInfo],
        dependency: t.Callable | None = None,
        *,
        use_cache: bool = True,
    ):
        if inspect.isfunction(field_wrapper):
            field_wrapper = field_wrapper()
        self.field_wrapper = t.cast(FieldInfo, field_wrapper)
        self._dependency = dependency
        super().__init__(dependency, use_cache=use_cache)

    @property
    def dependency(self) -> t.Callable | None:
        return self._dependency

    @dependency.setter
    def dependency(self, dependency: t.Callable | None) -> None:
        if inspect.isclass(dependency) and issubclass(dependency, BaseModel):
            self._dependency = wrapped_model_fields(dependency, self.field_wrapper)
        else:
            self._dependency = dependency
