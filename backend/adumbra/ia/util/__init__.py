import time
import typing as t

from pydantic import BaseModel

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


def profile(func):
    def wrap(*args, **kwargs):
        started_at = time.time()
        result = func(*args, **kwargs)
        diff = time.time() - started_at
        if isinstance(result, dict):
            result["time_ms"] = int(diff * 1000)
        return result

    return wrap
