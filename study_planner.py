#!/usr/bin/env python3
"""Smart Study Planner CLI.

This app lets you add study tasks with deadlines and view a simple
suggested daily study schedule based on the tasks you saved.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime

DEFAULT_TASKS_FILE = "tasks.json"


def load_tasks(tasks_file=DEFAULT_TASKS_FILE):
    """Load tasks from a JSON file. Return an empty list if the file is missing."""
    if not os.path.exists(tasks_file):
        return []

    with open(tasks_file, "r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError:
            return []

    return data if isinstance(data, list) else []


def save_tasks(tasks, tasks_file=DEFAULT_TASKS_FILE):
    """Save tasks to a JSON file."""
    directory = os.path.dirname(os.path.abspath(tasks_file))
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(tasks_file, "w", encoding="utf-8") as handle:
        json.dump(tasks, handle, indent=2)
        handle.write("\n")


def add_task(title, deadline, priority=1, tasks_file=DEFAULT_TASKS_FILE):
    """Add a study task and persist it to disk."""
    cleaned_title = (title or "").strip()
    if not cleaned_title:
        raise ValueError("Task title cannot be empty.")

    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Deadline must be in YYYY-MM-DD format.") from exc

    try:
        priority_value = int(priority)
    except (TypeError, ValueError) as exc:
        raise ValueError("Priority must be an integer.") from exc

    if priority_value < 1:
        raise ValueError("Priority must be at least 1.")

    tasks = load_tasks(tasks_file)
    task = {
        "title": cleaned_title,
        "deadline": deadline_date.isoformat(),
        "priority": priority_value,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    tasks.append(task)
    save_tasks(tasks, tasks_file)
    return task


def calculate_daily_study_hours(task):
    """Estimate how many hours a task should receive each day."""
    today = date.today()
    deadline_date = date.fromisoformat(task["deadline"])
    days_left = max(1, (deadline_date - today).days + 1)

    priority = max(1, int(task.get("priority", 1)))
    base_hours = priority * 0.5
    estimated_total_hours = max(priority, base_hours * days_left)
    daily_hours = estimated_total_hours / days_left

    return {
        "title": task["title"],
        "deadline": task["deadline"],
        "priority": priority,
        "days_left": days_left,
        "estimated_total_hours": estimated_total_hours,
        "daily_hours": round(daily_hours, 2),
    }


def suggest_daily_schedule(tasks):
    """Create a simple daily study schedule from the saved tasks."""
    today = date.today()
    ordered = sorted(tasks, key=lambda item: (item["deadline"], -int(item["priority"])))
    schedule = []

    for task in ordered:
        deadline_date = date.fromisoformat(task["deadline"])
        days_left = (deadline_date - today).days

        if days_left < 0:
            day_label = "Overdue"
            time_slot = "Start today"
        elif days_left == 0:
            day_label = "Today"
            time_slot = "Morning session"
        elif days_left == 1:
            day_label = "Tomorrow"
            time_slot = "Afternoon session"
        else:
            day_label = f"In {days_left} days"
            time_slot = "Evening session"

        study_hours = calculate_daily_study_hours(task)
        duration_hours = study_hours["daily_hours"]
        reasoning = (
            f"Priority {study_hours['priority']} and {study_hours['days_left']} day(s) left "
            f"give about {study_hours['daily_hours']} hour(s) per day; "
            f"estimated total workload is {study_hours['estimated_total_hours']} hour(s)."
        )
        schedule.append(
            {
                "title": task["title"],
                "deadline": task["deadline"],
                "priority": int(task["priority"]),
                "day_label": day_label,
                "time_slot": time_slot,
                "duration_hours": duration_hours,
                "reasoning": reasoning,
            }
        )

    return schedule


def build_parser():
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Smart Study Planner: manage study tasks and get a daily schedule."
    )
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Add a new study task")
    add_parser.add_argument("title", help="Name of the study task")
    add_parser.add_argument("deadline", help="Deadline in YYYY-MM-DD format")
    add_parser.add_argument("priority", nargs="?", type=int, default=1,
                            help="Priority level (default: 1)")
    add_parser.add_argument("--tasks-file", default=DEFAULT_TASKS_FILE,
                            help="Path to the task database JSON file")

    schedule_parser = subparsers.add_parser("schedule", help="Show a suggested schedule")
    schedule_parser.add_argument("--tasks-file", default=DEFAULT_TASKS_FILE,
                                 help="Path to the task database JSON file")

    return parser


def main(argv=None):
    """Run the CLI app."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "add":
        try:
            task = add_task(args.title, args.deadline, args.priority, args.tasks_file)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        print(
            f"Added task: {task['title']} (deadline: {task['deadline']}, "
            f"priority: {task['priority']})"
        )
        return 0

    if args.command == "schedule":
        tasks = load_tasks(args.tasks_file)
        if not tasks:
            print("No study tasks found. Add one with 'python study_planner.py add <title> <YYYY-MM-DD> [priority]'.")
            return 0

        schedule = suggest_daily_schedule(tasks)
        print("Suggested daily schedule:")
        for entry in schedule:
            print(
                f"- {entry['day_label']}: {entry['title']} | "
                f"{entry['time_slot']} for {entry['duration_hours']} hour(s)"
            )
            print(f"  Why: {entry['reasoning']}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
