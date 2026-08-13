from copy import deepcopy
from typing import TypeVar


T = TypeVar("T")


def snapshot(value: T) -> T:
    """返回与 Core 内部可变状态隔离的深拷贝。"""
    return deepcopy(value)
