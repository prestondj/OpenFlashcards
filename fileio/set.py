from .flashcard import Flashcard

import pathlib
from datetime import datetime

DATE_DUE = "datedue.txt"

class Set():

    def __init__(self, directory_path: pathlib.Path) -> "Set":
        """
        Groups together flashcards into logical sets, and manages the time until they're next studied.

        Args:
          directory_path (`pathlib.Path`): The path of the set directory containing the flashcards.
        """

        # Ensure path exists
        if not directory_path.exists():
            raise FileNotFoundError(f"[set.py: __init__] Set directory cannot be found for {directory_path}")

        # Ensure it is a directory
        if not directory_path.is_dir():
            raise ValueError(f"[set.py: __init__] Set directory is not actually a directory for {directory_path}")

        # collect datedue.txt
        self._due_file: pathlib.Path = directory_path / DATE_DUE

        if not self._due_file.exists():
            raise FileNotFoundError(f"[set.py: __init__] Date due file could not be located within {directory_path}")

        raw_due_text: str
        try:
            raw_due_text = self._due_file.read_text()
        except (OSError, UnicodeDecodeError) as e:
            raise type(e)(f"[set.py: __init__] Re-raising error whilst reading from file {self._due_file}") from e

        self._due_datetime: str
        try:
            self._due_datetime = datetime.fromisoformat(raw_due_text)
        except ValueError as e:
            raise ValueError(f"[set.py: __init__] Invalid data within {self._due_file}") from e

        children: list[pathlib.Path] = list(directory_path.iterdir())
        children.remove(self._due_file)

        self._flashcards: list[Flashcard] = []

        for child in children:
            try:
                self._flashcards.append(Flashcard(child))
            except (FileNotFoundError, ValueError, UnicodeDecodeError, OSError) as e:
                raise type(e)(f"[set.py: __init__] Error creating flashcard from {child}")

        self._flashcards.sort(key=lambda f: f.number)
            
                
