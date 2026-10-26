import math
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

from config import MIN_EASE_FACTOR, MAX_BOX


@dataclass
class ReviewResult:
    new_box: int
    new_reps: int
    new_interval_days: float
    new_ease_factor: float
    new_stability: float
    new_due_at: datetime
    retention_before: float


class SpacedRepetitionEngine:
    """
    Hybrid Leitner + SM-2 + Ebbinghaus exponential forgetting curve scheduler.
    R(t) = exp(-delta_t / S)
    """

    @staticmethod
    def _ensure_utc(dt: Optional[datetime]) -> datetime:
        if dt is None:
            return datetime.now(timezone.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @classmethod
    def calculate_retention(
        cls,
        last_reviewed: Optional[datetime],
        stability: float,
        now: Optional[datetime] = None,
    ) -> float:
        """
        Calculates estimated recall probability R = exp(-delta_t / max(S, 0.1)).
        If the card has never been reviewed, returns 1.0 if not yet due, else decays from creation/due.
        """
        if last_reviewed is None:
            return 1.0
        now_utc = cls._ensure_utc(now)
        last_utc = cls._ensure_utc(last_reviewed)
        delta_days = max(0.0, (now_utc - last_utc).total_seconds() / 86400.0)
        s = max(0.1, float(stability))
        retention = math.exp(-delta_days / s)
        return max(0.0, min(1.0, retention))

    @classmethod
    def calculate_overdue_score(
        cls,
        due_at: datetime,
        interval_days: float,
        now: Optional[datetime] = None,
    ) -> float:
        """
        Calculates urgency ratio: (now - due_at) in days / max(1.0, interval_days).
        Positive values indicate overdue cards; higher values mean higher urgency.
        """
        now_utc = cls._ensure_utc(now)
        due_utc = cls._ensure_utc(due_at)
        overdue_days = (now_utc - due_utc).total_seconds() / 86400.0
        denominator = max(1.0, float(interval_days))
        return overdue_days / denominator

    @classmethod
    def get_learning_curve_points(cls, stability: float, days_horizon: int = 30, steps: int = 60) -> list[tuple[float, float]]:
        """
        Generates (day, retention_percent) points for plotting the forgetting curve of a card or course.
        """
        s = max(0.1, float(stability))
        points = []
        for i in range(steps + 1):
            t = (days_horizon * i) / steps
            r = math.exp(-t / s) * 100.0
            points.append((round(t, 2), round(r, 2)))
        return points

    @classmethod
    def process_review(
        cls,
        grade: int,
        current_box: int,
        reps: int,
        interval_days: float,
        ease_factor: float,
        stability: float = 1.0,
        last_reviewed_at: Optional[datetime] = None,
        now: Optional[datetime] = None,
    ) -> ReviewResult:
        """
        Grades:
          1 = Again (Fail, reset to Box 1, 10m interval ~ 0.007 days or 0.1 days)
          2 = Hard  (Pass with difficulty, small interval increase, slight ease penalty)
          3 = Good  (Standard recall, Leitner/SM-2 progression)
          4 = Easy  (Effortless recall, bonus interval & ease increase)
        """
        if grade not in (1, 2, 3, 4):
            raise ValueError(f"Invalid review grade {grade}. Must be 1, 2, 3, or 4.")

        now_utc = cls._ensure_utc(now)
        retention_before = cls.calculate_retention(last_reviewed_at, stability, now_utc)

        # Calculate actual elapsed time if reviewed late (overdue bonus on pass)
        elapsed_days = 0.0
        if last_reviewed_at is not None:
            elapsed_days = max(0.0, (now_utc - cls._ensure_utc(last_reviewed_at)).total_seconds() / 86400.0)

        effective_base = max(interval_days, elapsed_days * 0.5) if grade >= 3 else interval_days

        if grade == 1:  # Again
            new_box = 1
            new_reps = 0
            new_interval = 0.1  # ~2.4 hours / same-day re-review
            new_ease = max(MIN_EASE_FACTOR, ease_factor - 0.20)
            new_stability = max(0.25, stability * 0.4)
        elif grade == 2:  # Hard
            new_box = max(1, current_box)
            new_reps = reps + 1
            new_interval = max(1.0, interval_days * 1.2)
            new_ease = max(MIN_EASE_FACTOR, ease_factor - 0.15)
            new_stability = max(1.0, new_interval * 0.9)
        elif grade == 3:  # Good
            new_box = min(MAX_BOX, current_box + 1)
            new_reps = reps + 1
            new_ease = ease_factor
            if reps == 0:
                new_interval = 1.0
            elif reps == 1:
                new_interval = 3.0
            else:
                new_interval = round(effective_base * new_ease, 2)
            new_stability = max(1.0, new_interval)
        else:  # grade == 4 (Easy)
            new_box = min(MAX_BOX, current_box + 1)
            new_reps = reps + 1
            new_ease = ease_factor + 0.15
            if reps == 0:
                new_interval = 4.0
            else:
                new_interval = round(max(4.0, effective_base * new_ease * 1.3), 2)
            new_stability = max(1.5, new_interval * 1.15)

        new_due_at = now_utc + timedelta(days=new_interval)

        return ReviewResult(
            new_box=new_box,
            new_reps=new_reps,
            new_interval_days=round(new_interval, 4),
            new_ease_factor=round(new_ease, 4),
            new_stability=round(new_stability, 4),
            new_due_at=new_due_at,
            retention_before=round(retention_before, 4),
        )
