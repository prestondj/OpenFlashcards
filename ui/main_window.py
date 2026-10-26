from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QPushButton,
    QLabel,
    QStackedWidget,
    QButtonGroup,
)

from config import APP_NAME, APP_VERSION
from core.database import DatabaseManager
from .styles import APP_STYLESHEET
from .views.course_view import CourseDashboardView
from .views.card_editor import CardEditorView
from .views.study_session import StudySessionView


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1140, 760)
        self.setStyleSheet(APP_STYLESHEET)

        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Navigation Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)
        nav_layout = QVBoxLayout(sidebar)
        nav_layout.setContentsMargins(16, 24, 16, 24)
        nav_layout.setSpacing(8)

        brand = QLabel(APP_NAME)
        brand.setStyleSheet("font-size: 19px; font-weight: 800; color: #38bdf8; background: transparent;")
        nav_layout.addWidget(brand)

        subtitle = QLabel("Spaced Repetition Engine")
        subtitle.setObjectName("SubTitle")
        nav_layout.addWidget(subtitle)
        nav_layout.addSpacing(20)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_dashboard = QPushButton("Courses and Curves")
        self.btn_study = QPushButton("Study Session")
        self.btn_editor = QPushButton("Card Editor")

        for btn in (self.btn_dashboard, self.btn_study, self.btn_editor):
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            self.nav_group.addButton(btn)
            nav_layout.addWidget(btn)

        self.btn_dashboard.setChecked(True)

        self.btn_dashboard.clicked.connect(self.show_dashboard)
        self.btn_study.clicked.connect(lambda: self.show_study(None))
        self.btn_editor.clicked.connect(lambda: self.show_editor(None))

        nav_layout.addStretch()

        footer = QLabel(f"v{APP_VERSION} • SQLite WAL")
        footer.setObjectName("SubTitle")
        nav_layout.addWidget(footer)

        main_layout.addWidget(sidebar)

        # Stacked View Router
        self.stack = QStackedWidget()
        self.dashboard_view = CourseDashboardView(self.db)
        self.study_view = StudySessionView(self.db)
        self.editor_view = CardEditorView(self.db)

        self.dashboard_view.study_requested.connect(self.show_study)
        self.dashboard_view.manage_cards_requested.connect(self.show_editor)
        self.study_view.session_completed.connect(self.dashboard_view.refresh)

        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.study_view)
        self.stack.addWidget(self.editor_view)

        main_layout.addWidget(self.stack, stretch=1)

    def show_dashboard(self) -> None:
        self.btn_dashboard.setChecked(True)
        self.dashboard_view.refresh()
        self.stack.setCurrentWidget(self.dashboard_view)

    def show_study(self, course_id: str | None = None) -> None:
        self.btn_study.setChecked(True)
        self.study_view.start_session(course_id=course_id)
        self.stack.setCurrentWidget(self.study_view)

    def show_editor(self, course_id: str | None = None) -> None:
        self.btn_editor.setChecked(True)
        if course_id:
            self.editor_view.select_course(course_id)
        else:
            self.editor_view.refresh()
        self.stack.setCurrentWidget(self.editor_view)
