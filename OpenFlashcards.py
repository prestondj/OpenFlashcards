import fileio
import flashcardmanager

manager: flashcardmanager.FlashcardManager = flashcardmanager.FlashcardManager()
current_set: fileio.Set | None = None
current_flashcard: fileio.Flashcard | None = None