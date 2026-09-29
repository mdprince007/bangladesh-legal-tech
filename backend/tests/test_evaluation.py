import pytest
from app.core.database import SessionLocal
from app.services.evaluation_service import evaluation_service

def test_evaluation_benchmark_suite():
    db = SessionLocal()
    try:
        report = evaluation_service.run_suite(db)
        assert report.total_cases >= 4
        assert report.passed_cases == report.total_cases
        assert report.overall_accuracy_percentage == 100.0
        for item in report.results:
            assert item.passed is True
            assert item.score == 100.0
    finally:
        db.close()
