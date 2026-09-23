import fileio
import flashcardmanager
import os
import sys

from typing import Literal
from readchar import readkey

# used with os.system to clear terminal.
CLEAR_TERM = 'clear' if sys.platform in ('linux', 'darwin') else 'cls'

def any_cont(clr: bool = True) -> None:
    print("Press any key to continue.")
    readkey()
    if clr:
        os.system(CLEAR_TERM)

# the 3 tiers of the project
manager: flashcardmanager.FlashcardManager = flashcardmanager.FlashcardManager()
current_set: fileio.Set | None = None
current_flashcard: fileio.Flashcard | None = None

# the current tier
current_fidelity: Literal["m", "s", "f"] = "m"

# corresponding options for each tier
MANAGER_MENU: list[str] = [
    "1 - Select a set",
    "2 - View all sets",
    "3 - View overdue sets",
    "4 - Create a new set",
    "0 - Quit"
]

SET_MENU: list[str] = [
    "1 - Attempt set",
    "2 - Add a card to this set",
    "3 - View statistics of this set",
    "4 - Preview the set,",
    "0 - Back to manager",
]

MENU_LOOKUP: dict[str, list] = {
    "m": MANAGER_MENU,
    "s": SET_MENU,
}

user_input: str = None
while user_input != "EXITFLAG":
    if current_fidelity == "s":
        print(f"Looking at the set {current_set.name}, which is due on {current_set.get_due_date().strftime("%A %d %B, %Y at %H:%M %Z")}.\n")

    print("\n".join(MENU_LOOKUP[current_fidelity]))
    user_input = readkey()

    # manager menu

    # quit on manager menu
    if user_input == "0" and current_fidelity == "m":
        os.system(CLEAR_TERM)
        break

    # attempt set on manager menu
    elif user_input == "1" and current_fidelity == "m":
        os.system(CLEAR_TERM)
        current_set = manager.get_set(input("Enter the set you wish to practice: "))

        if current_set:
            current_fidelity = "s"
            print(f"Selected set: {current_set.name}")
        else:
            print("Set could not be found.")
            readkey()

        os.system(CLEAR_TERM)
            
    # view all sets on manager menu
    elif user_input == "2" and current_fidelity == "m":
        os.system(CLEAR_TERM)

        print("Available Flashcard sets:")
        manager.list_sets()

        readkey()
        os.system(CLEAR_TERM)

    # view overdue sets on manager menu
    elif user_input == "3" and current_fidelity == "m":
        os.system(CLEAR_TERM)

        print(f"There are currently {manager.num_overdue} overdue sets.")
        if manager.num_overdue > 0:
            manager.list_overdue()

        readkey()
        os.system(CLEAR_TERM)

    # create a new set
    elif user_input == "4" and current_fidelity == "m":
        os.system(CLEAR_TERM)

        set_name = input("Enter name for new set: ").strip()
        if manager.get_set(set_name):
            print("Set with this name already exists.")
        else:
            manager.create_set(set_name)
            print(f"Successfuly created the set {set_name}")

        readkey()
        os.system(CLEAR_TERM)

    # set menu
    
    # back to manager
    elif user_input == "0" and current_fidelity == "s":
        os.system(CLEAR_TERM)
        current_fidelity = "m"

    # attempt set
    elif user_input == "1" and current_fidelity == "s":

        failure = False

        for fc_number in range(1, current_set.max_index+1):
            os.system(CLEAR_TERM)
            current_flashcard = current_set.get_flashcard(fc_number)

            print(f"Question {fc_number+1}: {current_flashcard.question}")
            usr_ans: str = input("Answer: ")

            os.system(CLEAR_TERM)
            print(f"You answered: {usr_ans}")
            print(f"Actual answer: {current_flashcard.answer}")

            print("Did you answer this correctly? Y/N")
            key = readkey()
            while key != "y" and key != "n":
                key = readkey()

            if key == "y":
                current_flashcard.attempt(True)
            else:
                current_flashcard.attempt(False)
                failure = True

        os.system(CLEAR_TERM)
        if failure:
            current_set.attempt_set(False, manager._curve)
            print(f"You have failed this set! It will now be due at: {current_set.get_due_date().strftime("%A %d %B, %Y, at %H:%M %Z")}.")

        else:
            current_set.attempt_set(True, manager._curve)
            print(f"You have completed this set! It will now be due at: {current_set.get_due_date().strftime("%A %d %B, %Y, at %H:%M %Z")}.")

        any_cont()

    # add a card to the set
    elif user_input == "2" and current_fidelity == "s":
        os.system(CLEAR_TERM)

        print(f"Adding a new card to the {current_set.name} set.")
        q = input("Enter the question: ").strip()
        a = input("Enter the corresponding answer: ").strip()

        if q and a:
            current_set.add_flashcard(q, a)
            print("Successfully added flashcard.")
        else:
            print("Invalid question or answer!")

        readkey()
        os.system(CLEAR_TERM)

    elif user_input == "3" and current_fidelity == "s":
        os.system(CLEAR_TERM)

        raw_stats = current_set.consolidated_statistics

        if not raw_stats:
            print("You need to attempt this set prior to viewing its statistics!")
        else:
            success_rate, weakest, threshold, revisions = raw_stats
            print(f"Your success rate across {revisions} revisions is {success_rate}.")

            if success_rate == "100%":
                print("You've never failed a card!")
            else:
                print(f"Your weakest cards, with a {int(threshold)}% success rate, are:")
                for card in weakest:
                    fc = current_set.get_flashcard(card)
                    print(f"{fc.number}: {fc.question}")

        readkey()
        os.system(CLEAR_TERM)

    elif user_input == "4":
        os.system(CLEAR_TERM)

        print("Set Preview:")
        for fc in current_set._flashcards:
            print(f"Flashcard {fc.number}: {fc.question}")

        readkey()
        os.system(CLEAR_TERM)