import time
from datetime import datetime, timezone
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QProgressBar,
    QComboBox,
)

from core.database import DatabaseManager
from core.models import Card
from core.scheduler import SpacedRepetitionEngine


class StudySessionView(QWidget):
    session_completed = Signal()

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.queue: list[Card] = []
        self.current_index: int = 0
        self.is_revealed: bool = False
        self.card_start_time: float = 0.0
        self.active_course_id: str | None = None

        self._build_ui()
        self._bind_shortcuts()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        top_bar = QHBoxLayout()
        header = QLabel("Spaced Repetition Study Session")
        header.setObjectName("HeaderTitle")
        top_bar.addWidget(header)
        top_bar.addStretch()

        top_bar.addWidget(QLabel("Deck:"))
        self.course_selector = QComboBox()
        self.course_selector.setMinimumWidth(230)
        self.course_selector.currentIndexChanged.connect(self._on_course_selector_changed)
        top_bar.addWidget(self.course_selector)
        layout.addLayout(top_bar)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        meta_row = QHBoxLayout()
        self.course_badge = QLabel("")
        self.course_badge.setObjectName("SubTitle")
        meta_row.addWidget(self.course_badge)
        meta_row.addStretch()

        self.overdue_badge = QLabel("")
        meta_row.addWidget(self.overdue_badge)
        layout.addLayout(meta_row)

        # Flashcard Display Surface
        self.card_surface = QFrame()
        self.card_surface.setObjectName("CardSurface")
        card_layout = QVBoxLayout(self.card_surface)
        card_layout.setContentsMargins(32, 28, 32, 28)

        self.side_indicator = QLabel("FRONT (PROMPT)")
        self.side_indicator.setObjectName("SubTitle")
        self.side_indicator.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.side_indicator)

        self.front_label = QLabel("")
        self.front_label.setObjectName("FlashcardText")
        self.front_label.setAlignment(Qt.AlignCenter)
        self.front_label.setWordWrap(True)
        card_layout.addWidget(self.front_label, stretch=1)

        self.divider = QFrame()
        self.divider.setObjectName("Divider")
        self.divider.setFrameShape(QFrame.HLine)
        card_layout.addWidget(self.divider)

        self.back_label = QLabel("")
        self.back_label.setObjectName("FlashcardText")
        self.back_label.setAlignment(Qt.AlignCenter)
        self.back_label.setWordWrap(True)
        card_layout.addWidget(self.back_label, stretch=1)

        layout.addWidget(self.card_surface, stretch=1)

        # Controls Bar
        self.reveal_btn = QPushButton("Reveal Answer  [Space]")
        self.reveal_btn.setObjectName("PrimaryButton")
        self.reveal_btn.setMinimumHeight(46)
        self.reveal_btn.clicked.connect(self.reveal_answer)
        layout.addWidget(self.reveal_btn)

        self.grade_widget = QWidget()
        grade_row = QHBoxLayout(self.grade_widget)
        grade_row.setContentsMargins(0, 0, 0, 0)
        grade_row.setSpacing(12)

        self.btn_again = QPushButton("[1] Again (Reset)")
        self.btn_again.setObjectName("GradeAgain")
        self.btn_again.setMinimumHeight(46)
        self.btn_again.clicked.connect(lambda: self.submit_grade(1))

        self.btn_hard = QPushButton("[2] Hard")
        self.btn_hard.setObjectName("GradeHard")
        self.btn_hard.setMinimumHeight(46)
        self.btn_hard.clicked.connect(lambda: self.submit_grade(2))

        self.btn_good = QPushButton("[3] Good")
        self.btn_good.setObjectName("GradeGood")
        self.btn_good.setMinimumHeight(46)
        self.btn_good.clicked.connect(lambda: self.submit_grade(3))

        self.btn_easy = QPushButton("[4] Easy")
        self.btn_easy.setObjectName("GradeEasy")
        self.btn_easy.setMinimumHeight(46)
        self.btn_easy.clicked.connect(lambda: self.submit_grade(4))

        grade_row.addWidget(self.btn_again)
        grade_row.addWidget(self.btn_hard)
        grade_row.addWidget(self.btn_good)
        grade_row.addWidget(self.btn_easy)
        layout.addWidget(self.grade_widget)

    def _bind_shortcuts(self) -> None:
        QShortcut(QKeySequence(Qt.Key_Space), self, activated=self.reveal_answer)
        QShortcut(QKeySequence("1"), self, activated=lambda: self._shortcut_grade(1))
        QShortcut(QKeySequence("2"), self, activated=lambda: self._shortcut_grade(2))
        QShortcut(QKeySequence("3"), self, activated=lambda: self._shortcut_grade(3))
        QShortcut(QKeySequence("4"), self, activated=lambda: self._shortcut_grade(4))

    def _shortcut_grade(self, grade: int) -> None:
        if self.is_revealed and self.current_index < len(self.queue):
            self.submit_grade(grade)

    def start_session(self, course_id: str | None = None) -> None:
        self.active_course_id = course_id
        self.course_selector.blockSignals(True)
        self.course_selector.clear()
        self.course_selector.addItem("All Due Courses", None)
        for c in self.db.list_courses():
            self.course_selector.addItem(c.title, c.id)
        if course_id:
            idx = self.course_selector.findData(course_id)
            if idx >= 0:
                self.course_selector.setCurrentIndex(idx)
        self.course_selector.blockSignals(False)
        self._load_queue()

    def _on_course_selector_changed(self) -> None:
        self.active_course_id = self.course_selector.currentData()
        self._load_queue()

    def _load_queue(self) -> None:
        self.queue = self.db.get_due_cards(course_id=self.active_course_id)
        self.current_index = 0
        self._render_current_card()

    def _render_current_card(self) -> None:
        total = len(self.queue)
        if total == 0 or self.current_index >= total:
            self.progress_bar.setMaximum(1)
            self.progress_bar.setValue(1)
            self.progress_bar.setFormat("All caught up! 0 cards due.")
            self.side_indicator.setText("SESSION COMPLETE")
            self.front_label.setText("All scheduled flashcards have been reviewed!")
            self.back_label.hide()
            self.divider.hide()
            self.reveal_btn.hide()
            self.grade_widget.hide()
            self.overdue_badge.setText("Retention Optimal")
            self.overdue_badge.setObjectName("HealthyBadge")
            self.overdue_badge.style().unpolish(self.overdue_badge)
            self.overdue_badge.style().polish(self.overdue_badge)
            self.course_badge.setText("")
            return

        card = self.queue[self.current_index]
        course = self.db.get_course(card.course_id)
        self.is_revealed = False
        self.card_start_time = time.monotonic()

        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(self.current_index)
        self.progress_bar.setFormat(f"Card {self.current_index + 1} of {total}")

        self.course_badge.setText(
            f"Course: {course.title if course else 'Unknown'}   •   Box {card.box}   •   Ease {card.ease_factor:.2f}"
        )

        now = datetime.now(timezone.utc)
        ret = SpacedRepetitionEngine.calculate_retention(card.last_reviewed_at, card.stability, now)
        overdue_days = max(0.0, (now - card.due_at).total_seconds() / 86400.0)

        if overdue_days >= 0.5 or ret < 0.65:
            self.overdue_badge.setText(
                f"Overdue by {overdue_days:.1f}d  |  Est. Retention: {ret * 100:.0f}%"
            )
            self.overdue_badge.setObjectName("OverdueBadge")
        else:
            self.overdue_badge.setText(f"Est. Retention: {ret * 100:.0f}%")
            self.overdue_badge.setObjectName("HealthyBadge")
        self.overdue_badge.style().unpolish(self.overdue_badge)
        self.overdue_badge.style().polish(self.overdue_badge)

        for grade, btn, label in [
            (1, self.btn_again, "[1] Again"),
            (2, self.btn_hard, "[2] Hard"),
            (3, self.btn_good, "[3] Good"),
            (4, self.btn_easy, "[4] Easy"),
        ]:
            preview = SpacedRepetitionEngine.process_review(
                grade,
                card.box,
                card.reps,
                card.interval_days,
                card.ease_factor,
                card.stability,
                card.last_reviewed_at,
                now,
            )
            btn.setText(f"{label} ({preview.new_interval_days:.1f}d)")

        self.side_indicator.setText("FRONT (PROMPT)")
        self.front_label.setText(card.front)
        self.back_label.setText(card.back)
        self.back_label.hide()
        self.divider.hide()
        self.reveal_btn.show()
        self.grade_widget.hide()

    def reveal_answer(self) -> None:
        if self.current_index >= len(self.queue) or self.is_revealed:
            return
        self.is_revealed = True
        self.side_indicator.setText("FRONT & BACK (ANSWER REVEALED)")
        self.divider.show()
        self.back_label.show()
        self.reveal_btn.hide()
        self.grade_widget.show()

    def submit_grade(self, grade: int) -> None:
        if self.current_index >= len(self.queue):
            return
        card = self.queue[self.current_index]
        elapsed_ms = int((time.monotonic() - self.card_start_time) * 1000)
        self.db.record_review(card.id, grade=grade, time_taken_ms=elapsed_ms)

        self.current_index += 1
        if self.current_index >= len(self.queue):
            self._render_current_card()
            self.session_completed.emit()
        else:
            self._render_current_card()
