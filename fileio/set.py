from .flashcard import Flashcard

import pathlib
from datetime import datetime, UTC, timedelta

DATE_DUE = "datedue.txt"
ITER_FILE = "iter.txt" # refers to current iter (e.g. 1 means next iter should be 1, 2 means next iter should be 2)

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

        self._directory_path: pathlib.Path = directory_path
        self._name: str = directory_path.name

        # Ensure path exists
        if not directory_path.exists():
            raise FileNotFoundError(f"[set.py: __init__] Set directory cannot be found for {directory_path}")

        # Ensure it is a directory
        if not directory_path.is_dir():
            raise ValueError(f"[set.py: __init__] Set directory is not actually a directory for {directory_path}")

        # collect datedue.txt and iter.txt
        self._due_file: pathlib.Path = directory_path / DATE_DUE
        self._iter_file: pathlib.Path = directory_path / ITER_FILE

        # ensure duedate and iter exists
        if not self._due_file.exists():
            raise FileNotFoundError(f"[set.py: __init__] Date due file could not be located within {directory_path}")

        if not self._iter_file.exists():
            raise FileNotFoundError(f"[set.py: __init__] Iter due file could not be located within {directory_path}")

        try:
            _ = self.get_due_date()
            _ = int(self.get_iter())
        except ValueError as e:
            raise ValueError(f"[set.py: __init__] Invalid data within {self._due_file} or {self._iter_file}") from e

        # all children including iter/duedate
        children: list[pathlib.Path] = list(directory_path.iterdir())
        self._flashcards: list[Flashcard] = []

        for child in children:
            if child.is_dir(): # filter out iter/duedate
                try:
                    self._flashcards.append(Flashcard(child))
                except (FileNotFoundError, ValueError, UnicodeDecodeError, OSError) as e:
                    raise type(e)(f"[set.py: __init__] Error creating flashcard from {child}")

        # sort by number ascending
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
        # prevent error if the list is empty
        if self._flashcards:
            return self._flashcards[-1].number
        return 0

    @property
    def consolidated_statistics(self) -> tuple[str, list[int], int] | None:
        """
        Returns a tuple of arity 3.
        1 - overall success rate (str)
        2 - weakest flashcard (list int)
        3 - total revisions (int)
        None = no flashcards in set
        """

        cards = len(self._flashcards)
        if cards == 0:
            return None

        success_rate = 0
        revisions = 0
        weakest: list[int] = []
        threshold = 101

        for fc in self._flashcards:
            revisions += fc.revisions
            this_success = int(fc.success_rate[:-1])
            success_rate += this_success

            if this_success <= threshold:
                weakest.append(fc.number)
                threshold = this_success

        success_rate /= cards
        success_rate = int(success_rate)
        success_rate = f"{success_rate}%"

        revisions /= cards
        revisions = int(revisions)

        return (success_rate, weakest, revisions)


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
            self._flashcards.append(Flashcard.create_flashcard(self._directory_path, self.max_index+1, question, answer))
        except (FileNotFoundError, FileExistsError, OSError) as e:
            raise type(e)("[set.py: add_flashcards] Re-raising error.") from e

    def get_flashcard(self, number: int) -> Flashcard | None:
        """
        Get a flashcard by its cannonical number.

        Args:
          number (`int`): The flashcard's cannonical number.

        Returns:
          `Flashcard` or `None`: The flashcard, or none if it couldnt be found.
        """

        for fc in self._flashcards:
            if fc.number == number:
                return fc
        return None

    def attempt_set(self, success: bool, curve: dict[str, int]) -> None:
        """
        Record whether or not the user has successfully attempted the flashcard set.

        Args:
          success (`bool`): Whether the user successfully completed the set.
          curve (`dict[str, int]`): The curve.json contents as a formatted dictionary.

        Raises:
          OSError: Invalid permissions when accessing file.
          UnicodeDecodeError: Invalid bytes within file.
        """

        # if success, update with the next step in the iter curve.
        if success:
            iter = self.get_iter()
            date = self.get_due_date()

            next_days = curve.get(f"iter{iter+1}", curve.get("max", 1))

            try:
                self._iter_file.write_text(f"{iter+1}")
                self._due_file.write_text((date + timedelta(days=next_days)).isoformat())
            except (OSError, UnicodeDecodeError) as e:
                raise type(e)("[set.py: attempt_set] Issue writing to file") from e

            return

        # otherwise reset back to one
        try:
            self._iter_file.write_text("1")
            self._due_file.write_text((date + timedelta(days=curve.get("iter1", 1))).isoformat())
        except (OSError, UnicodeDecodeError) as e:
                        raise type(e)("[set.py: attempt_set] Issue writing to file") from e
                
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

        # error if set already exists
        if directory_path.exists():
            raise FileExistsError(f"[set.py: create_set] The directory already exists: {directory_path}")

        # otherwise try to create it
        try:
            directory_path.mkdir()

            # iter file creation, defaults to 1
            iter_file: pathlib.Path = directory_path / ITER_FILE
            iter_file.write_text("1")

            # due file, with `days_until_due` as default
            due_file: pathlib.Path = directory_path / DATE_DUE
            due_file.touch()

            now: datetime = datetime.now(UTC)
            due_at: str = (now + timedelta(days=days_until_due)).isoformat()
            due_file.write_text(due_at)
        except (OSError, UnicodeDecodeError, ValueError) as e:
            raise type(e)("[set.py: create_set] See original for more details.") from e

        return Set(directory_path)