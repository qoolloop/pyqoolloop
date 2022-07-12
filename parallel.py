"""Features for parallel programming."""

from contextlib import AbstractContextManager
from threading import (
    Lock,
    RLock,
)
from types import TracebackType
from typing import (
    Optional,
    Type,
    TypeVar,
    Union,
)


T = TypeVar('T')  # pylint: disable=invalid-name


class Guard(AbstractContextManager[T]):
    """Class to guard access to an instance."""

    def __init__(self, variable: T, *, reentrant: bool = False) -> None:
        """
        Initialize with variable to guard.

        :param variable: Variable to guard. If the variable is of a primitive
          type, assigning it a value through this `Guard` does not modify the
          original variable.
        """
        self._variable = variable

        if reentrant:
            self._lock: Union[RLock, Lock] = RLock()

        else:
            self._lock = Lock()

    def __enter__(self) -> T:
        self._lock.acquire()
        return self._variable

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self._lock.release()
