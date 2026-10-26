import sys
from PySide6.QtWidgets import QApplication

from core.database import DatabaseManager
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    db = DatabaseManager()
    window = MainWindow(db)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
