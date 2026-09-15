"""Tests for the independent NEET Scoring Engine."""

import pytest
from app.services.scoring_service import ScoringService


def test_ten_correct_answers():
    """10 correct questions must yield 40 marks."""
    res = ScoringService.calculate_score(correct_count=10, wrong_count=0, unattempted_count=0)
    assert res.total_questions == 10
    assert res.correct_marks_total == 40.0
    assert res.wrong_marks_total == 0.0
    assert res.unattempted_marks_total == 0.0
    assert res.score == 40.0
    assert res.max_score == 40.0
    assert res.percentage == 100.0


def test_eight_correct_two_wrong():
    """8 correct + 2 wrong must yield 30 marks (32 - 2 = 30)."""
    res = ScoringService.calculate_score(correct_count=8, wrong_count=2, unattempted_count=0)
    assert res.total_questions == 10
    assert res.correct_marks_total == 32.0
    assert res.wrong_marks_total == -2.0
    assert res.score == 30.0
    assert res.max_score == 40.0
    assert res.percentage == 75.0


def test_eight_correct_two_unattempted():
    """8 correct + 2 unattempted must yield 32 marks (32 + 0 = 32)."""
    res = ScoringService.calculate_score(correct_count=8, wrong_count=0, unattempted_count=2)
    assert res.total_questions == 10
    assert res.correct_marks_total == 32.0
    assert res.wrong_marks_total == 0.0
    assert res.score == 32.0
    assert res.max_score == 40.0
    assert res.percentage == 80.0


def test_zero_correct_ten_wrong():
    """0 correct + 10 wrong must yield -10 marks."""
    res = ScoringService.calculate_score(correct_count=0, wrong_count=10, unattempted_count=0)
    assert res.total_questions == 10
    assert res.correct_marks_total == 0.0
    assert res.wrong_marks_total == -10.0
    assert res.score == -10.0
    assert res.max_score == 40.0
    assert res.percentage == -25.0


def test_zero_correct_ten_unattempted():
    """0 correct + 10 unattempted must yield 0 marks."""
    res = ScoringService.calculate_score(correct_count=0, wrong_count=0, unattempted_count=10)
    assert res.total_questions == 10
    assert res.correct_marks_total == 0.0
    assert res.wrong_marks_total == 0.0
    assert res.score == 0.0
    assert res.max_score == 40.0
    assert res.percentage == 0.0


def test_neet_benchmark_example():
    """
    40 correct, 5 wrong, 5 unattempted:
    40 * 4 = 160
    5 * -1 = -5
    5 * 0 = 0
    Total score = 155 / 200 (77.5%)
    """
    res = ScoringService.calculate_score(correct_count=40, wrong_count=5, unattempted_count=5)
    assert res.total_questions == 50
    assert res.correct_marks_total == 160.0
    assert res.wrong_marks_total == -5.0
    assert res.unattempted_marks_total == 0.0
    assert res.score == 155.0
    assert res.max_score == 200.0
    assert res.percentage == 77.5


def test_custom_marking_scheme():
    """Support custom marking schemes (e.g. +2, -0.5, 0)."""
    res = ScoringService.calculate_score(
        correct_count=10,
        wrong_count=4,
        unattempted_count=6,
        correct_marks=2.0,
        wrong_marks=-0.5,
        unattempted_marks=0.0
    )
    assert res.total_questions == 20
    assert res.correct_marks_total == 20.0
    assert res.wrong_marks_total == -2.0
    assert res.score == 18.0
    assert res.max_score == 40.0
    assert res.percentage == 45.0


def test_evaluate_single_answer():
    """Individual answer evaluation for correct, incorrect, and timeout states."""
    assert ScoringService.evaluate_single_answer(is_correct=True, is_timeout=False) == 4.0
    assert ScoringService.evaluate_single_answer(is_correct=False, is_timeout=False) == -1.0
    assert ScoringService.evaluate_single_answer(is_correct=False, is_timeout=True) == 0.0
