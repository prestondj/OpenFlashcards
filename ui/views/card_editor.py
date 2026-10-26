from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QTextEdit,
    QMessageBox,
    QFileDialog,
    QAbstractItemView,
)

from core.database import DatabaseManager
from core.models import Card
from core.scheduler import SpacedRepetitionEngine


class CardDialog(QDialog):
    def __init__(self, db: DatabaseManager, parent=None, card: Card | None = None, default_course_id: str | None = None):
        super().__init__(parent)
        self.db = db
        self.card = card
        self.setWindowTitle("Edit Flashcard" if card else "New Flashcard")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        form = QFormLayout()
        form.setSpacing(10)

        self.course_combo = QComboBox()
        self.courses = self.db.list_courses()
        for c in self.courses:
            self.course_combo.addItem(c.title, c.id)

        target_course_id = card.course_id if card else default_course_id
        if target_course_id:
            idx = self.course_combo.findData(target_course_id)
            if idx >= 0:
                self.course_combo.setCurrentIndex(idx)

        self.front_input = QTextEdit(card.front if card else "")
        self.front_input.setPlaceholderText("Question / Prompt on the front of the card...")
        self.front_input.setMinimumHeight(95)

        self.back_input = QTextEdit(card.back if card else "")
        self.back_input.setPlaceholderText("Answer / Explanation on the back of the card...")
        self.back_input.setMinimumHeight(95)

        form.addRow("Course:", self.course_combo)
        form.addRow("Front (Prompt):", self.front_input)
        form.addRow("Back (Answer):", self.back_input)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        save_btn = QPushButton("Save Flashcard")
        save_btn.setObjectName("PrimaryButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_save(self) -> None:
        if not self.courses:
            QMessageBox.warning(self, "No Course", "Please create a course first.")
            return
        if not self.front_input.toPlainText().strip() or not self.back_input.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Both Front and Back fields are required.")
            return
        self.accept()

    def get_data(self) -> tuple[str, str, str]:
        return (
            self.course_combo.currentData(),
            self.front_input.toPlainText().strip(),
            self.back_input.toPlainText().strip(),
        )


class CardEditorView(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._cards: list[Card] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        header = QLabel("Flashcard Manager & Editor")
        header.setObjectName("HeaderTitle")
        header_row.addWidget(header)
        header_row.addStretch()

        import_btn = QPushButton("Import (CSV/JSON)")
        import_btn.clicked.connect(self._import_cards)
        export_btn = QPushButton("Export (CSV/JSON)")
        export_btn.clicked.connect(self._export_cards)
        add_btn = QPushButton("+ Add Flashcard")
        add_btn.setObjectName("PrimaryButton")
        add_btn.clicked.connect(self._add_card)

        header_row.addWidget(import_btn)
        header_row.addWidget(export_btn)
        header_row.addWidget(add_btn)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)
        filter_row.addWidget(QLabel("Course:"))
        self.course_filter = QComboBox()
        self.course_filter.setMinimumWidth(230)
        self.course_filter.currentIndexChanged.connect(self._populate_table)
        filter_row.addWidget(self.course_filter)

        filter_row.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by front or back text...")
        self.search_input.textChanged.connect(self._populate_table)
        filter_row.addWidget(self.search_input)
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Course", "Front", "Back", "Box", "Interval (d)", "Retention", "Due Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(self._edit_selected_card)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self._edit_selected_card)
        reset_btn = QPushButton("Reset Learning Progress")
        reset_btn.clicked.connect(self._reset_selected_card)
        del_btn = QPushButton("Delete Selected")
        del_btn.setObjectName("DangerButton")
        del_btn.clicked.connect(self._delete_selected_card)

        action_row.addWidget(edit_btn)
        action_row.addWidget(reset_btn)
        action_row.addStretch()
        action_row.addWidget(del_btn)
        layout.addLayout(action_row)

    def select_course(self, course_id: str) -> None:
        self.refresh()
        idx = self.course_filter.findData(course_id)
        if idx >= 0:
            self.course_filter.setCurrentIndex(idx)

    def refresh(self) -> None:
        current_course_id = self.course_filter.currentData()
        self.course_filter.blockSignals(True)
        self.course_filter.clear()
        self.course_filter.addItem("All Courses", None)
        for c in self.db.list_courses():
            self.course_filter.addItem(c.title, c.id)
        if current_course_id:
            idx = self.course_filter.findData(current_course_id)
            if idx >= 0:
                self.course_filter.setCurrentIndex(idx)
        self.course_filter.blockSignals(False)
        self._populate_table()

    def _populate_table(self) -> None:
        course_id = self.course_filter.currentData()
        query = self.search_input.text().strip()
        self._cards = self.db.list_cards(course_id=course_id, search_query=query)
        courses_map = {c.id: c.title for c in self.db.list_courses()}

        self.table.setRowCount(len(self._cards))
        for row_idx, card in enumerate(self._cards):
            ret = SpacedRepetitionEngine.calculate_retention(card.last_reviewed_at, card.stability)
            overdue_score = SpacedRepetitionEngine.calculate_overdue_score(card.due_at, card.interval_days)
            if overdue_score >= 0:
                due_str = f"Overdue ({overdue_score:.2f}x)" if overdue_score > 0.05 else "Due Now"
            else:
                due_str = card.due_at.strftime("%Y-%m-%d %H:%M")

            vals = [
                courses_map.get(card.course_id, "Unknown"),
                card.front.replace("\n", " "),
                card.back.replace("\n", " "),
                f"Box {card.box}",
                f"{card.interval_days:.1f}",
                f"{ret * 100:.0f}%",
                due_str,
            ]
            for col_idx, text in enumerate(vals):
                item = QTableWidgetItem(text)
                if col_idx in (3, 4, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

    def _get_selected_card(self) -> Card | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._cards):
            return None
        return self._cards[row]

    def _add_card(self) -> None:
        if not self.db.list_courses():
            QMessageBox.information(self, "Create a Course First", "Please create a course before adding flashcards.")
            return
        dlg = CardDialog(self.db, self, default_course_id=self.course_filter.currentData())
        if dlg.exec() == QDialog.Accepted:
            cid, front, back = dlg.get_data()
            self.db.create_card(cid, front, back)
            self._populate_table()

    def _edit_selected_card(self) -> None:
        card = self._get_selected_card()
        if not card:
            return
        dlg = CardDialog(self.db, self, card=card)
        if dlg.exec() == QDialog.Accepted:
            cid, front, back = dlg.get_data()
            self.db.update_card_content(card.id, front, back, course_id=cid)
            self._populate_table()

    def _reset_selected_card(self) -> None:
        card = self._get_selected_card()
        if not card:
            return
        reply = QMessageBox.question(
            self,
            "Reset Learning Progress",
            "Are you sure you want to reset the learning progress and forgetting curve for this card?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.reset_card_progress(card.id)
            self._populate_table()

    def _delete_selected_card(self) -> None:
        card = self._get_selected_card()
        if not card:
            return
        reply = QMessageBox.question(
            self,
            "Delete Flashcard",
            "Delete the selected flashcard permanently?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_card(card.id)
            self._populate_table()

    def _import_cards(self) -> None:
        course_id = self.course_filter.currentData()
        if not course_id:
            courses = self.db.list_courses()
            if not courses:
                QMessageBox.warning(self, "No Course", "Create and select a course before importing cards.")
                return
            course_id = courses[0].id

        path, _ = QFileDialog.getOpenFileName(
            self, "Import Flashcards", "", "Data Files (*.json *.csv)"
        )
        if not path:
            return
        try:
            if path.lower().endswith(".json"):
                count = self.db.import_cards_json(course_id, path)
            else:
                count = self.db.import_cards_csv(course_id, path)
            QMessageBox.information(self, "Import Complete", f"Imported {count} flashcards.")
            self._populate_table()
        except Exception as exc:
            QMessageBox.critical(self, "Import Failed", str(exc))

    def _export_cards(self) -> None:
        course_id = self.course_filter.currentData()
        if not course_id:
            QMessageBox.information(self, "Select Course", "Select a specific course in the filter to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Course Flashcards", "flashcards_export.json", "JSON (*.json);;CSV (*.csv)"
        )
        if not path:
            return
        try:
            if path.lower().endswith(".csv"):
                count = self.db.export_course_csv(course_id, path)
            else:
                count = self.db.export_course_json(course_id, path)
            QMessageBox.information(self, "Export Complete", f"Exported {count} flashcards.")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))
