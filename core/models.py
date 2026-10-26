from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Course:
    id: str
    title: str
    description: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Card:
    id: str
    course_id: str
    front: str
    back: str
    box: int
    reps: int
    interval_days: float
    ease_factor: float
    stability: float
    last_reviewed_at: Optional[datetime]
    due_at: datetime
    created_at: datetime
    updated_at: datetime


@dataclass
class ReviewLog:
    id: str
    card_id: str
    grade: int
    reviewed_at: datetime
    time_taken_ms: int
    interval_before: float
    interval_after: float


@dataclass
class CourseStats:
    course_id: str
    total_cards: int
    due_count: int
    overdue_critical_count: int
    average_retention: float
    box_distribution: dict[int, int]
