from datetime import datetime, timedelta, timezone
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QLinearGradient
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QDialog,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QGridLayout,
)

from core.database import DatabaseManager
from core.models import Course
from core.scheduler import SpacedRepetitionEngine


class ForgettingCurveWidget(QWidget):
    """Draws a smooth Ebbinghaus retention decay curve R = e^(-t/S) with gradient fill."""

    def __init__(self, stability: float = 3.0, parent=None):
        super().__init__(parent)
        self.stability = max(0.2, stability)
        self.setMinimumHeight(105)
        self.setMaximumHeight(115)

    def set_stability(self, stability: float) -> None:
        self.stability = max(0.2, stability)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Subtle inset chart background
        bg_rect = QRectF(0.5, 0.5, w - 1.0, h - 1.0)
        painter.setPen(QPen(QColor("#26334d"), 1))
        painter.setBrush(QColor("#0f172a"))
        painter.drawRoundedRect(bg_rect, 8.0, 8.0)

        pad_left, pad_right = 16, 16
        pad_top, pad_bottom = 26, 14
        plot_w = max(10, w - pad_left - pad_right)
        plot_h = max(10, h - pad_top - pad_bottom)

        # Draw 50% critical threshold dashed line
        threshold_y = pad_top + plot_h * 0.5
        pen_thresh = QPen(QColor(239, 68, 68, 110), 1, Qt.DashLine)
        painter.setPen(pen_thresh)
        painter.drawLine(int(pad_left), int(threshold_y), int(pad_left + plot_w), int(threshold_y))

        # Generate curve coordinates
        points = SpacedRepetitionEngine.get_learning_curve_points(self.stability, days_horizon=14, steps=45)
        coords = []
        for day, ret_pct in points:
            x = pad_left + (day / 14.0) * plot_w
            y = pad_top + ((100.0 - ret_pct) / 100.0) * plot_h
            coords.append((x, y))

        if coords:
            # Area fill path
            fill_path = QPainterPath()
            fill_path.moveTo(coords[0][0], pad_top + plot_h)
            for x, y in coords:
                fill_path.lineTo(x, y)
            fill_path.lineTo(coords[-1][0], pad_top + plot_h)
            fill_path.closeSubpath()

            grad = QLinearGradient(0, pad_top, 0, pad_top + plot_h)
            grad.setColorAt(0.0, QColor(56, 189, 248, 75))
            grad.setColorAt(1.0, QColor(56, 189, 248, 4))
            painter.fillPath(fill_path, grad)

            # Stroke path
            line_path = QPainterPath()
            line_path.moveTo(coords[0][0], coords[0][1])
            for x, y in coords[1:]:
                line_path.lineTo(x, y)

            painter.setPen(QPen(QColor("#38bdf8"), 2.2))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(line_path)

        # Caption & 50% marker label
        painter.setPen(QColor("#94a3b8"))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(pad_left, 17, f"14-Day Forgetting Curve  •  Stability S = {self.stability:.1f}d")

        painter.setPen(QColor(252, 165, 165, 160))
        painter.drawText(int(pad_left + plot_w - 62), int(threshold_y - 4), "50% Crit.")
        painter.end()


class CourseDialog(QDialog):
    def __init__(self, parent=None, course: Course | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Course" if course else "New Course")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        form = QFormLayout()
        form.setSpacing(10)

        self.title_input = QLineEdit(course.title if course else "")
        self.title_input.setPlaceholderText("e.g., Computer Networks & Protocols")
        self.desc_input = QTextEdit(course.description if course else "")
        self.desc_input.setPlaceholderText("Course summary or exam module notes...")
        self.desc_input.setMaximumHeight(90)

        form.addRow("Course Title:", self.title_input)
        form.addRow("Description:", self.desc_input)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        save_btn = QPushButton("Save Course")
        save_btn.setObjectName("PrimaryButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_save(self) -> None:
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Course title cannot be empty.")
            return
        self.accept()

    def get_data(self) -> tuple[str, str]:
        return self.title_input.text().strip(), self.desc_input.toPlainText().strip()


class CourseDashboardView(QWidget):
    study_requested = Signal(str)        # course_id
    manage_cards_requested = Signal(str) # course_id

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(18)

        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        header = QLabel("Course Bundles & Learning Curves")
        header.setObjectName("HeaderTitle")
        sub = QLabel("Prioritize overdue cards and monitor Ebbinghaus memory retention across courses.")
        sub.setObjectName("SubTitle")
        title_col.addWidget(header)
        title_col.addWidget(sub)
        header_row.addLayout(title_col)
        header_row.addStretch()

        demo_btn = QPushButton("Load Demo Course")
        demo_btn.clicked.connect(self._seed_demo_course)
        header_row.addWidget(demo_btn)

        new_course_btn = QPushButton("+ New Course")
        new_course_btn.setObjectName("PrimaryButton")
        new_course_btn.clicked.connect(self._create_course_dialog)
        header_row.addWidget(new_course_btn)

        main_layout.addLayout(header_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.grid_container = QWidget()
        self.grid_container.setObjectName("ScrollCanvas")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 4, 0, 12)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.grid_container)

        main_layout.addWidget(self.scroll)

    def refresh(self) -> None:
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        courses = self.db.list_courses()
        if not courses:
            empty_label = QLabel(
                "No courses yet. Click '+ New Course' or 'Load Demo Course' to begin."
            )
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setObjectName("SubTitle")
            empty_label.setMinimumHeight(220)
            self.grid_layout.addWidget(empty_label, 0, 0)
            return

        for idx, course in enumerate(courses):
            tile = self._build_course_tile(course)
            row = idx // 2
            col = idx % 2
            self.grid_layout.addWidget(tile, row, col)

    def _build_course_tile(self, course: Course) -> QFrame:
        stats = self.db.get_course_stats(course.id)
        cards = self.db.list_cards(course_id=course.id)
        avg_stability = (
            sum(c.stability for c in cards) / len(cards) if cards else 1.0
        )

        tile = QFrame()
        tile.setObjectName("CourseTile")
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        title_lbl = QLabel(course.title)
        title_lbl.setObjectName("CourseTitle")
        top_row.addWidget(title_lbl)
        top_row.addStretch()

        badge = QLabel()
        if stats.overdue_critical_count > 0:
            badge.setText(f"{stats.overdue_critical_count} Critical Overdue (R < 50%)")
            badge.setObjectName("OverdueBadge")
        else:
            badge.setText(f"Avg Retention: {stats.average_retention * 100:.0f}%")
            badge.setObjectName("HealthyBadge")
        top_row.addWidget(badge)
        layout.addLayout(top_row)

        if course.description:
            desc_lbl = QLabel(course.description)
            desc_lbl.setObjectName("SubTitle")
            desc_lbl.setWordWrap(True)
            layout.addWidget(desc_lbl)

        metrics_lbl = QLabel(
            f"Total Cards: <b>{stats.total_cards}</b> &nbsp;&bull;&nbsp; "
            f"Due Now: <b>{stats.due_count}</b> &nbsp;&bull;&nbsp; "
            f"Leitner Boxes (1–5): <b>{stats.box_distribution[1]} / {stats.box_distribution[2]} / "
            f"{stats.box_distribution[3]} / {stats.box_distribution[4]} / {stats.box_distribution[5]}</b>"
        )
        metrics_lbl.setObjectName("MetricsLabel")
        layout.addWidget(metrics_lbl)

        curve = ForgettingCurveWidget(stability=avg_stability)
        layout.addWidget(curve)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        study_btn = QPushButton(f"Study Due ({stats.due_count})")
        study_btn.setObjectName("PrimaryButton")
        study_btn.setEnabled(stats.due_count > 0)
        study_btn.clicked.connect(lambda _, cid=course.id: self.study_requested.emit(cid))

        manage_btn = QPushButton("Manage Cards")
        manage_btn.clicked.connect(lambda _, cid=course.id: self.manage_cards_requested.emit(cid))

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda _, c=course: self._edit_course_dialog(c))

        del_btn = QPushButton("Delete")
        del_btn.setObjectName("DangerButton")
        del_btn.clicked.connect(lambda _, c=course: self._delete_course(c))

        btn_row.addWidget(study_btn)
        btn_row.addWidget(manage_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

        return tile

    def _create_course_dialog(self) -> None:
        dlg = CourseDialog(self)
        if dlg.exec() == QDialog.Accepted:
            title, desc = dlg.get_data()
            self.db.create_course(title, desc)
            self.refresh()

    def _edit_course_dialog(self, course: Course) -> None:
        dlg = CourseDialog(self, course=course)
        if dlg.exec() == QDialog.Accepted:
            title, desc = dlg.get_data()
            self.db.update_course(course.id, title, desc)
            self.refresh()

    def _delete_course(self, course: Course) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Course",
            f"Delete '{course.title}' and all its flashcards permanently?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_course(course.id)
            self.refresh()

    def _seed_demo_course(self) -> None:
        now = datetime.now(timezone.utc)
        course = self.db.create_course(
            "Computer Science Fundamentals",
            "Sample deck demonstrating overdue prioritization and Ebbinghaus retention decay.",
        )
        c1 = self.db.create_card(
            course.id,
            "What is the Ebbinghaus Forgetting Curve formula?",
            "R = exp(-t / S), where R is memory retention, t is elapsed time, and S is stability.",
        )
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE cards
                SET box = 2, reps = 2, interval_days = 2.0, stability = 2.0,
                    last_reviewed_at = ?, due_at = ?
                WHERE id = ?
                """,
                (
                    (now - timedelta(days=9)).isoformat(),
                    (now - timedelta(days=7)).isoformat(),
                    c1.id,
                ),
            )

        c2 = self.db.create_card(
            course.id,
            "What does SQLite WAL mode provide?",
            "Write-Ahead Logging allows concurrent reads while a write transaction is occurring.",
        )
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE cards
                SET box = 3, reps = 3, interval_days = 4.0, stability = 4.0,
                    last_reviewed_at = ?, due_at = ?
                WHERE id = ?
                """,
                (
                    (now - timedelta(days=6)).isoformat(),
                    (now - timedelta(days=2)).isoformat(),
                    c2.id,
                ),
            )

        self.db.create_card(
            course.id,
            "What is the time complexity of searching a balanced Binary Search Tree (BST)?",
            "O(log n) average and worst-case time complexity.",
        )
        self.refresh()
