import pathlib

# 3 required files within a flashcard directory
QUESTION: str = "question.txt"
ANSWER: str = "answer.txt"
STATISTICS: str = "statistics.txt"

# for easier iterating
REQUIRED_FILES: list[str] = [QUESTION, ANSWER, STATISTICS]

class Flashcard():

    def __init__(self, directory_path: pathlib.Path) -> "Flashcard":
        """
        Validate a flashcard directory, and provide a flashcard object.

        Args:
          directory_path (`pathlib.Path`): The path of the flashcard directory (structured as per `documentation.txt`)

        Raises:
          `FileNotFoundError`: One or more files, or the root could not be found.
          `ValueError`: A configuration within the found files is invalid.
          `UnicodeDecodeError`: A file within the directory contains invalid bytes.
          `OSError`: The OS cannot open one or more files within the directory.
        """
        # ensure path exists
        if not directory_path.exists():
            raise FileNotFoundError(f"[flashcard.py: __init__] Flashcard directory cannot be found: {directory_path}")

        # ensure it is a directory
        if not directory_path.is_dir():
            raise ValueError(f"[flashcard.py: __init__] Flashcard path does not point to a directory: {directory_path}")

        self._number: int = directory_path.name
        try:
            self._number = int(self._number)
        except TypeError as e:
            raise ValueError(f"[flashcard.py: __init__] Invalid name for a flashcard (non-numeric): {directory_path}")

        # ensure its children exist
        children: list[pathlib.Path] = list(directory_path.iterdir())
        if len(children) != 3:
            raise ValueError(f"[flashcard.py: __init__] Flashcard directory contains more than 3 files: {directory_path}")

        # make a dict for the path, key = constants, value = their full path
        self._paths: dict[str, pathlib.Path] = {}

        for file in REQUIRED_FILES:
            self._paths[file] = directory_path / file

        # ensure all paths exist
        for file in REQUIRED_FILES:
            if not self._paths[file] in children:
                raise FileNotFoundError(f"[flashcard.py: __init__] Flashcard directory {directory_path} is missing: {file}")
            if self._paths[file].is_dir():
                raise ValueError(f"[flashcard.py: __init__] Flashcard file {file} for {directory_path} is a directory.")


        # read statistics:
        raw_statistics: str = self._paths[STATISTICS].read_text()
        self._statistics: dict[str, int] | None = None
        try:
            self._statistics = Flashcard.read_statistics(raw_statistics)
        except ValueError as e:
            raise ValueError(f"[flashcard.py: __init__] Issue whilst setting up statistics for {directory_path}") from e

        # read question and answer:
        raw_question: str
        raw_answer: str
        try:
            raw_question = self._paths[QUESTION].read_text()
            raw_answer = self._paths[ANSWER].read_text()
        except (UnicodeDecodeError, OSError) as e:
            raise type(e)(f"[flashcard.py: __init__] Re-raising error from pathlib due to attempted reading of question/answer from: {directory_path}") from e

        if len(raw_question) == 0 or len(raw_answer) == 0:
            raise ValueError(f"[flashcard.py: __init] Answer '{raw_answer}' or Question '{raw_question}' are blank!")

        # set attributes if we've validated them
        self._question: str = raw_question.strip()
        self._answer: str = raw_answer.strip()

    # debugging utilities

    def __str__(self):
        return f"<flashcard {self.number}> q: {self.question} | a: {self.answer}"

    # properties

    @property
    def question(self) -> str:
        return self._question

    @property
    def answer(self) -> str:
        return self._answer

    @property
    def success_rate(self) -> str:
        # prevent div by 0
        if self._statistics["revisions"] == 0:
            return "100%"
        
        return f"{100 * (self._statistics["success"] / self._statistics["revisions"])}%"

    @property
    def revisions(self) -> int:
        return self._statistics["revisions"]

    @property
    def number(self) -> int:
        return self._number

    # instance methods

    def attempt(self, success: bool) -> None:
        """
        Increments the statistics based on the outcome of an attempt.

        Args:
          success (`bool`): Whether the flashcard was answered successfully.
        """

        # always increment revisions. update success only if bool is true.
        self._statistics["revisions"] += 1
        if success:
            self._statistics["success"] += 1

        # write the update
        payload: str = f"{self._statistics["revisions"]}\n{self._statistics["success"]}"
        self._paths[STATISTICS].write_text(payload)
    
    # static methods   

    @staticmethod
    def create_flashcard(set_directory: pathlib.Path, number: int, question: str, answer: str) -> "Flashcard":
        """
        Creates a flashcard in the given directory with the set question and answer.

        Args:
          set_directory (`pathlib.Path`): The path of the directory of which the flashcard directory will belong to.
          number (`int`): The flashcard's cannonical number.
          question (`str`): The question to live in `question.txt`.
          answer (`str`): The answer to live in `answer.txt`.

        Returns:
          Instance of Flashcard (`flashcard.Flashcard`): The instance tied to the created directory.

        Raises:
          `FileNotFoundError`: The set directory could not be resolved.
          `FileExistsError`: A flashcard with the cannonical number in the set already exists.
          `OSError`: An error creating the directory.
        """

        # ensure valid parent directory
        if not set_directory.exists() or not set_directory.is_dir():
            raise FileNotFoundError(f"[flashcard.py: create_flashcard] The set directory {set_directory} could not be found / is not a directory.")

        # ensure no duplicate set
        flashcard_directory: pathlib.Path = set_directory / str(number)
        if flashcard_directory.exists():
            raise FileExistsError(f"[flashcard.py: create_flashcard] Tried creating {flashcard_directory}, but it already exists!")

        # make flashcard directory
        try:
            flashcard_directory.mkdir()
        except OSError as e:
            raise OSError(f"[flashcard.py: create_flashcard] OS Error being re-raised, due to creation of {set_directory}") from e

        # populate flashcard directory
        paths: dict[str, pathlib.Path] = {}
        for file in REQUIRED_FILES:
            paths[file] = flashcard_directory / file
            paths[file].touch()

        # populate files with data
        paths[QUESTION].write_text(question)
        paths[ANSWER].write_text(answer)
        paths[STATISTICS].write_text("0\n0")

        # return a new instance - this does a lot of the validation!
        return Flashcard(flashcard_directory)

    @staticmethod
    def read_statistics(raw: str) -> dict[str, int]:
        """
        Decode statistics from the raw lines of the `statistics.txt` file.

        Args:
          raw (`str`): The raw lines of the file.

        Returns:
          statistics (`dict[str, int]`): A dictionary with two kvps of the success and revisions.

        Raises:
          `ValueError`: Data within the file is invalid.
        """
        # create new reference and split lines
        result: dict[str, int] = {}
        lines: list[str] = raw.split('\n')

        # invalid configuration if not 2 lines
        if len(lines) != 2:
            raise ValueError(f"[flashcard.py: read_statistics] Flashcard statistics file has invalid contents: {lines}")

        # ensure data within file is acceptable
        try:
            result["revisions"] = int(lines[0])
            result["success"] = int(lines[1])
        except TypeError as e:
            raise ValueError(f"[flashcard.py: read_statistics] Re-raising error due to invalid file contents: {lines}") from e

        return result