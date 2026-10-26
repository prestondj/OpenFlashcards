# OpenFlashcards v2.0

A desktop spaced-repetition flashcard application built with **Python 3.11+**, **PySide6 (Qt)**, and **SQLite (WAL mode)**. Designed around the **Ebbinghaus Forgetting Curve** ($R = e^{-\Delta t / S}$), hybrid **Leitner + SM-2** scheduling, and **Overdue Priority Score** ranking.

## Features
- **Course Bundling:** Group flashcards into courses with per-course retention statistics and live 14-day Ebbinghaus forgetting curves.
- **Overdue Prioritization:** Due cards are dynamically ranked by `Overdue Score = (now - due_at) / max(1.0, interval_days)` so the memories most at risk of decay are reviewed first.
- **Full Flashcard CRUD & Batch I/O:** Add, edit, search, reset progress, delete, and import/export decks in **JSON** or **CSV** formats.
- **Keyboard-Driven Study Session:** Flip cards with `Space` and grade responses with keys `1` (Again), `2` (Hard), `3` (Good), and `4` (Easy).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Running Unit Tests

```bash
python -m unittest discover -s tests -v
```
