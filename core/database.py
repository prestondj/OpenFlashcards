import csv
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import DB_PATH, DEFAULT_EASE_FACTOR, CRITICAL_RETENTION_THRESHOLD
from .models import Course, Card, ReviewLog, CourseStats
from .scheduler import SpacedRepetitionEngine


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    box INTEGER DEFAULT 1,
    reps INTEGER DEFAULT 0,
    interval_days REAL DEFAULT 0.0,
    ease_factor REAL DEFAULT 2.5,
    stability REAL DEFAULT 1.0,
    last_reviewed_at TIMESTAMP,
    due_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_logs (
    id TEXT PRIMARY KEY,
    card_id TEXT NOT NULL,
    grade INTEGER NOT NULL,
    reviewed_at TIMESTAMP NOT NULL,
    time_taken_ms INTEGER DEFAULT 0,
    interval_before REAL DEFAULT 0.0,
    interval_after REAL DEFAULT 0.0,
    FOREIGN KEY (card_id) REFERENCES cards (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cards_due ON cards (course_id, due_at);
CREATE INDEX IF NOT EXISTS idx_review_logs_card ON review_logs (card_id, reviewed_at);
"""


def _dt_to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _iso_to_dt(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    dt = datetime.fromisoformat(val)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class DatabaseManager:
    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)

    # ---------------- Course Operations ---------------- #

    def create_course(self, title: str, description: str = "") -> Course:
        now = datetime.now(timezone.utc)
        course_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO courses (id, title, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (course_id, title.strip(), description.strip(), _dt_to_iso(now), _dt_to_iso(now)),
            )
        return Course(
            id=course_id,
            title=title.strip(),
            description=description.strip(),
            created_at=now,
            updated_at=now,
        )

    def update_course(self, course_id: str, title: str, description: str = "") -> Optional[Course]:
        now = datetime.now(timezone.utc)
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE courses
                SET title = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (title.strip(), description.strip(), _dt_to_iso(now), course_id),
            )
        return self.get_course(course_id)

    def delete_course(self, course_id: str) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))

    def get_course(self, course_id: str) -> Optional[Course]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
            if not row:
                return None
            return self._row_to_course(row)

    def list_courses(self) -> list[Course]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM courses ORDER BY title COLLATE NOCASE ASC").fetchall()
            return [self._row_to_course(r) for r in rows]

    # ---------------- Card Operations ---------------- #

    def create_card(
        self,
        course_id: str,
        front: str,
        back: str,
        due_at: Optional[datetime] = None,
    ) -> Card:
        now = datetime.now(timezone.utc)
        due = due_at if due_at is not None else now
        card_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO cards (
                    id, course_id, front, back, box, reps, interval_days,
                    ease_factor, stability, last_reviewed_at, due_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, 1, 0, 0.0, ?, 1.0, NULL, ?, ?, ?)
                """,
                (
                    card_id,
                    course_id,
                    front.strip(),
                    back.strip(),
                    DEFAULT_EASE_FACTOR,
                    _dt_to_iso(due),
                    _dt_to_iso(now),
                    _dt_to_iso(now),
                ),
            )
        return self.get_card(card_id)

    def update_card_content(self, card_id: str, front: str, back: str, course_id: Optional[str] = None) -> Optional[Card]:
        now = datetime.now(timezone.utc)
        with self.get_connection() as conn:
            if course_id:
                conn.execute(
                    """
                    UPDATE cards
                    SET front = ?, back = ?, course_id = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (front.strip(), back.strip(), course_id, _dt_to_iso(now), card_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE cards
                    SET front = ?, back = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (front.strip(), back.strip(), _dt_to_iso(now), card_id),
                )
        return self.get_card(card_id)

    def reset_card_progress(self, card_id: str) -> Optional[Card]:
        now = datetime.now(timezone.utc)
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE cards
                SET box = 1, reps = 0, interval_days = 0.0, ease_factor = ?,
                    stability = 1.0, last_reviewed_at = NULL, due_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (DEFAULT_EASE_FACTOR, _dt_to_iso(now), _dt_to_iso(now), card_id),
            )
        return self.get_card(card_id)

    def delete_card(self, card_id: str) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))

    def get_card(self, card_id: str) -> Optional[Card]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
            if not row:
                return None
            return self._row_to_card(row)

    def list_cards(self, course_id: Optional[str] = None, search_query: str = "") -> list[Card]:
        query = "SELECT * FROM cards WHERE 1=1"
        params: list = []
        if course_id:
            query += " AND course_id = ?"
            params.append(course_id)
        if search_query.strip():
            like_q = f"%{search_query.strip()}%"
            query += " AND (front LIKE ? OR back LIKE ?)"
            params.extend([like_q, like_q])
        query += " ORDER BY due_at ASC"
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_card(r) for r in rows]

    # ---------------- Study & Scheduling Operations ---------------- #

    def get_due_cards(self, course_id: Optional[str] = None, now: Optional[datetime] = None) -> list[Card]:
        """
        Fetches all cards where due_at <= now, ordered by highest Overdue Priority Score first.
        """
        now_utc = SpacedRepetitionEngine._ensure_utc(now)
        query = "SELECT * FROM cards WHERE due_at <= ?"
        params: list = [_dt_to_iso(now_utc)]
        if course_id:
            query += " AND course_id = ?"
            params.append(course_id)

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            cards = [self._row_to_card(r) for r in rows]

        # Sort descending by overdue priority score so the most at-risk memories are reviewed first
        cards.sort(
            key=lambda c: SpacedRepetitionEngine.calculate_overdue_score(c.due_at, c.interval_days, now_utc),
            reverse=True,
        )
        return cards

    def record_review(
        self,
        card_id: str,
        grade: int,
        time_taken_ms: int = 0,
        now: Optional[datetime] = None,
    ) -> Card:
        now_utc = SpacedRepetitionEngine._ensure_utc(now)
        card = self.get_card(card_id)
        if not card:
            raise ValueError(f"Card {card_id} not found")

        result = SpacedRepetitionEngine.process_review(
            grade=grade,
            current_box=card.box,
            reps=card.reps,
            interval_days=card.interval_days,
            ease_factor=card.ease_factor,
            stability=card.stability,
            last_reviewed_at=card.last_reviewed_at,
            now=now_utc,
        )

        log_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE cards
                SET box = ?, reps = ?, interval_days = ?, ease_factor = ?,
                    stability = ?, last_reviewed_at = ?, due_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    result.new_box,
                    result.new_reps,
                    result.new_interval_days,
                    result.new_ease_factor,
                    result.new_stability,
                    _dt_to_iso(now_utc),
                    _dt_to_iso(result.new_due_at),
                    _dt_to_iso(now_utc),
                    card_id,
                ),
            )
            conn.execute(
                """
                INSERT INTO review_logs (
                    id, card_id, grade, reviewed_at, time_taken_ms, interval_before, interval_after
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    card_id,
                    grade,
                    _dt_to_iso(now_utc),
                    time_taken_ms,
                    card.interval_days,
                    result.new_interval_days,
                ),
            )
        return self.get_card(card_id)

    def get_course_stats(self, course_id: str, now: Optional[datetime] = None) -> CourseStats:
        now_utc = SpacedRepetitionEngine._ensure_utc(now)
        cards = self.list_cards(course_id=course_id)
        total = len(cards)
        due_count = 0
        critical_count = 0
        retentions = []
        box_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for card in cards:
            box_dist[card.box] = box_dist.get(card.box, 0) + 1
            if card.due_at <= now_utc:
                due_count += 1
            r = SpacedRepetitionEngine.calculate_retention(card.last_reviewed_at, card.stability, now_utc)
            retentions.append(r)
            if card.last_reviewed_at is not None and r < CRITICAL_RETENTION_THRESHOLD:
                critical_count += 1

        avg_ret = (sum(retentions) / total) if total > 0 else 1.0
        return CourseStats(
            course_id=course_id,
            total_cards=total,
            due_count=due_count,
            overdue_critical_count=critical_count,
            average_retention=round(avg_ret, 4),
            box_distribution=box_dist,
        )

    # ---------------- Batch Import / Export ---------------- #

    def export_course_json(self, course_id: str, file_path: str | Path) -> int:
        course = self.get_course(course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found")
        cards = self.list_cards(course_id=course_id)
        payload = {
            "course": {
                "title": course.title,
                "description": course.description,
            },
            "cards": [
                {
                    "front": c.front,
                    "back": c.back,
                    "box": c.box,
                    "reps": c.reps,
                    "interval_days": c.interval_days,
                    "ease_factor": c.ease_factor,
                    "stability": c.stability,
                }
                for c in cards
            ],
        }
        Path(file_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return len(cards)

    def import_cards_json(self, course_id: str, file_path: str | Path) -> int:
        data = json.loads(Path(file_path).read_text(encoding="utf-8"))
        cards_list = data.get("cards", data if isinstance(data, list) else [])
        count = 0
        for item in cards_list:
            front = str(item.get("front", "")).strip()
            back = str(item.get("back", "")).strip()
            if front and back:
                self.create_card(course_id=course_id, front=front, back=back)
                count += 1
        return count

    def export_course_csv(self, course_id: str, file_path: str | Path) -> int:
        cards = self.list_cards(course_id=course_id)
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["front", "back", "box", "reps", "interval_days", "ease_factor", "stability"])
            for c in cards:
                writer.writerow([c.front, c.back, c.box, c.reps, c.interval_days, c.ease_factor, c.stability])
        return len(cards)

    def import_cards_csv(self, course_id: str, file_path: str | Path) -> int:
        count = 0
        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                front = (row.get("front") or "").strip()
                back = (row.get("back") or "").strip()
                if front and back:
                    self.create_card(course_id=course_id, front=front, back=back)
                    count += 1
        return count

    # ---------------- Row Mappers ---------------- #

    @staticmethod
    def _row_to_course(row: sqlite3.Row) -> Course:
        return Course(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            created_at=_iso_to_dt(row["created_at"]),
            updated_at=_iso_to_dt(row["updated_at"]),
        )

    @staticmethod
    def _row_to_card(row: sqlite3.Row) -> Card:
        return Card(
            id=row["id"],
            course_id=row["course_id"],
            front=row["front"],
            back=row["back"],
            box=int(row["box"]),
            reps=int(row["reps"]),
            interval_days=float(row["interval_days"]),
            ease_factor=float(row["ease_factor"]),
            stability=float(row["stability"]),
            last_reviewed_at=_iso_to_dt(row["last_reviewed_at"]),
            due_at=_iso_to_dt(row["due_at"]),
            created_at=_iso_to_dt(row["created_at"]),
            updated_at=_iso_to_dt(row["updated_at"]),
        )
