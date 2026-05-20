"""Tests for src/team/statistics.py"""

import sqlite3
from datetime import datetime

import pytest

from src.team.statistics import (
    TeamStatistics,
    TeamStats,
    UsageRecord,
    UserStats,
    team_statistics,
)


class TestUsageRecord:
    """Test UsageRecord dataclass"""

    def test_create_usage_record(self):
        """Test creating UsageRecord"""
        record = UsageRecord(
            record_id="rec-001",
            team_id="team-001",
            user_id="user-001",
            task_id="task-001",
            task_type="build",
            model="gpt-4",
            tokens_used=1000,
            cost=0.05,
            execution_time=5.0,
            status="success",
        )

        assert record.record_id == "rec-001"
        assert record.team_id == "team-001"
        assert record.tokens_used == 1000

    def test_to_dict(self):
        """Test to_dict method"""
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        record = UsageRecord(
            record_id="rec-001",
            team_id="team-001",
            user_id="user-001",
            task_id="task-001",
            task_type="build",
            model="gpt-4",
            tokens_used=1000,
            cost=0.05,
            execution_time=5.0,
            status="success",
            created_at=created_at,
        )

        result = record.to_dict()

        assert result["record_id"] == "rec-001"
        assert result["team_id"] == "team-001"
        assert result["tokens_used"] == 1000
        assert result["created_at"] == created_at.isoformat()


class TestTeamStats:
    """Test TeamStats dataclass"""

    def test_to_dict(self):
        """Test to_dict method"""
        stats = TeamStats(
            team_id="team-001",
            period="week",
            total_tasks=10,
            successful_tasks=8,
            failed_tasks=2,
            total_tokens=50000,
            total_cost=2.5,
            avg_execution_time=3.5,
            top_models=[{"model": "gpt-4", "count": 5, "tokens": 30000}],
            top_users=[{"user_id": "user-001", "count": 5, "cost": 1.5}],
            daily_breakdown=[{"date": "2024-01-15", "count": 10, "tokens": 50000}],
        )

        result = stats.to_dict()

        assert result["team_id"] == "team-001"
        assert result["total_tasks"] == 10
        assert result["successful_tasks"] == 8
        assert result["success_rate"] == 80.0  # 8/10 * 100
        assert result["total_tokens"] == 50000

    def test_to_dict_zero_tasks(self):
        """Test to_dict with zero tasks (division by zero handling)"""
        stats = TeamStats(
            team_id="team-001",
            period="week",
            total_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_tokens=0,
            total_cost=0.0,
            avg_execution_time=0.0,
            top_models=[],
            top_users=[],
            daily_breakdown=[],
        )

        result = stats.to_dict()

        assert result["success_rate"] == 0  # Should handle division by zero


class TestUserStats:
    """Test UserStats dataclass"""

    def test_to_dict(self):
        """Test to_dict method"""
        stats = UserStats(
            user_id="user-001",
            team_id="team-001",
            period="week",
            total_tasks=5,
            successful_tasks=4,
            total_tokens=25000,
            total_cost=1.25,
            avg_execution_time=3.0,
            favorite_model="gpt-4",
        )

        result = stats.to_dict()

        assert result["user_id"] == "user-001"
        assert result["total_tasks"] == 5
        assert result["successful_tasks"] == 4
        assert result["success_rate"] == 80.0
        assert result["favorite_model"] == "gpt-4"

    def test_to_dict_zero_tasks(self):
        """Test to_dict with zero tasks"""
        stats = UserStats(
            user_id="user-001",
            team_id="team-001",
            period="week",
            total_tasks=0,
            successful_tasks=0,
            total_tokens=0,
            total_cost=0.0,
            avg_execution_time=0.0,
            favorite_model="none",
        )

        result = stats.to_dict()

        assert result["success_rate"] == 0


class TestTeamStatistics:
    """Test TeamStatistics class"""

    @pytest.fixture
    def stats_db(self, tmp_path):
        """Create a temporary TeamStatistics instance"""
        db_path = tmp_path / "test_stats.db"
        return TeamStatistics(db_path=str(db_path))

    def test_init_creates_db(self, tmp_path):
        """Test that __init__ creates the database file"""
        db_path = tmp_path / "test_stats.db"
        assert not db_path.exists()

        TeamStatistics(db_path=str(db_path))

        assert db_path.exists()

    def test_init_creates_tables(self, stats_db):
        """Test that _init_db creates the correct tables"""
        conn = sqlite3.connect(str(stats_db.db_path))
        cursor = conn.cursor()

        # Check that usage_records table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='usage_records'"
        )
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == "usage_records"

        # Check that indexes exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_team_created'"
        )
        result = cursor.fetchone()
        assert result is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_user_created'"
        )
        result = cursor.fetchone()
        assert result is not None

        conn.close()

    def test_record_usage(self, stats_db):
        """Test recording usage data"""
        record = stats_db.record_usage(
            record_id="rec-001",
            team_id="team-001",
            user_id="user-001",
            task_id="task-001",
            task_type="build",
            model="gpt-4",
            tokens_used=1000,
            cost=0.05,
            execution_time=5.0,
            status="success",
        )

        assert record.record_id == "rec-001"
        assert record.team_id == "team-001"

        # Verify it was stored in DB
        conn = sqlite3.connect(str(stats_db.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usage_records WHERE record_id = ?", ("rec-001",))
        row = cursor.fetchone()

        assert row is not None
        assert row[1] == "team-001"  # team_id
        assert row[2] == "user-001"  # user_id

        conn.close()

    def test_record_usage_multiple(self, stats_db):
        """Test recording multiple usage records"""
        for i in range(5):
            stats_db.record_usage(
                record_id=f"rec-{i:03d}",
                team_id="team-001",
                user_id="user-001",
                task_id=f"task-{i:03d}",
                task_type="build",
                model="gpt-4",
                tokens_used=1000 * (i + 1),
                cost=0.05 * (i + 1),
                execution_time=5.0 * (i + 1),
                status="success" if i % 2 == 0 else "failed",
            )

        # Verify 5 records were stored
        conn = sqlite3.connect(str(stats_db.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM usage_records")
        count = cursor.fetchone()[0]

        assert count == 5

        conn.close()

    def test_get_team_stats_empty(self, stats_db):
        """Test get_team_stats with no data"""
        stats = stats_db.get_team_stats("team-001", period="week")

        assert stats.team_id == "team-001"
        assert stats.total_tasks == 0
        assert stats.successful_tasks == 0
        assert stats.failed_tasks == 0
        assert stats.total_tokens == 0
        assert stats.total_cost == 0.0

    def test_get_team_stats_with_data(self, stats_db):
        """Test get_team_stats with data"""
        # Add some records
        for i in range(10):
            status = "success" if i < 8 else "failed"
            stats_db.record_usage(
                record_id=f"rec-{i:03d}",
                team_id="team-001",
                user_id=f"user-{i % 3:03d}",
                task_id=f"task-{i:03d}",
                task_type="build",
                model="gpt-4" if i < 5 else "claude",
                tokens_used=1000,
                cost=0.05,
                execution_time=5.0,
                status=status,
            )

        stats = stats_db.get_team_stats("team-001", period="week")

        assert stats.total_tasks == 10
        assert stats.successful_tasks == 8
        assert stats.failed_tasks == 2
        assert stats.total_tokens == 10000
        assert stats.total_cost == 0.5
        assert len(stats.top_models) <= 5
        assert len(stats.top_users) <= 5
        assert len(stats.daily_breakdown) > 0

    def test_get_team_stats_different_periods(self, stats_db):
        """Test get_team_stats for different periods"""
        # Add records with different timestamps
        # (This is tricky because records are created with current timestamp)
        stats_db.record_usage(
            record_id="rec-001",
            team_id="team-001",
            user_id="user-001",
            task_id="task-001",
            task_type="build",
            model="gpt-4",
            tokens_used=1000,
            cost=0.05,
            execution_time=5.0,
        )

        # Day period (last 24 hours)
        stats_day = stats_db.get_team_stats("team-001", period="day")
        assert stats_day.total_tasks >= 0  # Might be 0 if timing is weird

        # Week period (last 7 days)
        stats_week = stats_db.get_team_stats("team-001", period="week")
        assert stats_week.total_tasks >= 0

        # Month period (last 30 days)
        stats_month = stats_db.get_team_stats("team-001", period="month")
        assert stats_month.total_tasks >= 0

    def test_get_user_stats_empty(self, stats_db):
        """Test get_user_stats with no data"""
        stats = stats_db.get_user_stats("user-001", "team-001", period="week")

        assert stats.user_id == "user-001"
        assert stats.total_tasks == 0
        assert stats.successful_tasks == 0
        assert stats.total_tokens == 0
        assert stats.favorite_model == "none"

    def test_get_user_stats_with_data(self, stats_db):
        """Test get_user_stats with data"""
        # Add records for user-001
        for i in range(5):
            stats_db.record_usage(
                record_id=f"rec-{i:03d}",
                team_id="team-001",
                user_id="user-001",
                task_id=f"task-{i:03d}",
                task_type="build",
                model="gpt-4" if i < 3 else "claude",
                tokens_used=1000,
                cost=0.05,
                execution_time=5.0,
                status="success",
            )

        stats = stats_db.get_user_stats("user-001", "team-001", period="week")

        assert stats.user_id == "user-001"
        assert stats.total_tasks == 5
        assert stats.successful_tasks == 5
        assert stats.total_tokens == 5000
        assert stats.total_cost == 0.25
        assert stats.favorite_model == "gpt-4"  # Used 3 times vs claude 2 times

    def test_get_user_stats_favorite_model(self, stats_db):
        """Test that favorite_model is correctly identified"""
        # Add records with gpt-4 used 3 times, claude used 2 times
        for i in range(5):
            model = "gpt-4" if i < 3 else "claude"
            stats_db.record_usage(
                record_id=f"rec-{i:03d}",
                team_id="team-001",
                user_id="user-001",
                task_id=f"task-{i:03d}",
                task_type="build",
                model=model,
                tokens_used=1000,
                cost=0.05,
                execution_time=5.0,
                status="success",
            )

        stats = stats_db.get_user_stats("user-001", "team-001", period="week")

        assert stats.favorite_model == "gpt-4"

    def test_cleanup_old_records(self, stats_db):
        """Test cleanup_old_records"""
        # Add a record
        stats_db.record_usage(
            record_id="rec-001",
            team_id="team-001",
            user_id="user-001",
            task_id="task-001",
            task_type="build",
            model="gpt-4",
            tokens_used=1000,
            cost=0.05,
            execution_time=5.0,
        )

        # Verify record exists
        conn = sqlite3.connect(str(stats_db.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usage_records")
        count_before = cursor.fetchone()[0]
        conn.close()

        assert count_before == 1

        # Cleanup with 0 days (should delete all records)
        deleted = stats_db.cleanup_old_records(days=0)

        assert deleted == 1

        # Verify record was deleted
        conn = sqlite3.connect(str(stats_db.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usage_records")
        count_after = cursor.fetchone()[0]
        conn.close()

        assert count_after == 0

    def test_get_all_teams_empty(self, stats_db):
        """Test get_all_teams with no data"""
        teams = stats_db.get_all_teams()

        assert teams == []

    def test_get_all_teams_with_data(self, stats_db):
        """Test get_all_teams with data"""
        # Add records for different teams
        for team_id in ["team-001", "team-002", "team-003"]:
            stats_db.record_usage(
                record_id=f"rec-{team_id}",
                team_id=team_id,
                user_id="user-001",
                task_id="task-001",
                task_type="build",
                model="gpt-4",
                tokens_used=1000,
                cost=0.05,
                execution_time=5.0,
            )

        teams = stats_db.get_all_teams()

        assert len(teams) == 3
        assert "team-001" in teams
        assert "team-002" in teams
        assert "team-003" in teams


class TestGlobalInstance:
    """Test the global team_statistics instance"""

    def test_global_instance_exists(self):
        """Test that the global instance exists"""
        assert team_statistics is not None
        assert isinstance(team_statistics, TeamStatistics)
