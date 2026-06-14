import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import study_planner


def test_add_task_and_schedule(tmp_path):
    tasks_file = tmp_path / "tasks.json"

    tasks = study_planner.load_tasks(str(tasks_file))
    assert tasks == []

    task = study_planner.add_task("Math", "2026-06-20", 2, str(tasks_file))
    assert task["title"] == "Math"
    assert task["deadline"] == "2026-06-20"
    assert task["priority"] == 2

    tasks = study_planner.load_tasks(str(tasks_file))
    assert len(tasks) == 1

    schedule = study_planner.suggest_daily_schedule(tasks)
    assert schedule[0]["title"] == "Math"


def test_cli_add_command(tmp_path):
    tasks_file = tmp_path / "tasks.json"

    exit_code = study_planner.main([
        "add",
        "History",
        "2026-06-18",
        "1",
        "--tasks-file",
        str(tasks_file),
    ])

    assert exit_code == 0
    tasks = study_planner.load_tasks(str(tasks_file))
    assert any(task["title"] == "History" for task in tasks)


def test_calculate_daily_hours_uses_deadline_and_priority():
    task = {"title": "Biology", "deadline": "2026-06-20", "priority": 3}

    result = study_planner.calculate_daily_study_hours(task)

    assert result["title"] == "Biology"
    assert result["daily_hours"] > 0
    assert result["estimated_total_hours"] >= 3
