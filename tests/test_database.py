import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from core.database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_flashcards.db"
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_course_and_card_crud_and_cascade(self):
        course = self.db.create_course("Distributed Systems", "Consensus & RPC")
        card1 = self.db.create_card(course.id, "What is Raft?", "A consensus algorithm.")
        card2 = self.db.create_card(course.id, "What is Paxos?", "A family of consensus protocols.")

        cards = self.db.list_cards(course_id=course.id)
        self.assertEqual(len(cards), 2)

        updated = self.db.update_card_content(card1.id, "Define Raft.", "A log-replicated consensus algorithm.")
        self.assertEqual(updated.front, "Define Raft.")

        # Deleting course must cascade delete cards
        self.db.delete_course(course.id)
        self.assertEqual(len(self.db.list_cards(course_id=course.id)), 0)

    def test_overdue_ordering_and_review_logging(self):
        now = datetime(2026, 10, 25, 12, 0, 0, tzinfo=timezone.utc)
        course = self.db.create_course("Algorithms", "")

        # Less urgent card (due 1 day ago)
        c_mild = self.db.create_card(course.id, "Q1", "A1", due_at=now - timedelta(days=1))
        # More urgent card (due 6 days ago)
        c_urgent = self.db.create_card(course.id, "Q2", "A2", due_at=now - timedelta(days=6))
        # Future card (not due)
        self.db.create_card(course.id, "Q3", "A3", due_at=now + timedelta(days=3))

        due_cards = self.db.get_due_cards(course_id=course.id, now=now)
        self.assertEqual(len(due_cards), 2)
        self.assertEqual(due_cards[0].id, c_urgent.id)
        self.assertEqual(due_cards[1].id, c_mild.id)

        # Record a 'Good' review on the urgent card
        reviewed = self.db.record_review(c_urgent.id, grade=3, time_taken_ms=1450, now=now)
        self.assertEqual(reviewed.box, 2)
        self.assertEqual(reviewed.reps, 1)
        self.assertGreater(reviewed.due_at, now)


if __name__ == "__main__":
    unittest.main()
