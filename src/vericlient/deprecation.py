"""Support for the call style the clients used to require.

Every method used to take a single pydantic model. They now take the arguments themselves and
build the model internally, which removes an import from every call site and lets an editor
offer the parameters. The old style keeps working for one version so that upgrading is not a
rewrite, and is removed in 1.0.0.
"""

import functools
import warnings
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def legacy_model_argument(model: type[BaseModel]) -> Callable:
    """Accept the input model a method used to require, in place of its arguments.

    The model is expanded into keyword arguments, so validation and every error message are
    the ones the method would have produced anyway. Field values are passed through as they
    are rather than dumped, because some of them are models in their own right.

    Args:
        model: The input model this method used to take

    Returns:
        A decorator that accepts either call style

    """

    def decorator(method: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(method)
        def wrapper(self: object, *args: object, **kwargs: object) -> T:
            legacy = None
            if len(args) == 1 and isinstance(args[0], model):
                legacy, args = args[0], ()
            elif isinstance(kwargs.get("data_model"), model):
                legacy = kwargs.pop("data_model")

            if legacy is None:
                return method(self, *args, **kwargs)

            warnings.warn(
                f"Passing {model.__name__} to {method.__name__}() is deprecated and will be removed in "
                f"1.0.0. Pass the arguments directly: {method.__name__}("
                + ", ".join(f"{name}=..." for name in model.model_fields)
                + ").",
                DeprecationWarning,
                stacklevel=2,
            )
            return method(self, **dict(legacy), **kwargs)

        return wrapper

    return decorator
