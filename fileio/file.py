from abc import ABC, abstractmethod
from typing import Optional

class File(ABC):
    """
    Abstract base class for a file in the file system.
    """

    def __init__(self, name: str, parent: Optional["File"] = None) -> "File":
        self.name = name
        self.parent = parent

    @property
    def path(self) -> str:
        if self.parent:
            return f"{self.parent.path}/{self.name}"
        return self.name

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def write(self, data):
        pass