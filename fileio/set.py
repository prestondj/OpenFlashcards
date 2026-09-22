from .flashcard import Flashcard

import pathlib
from datetime import datetime, UTC, timedelta

DATE_DUE = "datedue.txt"
ITER_FILE = "iter.txt"

class Set():

    def __init__(self, directory_path: pathlib.Path) -> "Set":
        """
        Groups together flashcards into logical sets, and manages the time until they're next studied.

        Args:
          directory_path (`pathlib.Path`): The path of the set directory containing the flashcards.

        Raises:
          `FileNotFoundError`: Directory or required child could not be found.
          `ValueError`: Invalid configuration of directory or children.
          `OSError`: Issue accessing files.
          `UnicodeDecodeError`: Invalid bytes contained within files.
        """

        self._directory_path = directory_path
        self._name = directory_path.name

        # Ensure path exists
        if not directory_path.exists():
            raise FileNotFoundError(f"[set.py: __init__] Set directory cannot be found for {directory_path}")

        # Ensure it is a directory
        if not directory_path.is_dir():
            raise ValueError(f"[set.py: __init__] Set directory is not actually a directory for {directory_path}")

        # collect datedue.txt
        self._due_file: pathlib.Path = directory_path / DATE_DUE
        self._iter_file: pathlib.Path = directory_path / ITER_FILE

        if not self._due_file.exists():
            raise FileNotFoundError(f"[set.py: __init__] Date due file could not be located within {directory_path}")

        if not self._iter_file.exists():
            raise FileNotFoundError(f"[set.py: __init__] Iter due file could not be located within {directory_path}")

        try:
            _ = self.get_due_date()
            _ = int(self.get_iter())
        except ValueError as e:
            raise ValueError(f"[set.py: __init__] Invalid data within {self._due_file} or {self._iter_file}") from e

        children: list[pathlib.Path] = list(directory_path.iterdir())

        self._flashcards: list[Flashcard] = []

        for child in children:
            if child.is_dir():
                try:
                    self._flashcards.append(Flashcard(child))
                except (FileNotFoundError, ValueError, UnicodeDecodeError, OSError) as e:
                    raise type(e)(f"[set.py: __init__] Error creating flashcard from {child}")

        self._flashcards.sort(key=lambda f: f.number)

    # properties

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_due(self) -> bool:
        return self.get_due_date() < datetime.now(UTC)

    @property
    def max_index(self) -> int:
        if self._flashcards:
            return self._flashcards[-1].number
        return 0

    # kind of a property
    def get_flashcard(self, index: int) -> Flashcard:
        return self._flashcards[index]

    # instance methods

    def get_due_date(self) -> datetime:
        """
        Reads the due date from the file within the set directory.

        Returns:
          Due Date (`datetime`): The due date as a datetime object.

        Raises:
          OSError: Invalid permissions to access due date file.
          UnicodeDecodeError: Invalid bytes within due date file.
          ValueError: Invalid data within due date file.
        """

        raw_due_text: str
        try:
            raw_due_text = self._due_file.read_text()
        except (OSError, UnicodeDecodeError) as e:
            raise type(e)(f"[set.py: get_due_date] Re-raising error whilst reading from file {self._due_file}") from e
        
        try:
            return datetime.fromisoformat(raw_due_text)
        except ValueError as e:
            raise ValueError(f"[set.py: get_due_date] Issue parsing isoformat time from file {self._due_file}") from e

    def get_iter(self) -> int:
        """
        Reads the current iter from the file within the set directory
        """

        try:
            return int(self._iter_file.read_text())
        except (OSError, UnicodeDecodeError, ValueError) as e:
            raise type(e)("[set.py: get_iter] Invalid data within iter file.")
            ...

    def add_flashcard(self, question: str, answer: str) -> None:
        """
        Adds a new flashcard and automatically numbers it.

        Args:
          question (`str`): The question of the flashcard.
          answer (`str`): The answer of the flashcard.

        Raises:
          FileNotFoundError: Re-raised from `Flashcard.create_flashcard`.
          FileExistsError: Same as above.
          OSError: Same as above.
        """

        try:
            self._flashcards.append(Flashcard.create_flashcard(self._directory_path, self.max_index, question, answer))
        except (FileNotFoundError, FileExistsError, OSError) as e:
            raise type(e)("[set.py: add_flashcards] Re-raising error.") from e

    def get_flashcard(self, number: int) -> Flashcard | None:
        for fc in self._flashcards:
            if fc.number == number:
                return fc
        return None

    def attempt_set(self, success: bool) -> None:
        ...
                
    # static methods

    @staticmethod
    def create_set(directory_path: pathlib.Path, days_until_due: int = 1) -> "Set":
        """
        Creates a new flashcard set directory and its due date file. Does not create flashcards.

        Args:
          directory_path (`pathlib.Path`): The path for the set. 
          days_until_due (`int`): The days from current UTC until set is first due.

        Raises:
          FileExistsError: Set with name already exists.
          OSError: Invalid permission configuration.
          UnicodeDecodeError: Invalid bytes written to due file.
          ValueError: Invalid datetime operation.
        """

        if directory_path.exists():
            raise FileExistsError(f"[set.py: create_set] The directory already exists: {directory_path}")

        try:
            directory_path.mkdir()

            iter_file: pathlib.Path = directory_path / ITER_FILE
            iter_file.write_text("0")

            due_file: pathlib.Path = directory_path / DATE_DUE
            due_file.touch()

            now: datetime = datetime.now(UTC)
            due_at: str = (now + timedelta(days=days_until_due)).isoformat()
            due_file.write_text(due_at)
        except (OSError, UnicodeDecodeError, ValueError) as e:
            raise type(e)("[set.py: create_set] See original for more details.") from e

        return Set(directory_path)