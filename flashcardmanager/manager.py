from fileio.set import Set

import pathlib

from json import loads

CURVE = "curve.json"

class FlashcardManager():

    def __init__(self, root: pathlib.Path = pathlib.Path(__file__).parent.parent / "root") -> "FlashcardManager":
        """
        Traverses root directory and finds all flashcard sets.

        Args:
          root (`pathlib.Path`): The root directory containing the flashcard sets.

        Returns:
          FlashcardManager: An instance of a flashcard manager.

        Raises:
          FileNotFoundError
          ValueError
          OSError
          UnicodeDecodeError
        """

        self._directory_path: pathlib.Path = root

        # ensure dir exists
        if not root.exists():
            raise FileNotFoundError(f"[manager.py: __init__] Unable to find root directory of {root}")

        # ensure it is a dir
        if not root.is_dir():
            raise ValueError(f"[manager.py: __init__] The provided root is not a directory: {root}")

        # get flashcard sets
        self._sets: list[Set] = []
        for child in root.iterdir():
            if not child.is_dir():
                continue

            try:
                self._sets.append(Set(child))
            except (FileNotFoundError, ValueError, OSError, UnicodeDecodeError) as e:
                raise type(e)("[manager.py: __init__] Re-raising issue caused from invalid flashcard set layout") from e

        # get the curve
        self._curve_path = root / CURVE
        if not self._curve_path.exists():
            raise ValueError(f"[manager.py: __init__] The provided directory contains no curve.json")

        raw_json = self._curve_path.read_text()
        self._curve: dict[str, int] = loads(raw_json)[0]

    def create_set(self, name: str) -> None:
        try:
            self._sets.append(Set.create_set(self._directory_path / name, self._curve["iter1"]))
        except (FileExistsError, OSError, UnicodeDecodeError, ValueError) as e:
            raise type(e)("[manager.py: create_set] See raiser for more details.") from e

    def get_set(self, name: str) -> Set | None:
        for set in self._sets:
            if set.name == name:
                return set
        return None