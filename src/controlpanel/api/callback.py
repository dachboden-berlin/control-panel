from typing import Hashable, Callable, Union, TypeVar
from itertools import product
from .api import subscribe
from .commons import CallbackType


T = TypeVar('T', bound=Hashable)
F = TypeVar("F", bound=CallbackType)


def callback(*,
    source: str | list[str] | None = None,
    action: str | list[str] | None = None,
    value: Hashable | list[Hashable] | None = None,
    fire_once: bool = False,
    allow_parallelism: bool = False,
    ) -> Callable[[F], F]:

    def normalize(x: Union[str, T, list[T], None]) -> list[T] | list[None]:
        if x is None:
            return [None]
        if not isinstance(x, list):
            return [x]
        return x

    def decorator(func: F) -> F:
        sources = normalize(source)
        actions = normalize(action)
        values = normalize(value)

        for s, a, v in product(sources, actions, values):
            subscribe(func, s, a, v,
                      fire_once=fire_once,
                      allow_parallelism=allow_parallelism)
        return func

    return decorator
