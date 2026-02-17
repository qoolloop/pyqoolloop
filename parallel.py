"""Features for parallel programming."""

from contextlib import AbstractContextManager
from threading import (
    Lock,
    RLock,
)
from types import TracebackType
from typing import (
    TypeVar,
)

T = TypeVar('T')


class Guard(AbstractContextManager[T]):
    """
    Class to guard access to an instance using a lock.

    :param variable: Variable to guard. If the variable is of a primitive
        type, assigning it a value through this `Guard` does not modify the
        original variable.
    :param reentrant: If True, uses RLock instead of Lock, allowing the same
        thread to acquire the lock multiple times.

    .. warning::
        **Thread Safety Considerations (including Free-Threading mode):**

        - **Do not store references outside the `with` block**: The guard only
          protects access during the context manager's lifetime. Storing and using
          references outside the `with` block bypasses the lock protection.

        - **Access only through the Guard**: All access to the guarded variable
          should go through the `with` statement. Direct access to the variable
          from other references is not protected.

        - **Guards protect access patterns, not object internals**: If the guarded
          variable is a mutable object (list, dict, custom class), the Guard
          protects when you access it, but doesn't make the object's methods
          inherently thread-safe. Ensure operations within the `with` block are
          atomic or use thread-safe data structures.

    Example of correct usage::

        guarded_list = Guard([1, 2, 3])

        # Correct - all access within the guard
        with guarded_list as lst:
            lst.append(4)
            value = lst[0]

        # INCORRECT - reference stored and used outside guard
        with guarded_list as lst:
            ref = lst
        ref.append(5)  # NOT PROTECTED!
    """

    def __init__(self, variable: T, *, reentrant: bool = False) -> None:
        assert not isinstance(variable, type)

        self._variable = variable

        if reentrant:
            self._lock: RLock | Lock = RLock()

        else:
            self._lock = Lock()

    def __enter__(self) -> T:
        self._lock.acquire()
        return self._variable

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._lock.release()


class NoGuard(AbstractContextManager[T]):
    """
    Class that provides the same interface as Guard but without locking.

    Can be used as a drop-in replacement for Guard to disable locking. This is
    useful for debugging, performance testing, or when external synchronization
    is already provided.

    :param variable: Variable to guard (if this was `Guard`). If the variable is of a
        primitive type, assigning it a value through this `NoGuard` does not modify the
        original variable.
    :param reentrant: Ignored. Provided for interface compatibility with Guard.

    .. warning::
        **No Thread Safety**: This class provides NO synchronization or thread
        safety. Only use this in single-threaded contexts or when you have
        external synchronization mechanisms in place.
    """

    def __init__(self, variable: T, *, reentrant: bool = False) -> None:  # noqa: ARG002
        assert not isinstance(variable, type)

        self._variable = variable

    def __enter__(self) -> T:
        return self._variable

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass
