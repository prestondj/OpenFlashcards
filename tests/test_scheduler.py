import unittest
from datetime import datetime, timezone, timedelta

from core.scheduler import SpacedRepetitionEngine


class TestSpacedRepetitionEngine(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 25, 12, 0, 0, tzinfo=timezone.utc)

    def test_again_grade_resets_to_box_one(self):
        res = SpacedRepetitionEngine.process_review(
            grade=1,
            current_box=4,
            reps=5,
            interval_days=15.0,
            ease_factor=2.5,
            stability=15.0,
            last_reviewed_at=self.now - timedelta(days=15),
            now=self.now,
        )
        self.assertEqual(res.new_box, 1)
        self.assertEqual(res.new_reps, 0)
        self.assertAlmostEqual(res.new_interval_days, 0.1)
        self.assertAlmostEqual(res.new_ease_factor, 2.3)

    def test_good_grade_progression(self):
        # First review (reps=0 -> interval=1.0)
        r1 = SpacedRepetitionEngine.process_review(
            grade=3, current_box=1, reps=0, interval_days=0.0, ease_factor=2.5, now=self.now
        )
        self.assertEqual(r1.new_box, 2)
        self.assertEqual(r1.new_reps, 1)
        self.assertAlmostEqual(r1.new_interval_days, 1.0)

        # Second review (reps=1 -> interval=3.0)
        r2 = SpacedRepetitionEngine.process_review(
            grade=3,
            current_box=r1.new_box,
            reps=r1.new_reps,
            interval_days=r1.new_interval_days,
            ease_factor=r1.new_ease_factor,
            now=self.now + timedelta(days=1),
        )
        self.assertEqual(r2.new_box, 3)
        self.assertEqual(r2.new_reps, 2)
        self.assertAlmostEqual(r2.new_interval_days, 3.0)

        # Third review (reps=2 -> interval = 3.0 * 2.5 = 7.5)
        r3 = SpacedRepetitionEngine.process_review(
            grade=3,
            current_box=r2.new_box,
            reps=r2.new_reps,
            interval_days=r2.new_interval_days,
            ease_factor=r2.new_ease_factor,
            now=self.now + timedelta(days=4),
        )
        self.assertEqual(r3.new_box, 4)
        self.assertEqual(r3.new_reps, 3)
        self.assertAlmostEqual(r3.new_interval_days, 7.5)

    def test_retention_forgetting_curve_decay(self):
        # At t = S, retention should equal 1/e (~0.367879)
        last_rev = self.now - timedelta(days=5)
        ret = SpacedRepetitionEngine.calculate_retention(last_rev, stability=5.0, now=self.now)
        self.assertAlmostEqual(ret, 0.367879, places=4)

    def test_overdue_score_ranking(self):
        # Card A overdue by 4 days on a 2-day interval -> score 2.0
        # Card B overdue by 2 days on a 4-day interval -> score 0.5
        score_a = SpacedRepetitionEngine.calculate_overdue_score(
            due_at=self.now - timedelta(days=4), interval_days=2.0, now=self.now
        )
        score_b = SpacedRepetitionEngine.calculate_overdue_score(
            due_at=self.now - timedelta(days=2), interval_days=4.0, now=self.now
        )
        self.assertGreater(score_a, score_b)
        self.assertAlmostEqual(score_a, 2.0)
        self.assertAlmostEqual(score_b, 0.5)


if __name__ == "__main__":
    unittest.main()
