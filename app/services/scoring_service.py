"""Independent NEET Scoring Engine."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ScoreResult:
    total_questions: int
    correct_count: int
    wrong_count: int
    unattempted_count: int
    correct_marks: float
    wrong_marks: float
    unattempted_marks: float
    correct_marks_total: float
    wrong_marks_total: float
    unattempted_marks_total: float
    score: float
    max_score: float
    percentage: float


class ScoringService:
    """
    Independent NEET-style scoring calculation engine.
    Never relies on Telegram's client-side quiz result counters.
    """

    @staticmethod
    def calculate_score(
        correct_count: int,
        wrong_count: int,
        unattempted_count: int,
        correct_marks: float = 4.0,
        wrong_marks: float = -1.0,
        unattempted_marks: float = 0.0
    ) -> ScoreResult:
        """
        Calculate total score and breakdown.

        Default NEET scheme:
        Correct = +4
        Wrong = -1
        Unattempted = 0
        """
        total_questions = correct_count + wrong_count + unattempted_count
        correct_marks_total = correct_count * correct_marks
        wrong_marks_total = wrong_count * wrong_marks
        unattempted_marks_total = unattempted_count * unattempted_marks

        total_score = correct_marks_total + wrong_marks_total + unattempted_marks_total
        max_score = total_questions * correct_marks

        if max_score > 0:
            percentage = round((total_score / max_score) * 100, 2)
        else:
            percentage = 0.0

        return ScoreResult(
            total_questions=total_questions,
            correct_count=correct_count,
            wrong_count=wrong_count,
            unattempted_count=unattempted_count,
            correct_marks=correct_marks,
            wrong_marks=wrong_marks,
            unattempted_marks=unattempted_marks,
            correct_marks_total=round(correct_marks_total, 2),
            wrong_marks_total=round(wrong_marks_total, 2),
            unattempted_marks_total=round(unattempted_marks_total, 2),
            score=round(total_score, 2),
            max_score=round(max_score, 2),
            percentage=percentage
        )

    @staticmethod
    def evaluate_single_answer(
        is_correct: bool,
        is_timeout: bool = False,
        correct_marks: float = 4.0,
        wrong_marks: float = -1.0,
        unattempted_marks: float = 0.0
    ) -> float:
        """Award marks for an individual question answer."""
        if is_timeout:
            return float(unattempted_marks)
        if is_correct:
            return float(correct_marks)
        return float(wrong_marks)
