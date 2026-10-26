APP_STYLESHEET = """
/* Base Window & Dialogs */
QMainWindow, QDialog, QMessageBox {
    background-color: #0f172a;
    color: #f1f5f9;
    font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif;
    font-size: 14px;
}

/* Prevent child widgets & labels from drawing dark boxes over cards/frames */
QWidget {
    color: #f1f5f9;
    font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif;
    font-size: 14px;
}

QLabel, QFrame {
    background-color: transparent;
    border: none;
}

QScrollArea, QWidget#ScrollCanvas {
    background-color: transparent;
    border: none;
}

/* Sidebar Navigation */
QFrame#Sidebar {
    background-color: #111827;
    border-right: 1px solid #1e293b;
}

QPushButton#NavButton {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 14px;
    font-weight: 600;
}

QPushButton#NavButton:hover {
    background-color: #1e293b;
    color: #f8fafc;
}

QPushButton#NavButton:checked {
    background-color: #1e293b;
    color: #38bdf8;
    border: 1px solid #334155;
}

/* Elevated Surfaces (Course Tiles & Study Flashcard) */
QFrame#CardSurface, QFrame#CourseTile {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
}

QFrame#Divider {
    background-color: #334155;
    max-height: 1px;
    min-height: 1px;
    border: none;
}

/* Typography */
QLabel#HeaderTitle {
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
    background-color: transparent;
}

QLabel#SubTitle {
    font-size: 13px;
    color: #94a3b8;
    background-color: transparent;
}

QLabel#CourseTitle {
    font-size: 17px;
    font-weight: 700;
    color: #f8fafc;
    background-color: transparent;
}

QLabel#MetricsLabel {
    font-size: 13px;
    color: #cbd5e1;
    background-color: #0f172a;
    border: 1px solid #26334d;
    border-radius: 8px;
    padding: 8px 12px;
}

QLabel#FlashcardText {
    font-size: 21px;
    font-weight: 600;
    color: #f8fafc;
    padding: 24px;
    background-color: transparent;
}

/* Status Badges */
QLabel#OverdueBadge {
    background-color: rgba(239, 68, 68, 0.16);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.45);
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 600;
    font-size: 12px;
}

QLabel#HealthyBadge {
    background-color: rgba(16, 185, 129, 0.16);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.45);
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 600;
    font-size: 12px;
}

/* Standard Buttons */
QPushButton {
    background-color: #26334d;
    color: #f1f5f9;
    border: 1px solid #3b4c6b;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #475569;
}

QPushButton:pressed {
    background-color: #1e293b;
}

QPushButton:disabled {
    background-color: #162032;
    color: #475569;
    border-color: #1e293b;
}

QPushButton#PrimaryButton {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
    color: #ffffff;
}

QPushButton#PrimaryButton:hover {
    background-color: #1d4ed8;
    border-color: #60a5fa;
}

QPushButton#DangerButton {
    background-color: rgba(220, 38, 38, 0.18);
    border: 1px solid rgba(239, 68, 68, 0.45);
    color: #fca5a5;
}

QPushButton#DangerButton:hover {
    background-color: #b91c1c;
    border-color: #ef4444;
    color: #ffffff;
}

/* Study Session Grade Buttons */
QPushButton#GradeAgain {
    background-color: rgba(220, 38, 38, 0.22);
    border: 1px solid #ef4444;
    color: #fecaca;
}
QPushButton#GradeAgain:hover {
    background-color: #b91c1c;
    color: #ffffff;
}

QPushButton#GradeHard {
    background-color: rgba(234, 88, 12, 0.22);
    border: 1px solid #f97316;
    color: #fed7aa;
}
QPushButton#GradeHard:hover {
    background-color: #c2410c;
    color: #ffffff;
}

QPushButton#GradeGood {
    background-color: rgba(22, 163, 74, 0.22);
    border: 1px solid #22c55e;
    color: #bbf7d0;
}
QPushButton#GradeGood:hover {
    background-color: #15803d;
    color: #ffffff;
}

QPushButton#GradeEasy {
    background-color: rgba(37, 99, 235, 0.22);
    border: 1px solid #3b82f6;
    color: #bfdbfe;
}
QPushButton#GradeEasy:hover {
    background-color: #1d4ed8;
    color: #ffffff;
}

/* Form Inputs */
QLineEdit, QTextEdit, QComboBox {
    background-color: #162032;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 11px;
    selection-background-color: #2563eb;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #38bdf8;
    background-color: #1a263d;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    selection-background-color: #2563eb;
    outline: 0;
}

/* Tables */
QTableWidget {
    background-color: #1e293b;
    alternate-background-color: #172033;
    color: #f1f5f9;
    gridline-color: #26334d;
    border: 1px solid #334155;
    border-radius: 10px;
    selection-background-color: rgba(37, 99, 235, 0.35);
    selection-color: #ffffff;
    outline: 0;
}

QTableWidget::item {
    padding: 6px 10px;
    border: none;
}

QHeaderView::section {
    background-color: #111827;
    color: #94a3b8;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #334155;
}

QTableCornerButton::section {
    background-color: #111827;
    border: none;
}

/* Progress Bar */
QProgressBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    text-align: center;
    color: #e2e8f0;
    font-weight: 600;
    font-size: 12px;
    min-height: 22px;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 7px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 24px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
