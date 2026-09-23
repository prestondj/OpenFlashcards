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
    "0 - Back to manager",
]

MENU_LOOKUP: dict[str, list] = {
    "m": MANAGER_MENU,
    "s": SET_MENU,
}

user_input: str = None
while user_input != "EXITFLAG":
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

        any_cont()
            
    # view all sets on manager menu
    elif user_input == "2" and current_fidelity == "m":
        os.system(CLEAR_TERM)

        print("Available Flashcard sets:")
        manager.list_sets()

        any_cont()

    # view overdue sets on manager menu
    elif user_input == "3" and current_fidelity == "m":
        os.system(CLEAR_TERM)

        print(f"There are currently {manager.num_overdue} overdue sets.")
        if manager.num_overdue > 0:
            manager.list_overdue()

        any_cont()

    elif user_input == "4" and current_fidelity == "m":
        os.system(CLEAR_TERM)

        set_name = input("Enter name for new set: ").strip()
        if manager.get_set(set_name):
            print("Set with this name already exists.")
        else:
            manager.create_set(set_name)
            print(f"Successfuly created the set {set_name}")

        any_cont()

    # set menu
    
    elif user_input == "0" and current_fidelity == "s":
        os.system(CLEAR_TERM)
        current_fidelity = "m"