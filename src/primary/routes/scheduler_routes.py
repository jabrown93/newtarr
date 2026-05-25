#!/usr/bin/env python3
"""
Scheduler API Routes
Handles API endpoints for scheduler management
"""

import os
import json
import logging
from flask import Blueprint, jsonify, request
from datetime import datetime

# Import the scheduler engine to get execution history
from src.primary.scheduler_engine import (
    get_execution_history,
    is_valid_schedule_app_value,
)

# Create logger
scheduler_logger = logging.getLogger("scheduler")

# Create blueprint
scheduler_api = Blueprint('scheduler_api', __name__)

# Configuration file path
CONFIG_DIR = "/config/scheduler"
SCHEDULE_FILE = os.path.join(CONFIG_DIR, "schedule.json")

def ensure_config_dir():
    """Ensure the config directory exists"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        scheduler_logger.info(f"Created config directory: {CONFIG_DIR}")

@scheduler_api.route('/api/scheduler/load', methods=['GET'])
def load_schedules():
    """Load schedules from the JSON file"""
    try:
        ensure_config_dir()

        # Default empty schedules
        schedules = {
            "global": [],
            "sonarr": [],
            "radarr": [],
            "lidarr": [],
            "readarr": []
        }

        # Load from file if it exists
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, 'r') as f:
                loaded_data = json.load(f)
                if loaded_data and isinstance(loaded_data, dict):
                    schedules.update(loaded_data)
            scheduler_logger.info(f"Loaded schedules from {SCHEDULE_FILE}")
        else:
            scheduler_logger.info(f"No schedule file found at {SCHEDULE_FILE}, returning empty schedules")

        return jsonify(schedules)

    except Exception as e:
        error_msg = f"Error loading schedules: {str(e)}"
        scheduler_logger.error(error_msg)
        return jsonify({"error": error_msg}), 500


@scheduler_api.route('/api/scheduler/history', methods=['GET'])
def get_scheduler_history():
    """Get the execution history of the scheduler"""
    try:
        history = get_execution_history()

        return jsonify({
            "success": True,
            "history": history,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        error_msg = f"Error getting scheduler history: {str(e)}"
        scheduler_logger.error(error_msg)
        return jsonify({"error": error_msg}), 500

@scheduler_api.route('/api/scheduler/save', methods=['POST'])
def save_schedules():
    """Save schedules to the JSON file"""
    try:
        ensure_config_dir()

        # Get schedule data from request
        schedules = request.json

        if not schedules or not isinstance(schedules, dict):
            return jsonify({"error": "Invalid schedule data format"}), 400

        # Validate every entry's "app" field is a syntactically safe identifier
        # before persisting. The scheduler engine interpolates this value into a
        # /config/{app}.json path; rejecting anything containing path separators
        # or parent-directory tokens keeps traversal payloads off disk. The
        # validator is intentionally permissive about the *set* of identifiers
        # (it accepts UI-emitted composite values like "sonarr-all") — the
        # executor's strict allowlist is what actually gates file access.
        for group_key, entries in schedules.items():
            if not isinstance(entries, list):
                return jsonify({"error": f"Invalid entries for {group_key!r}"}), 400
            for entry in entries:
                if not isinstance(entry, dict):
                    return jsonify({"error": f"Invalid schedule entry in {group_key!r}"}), 400
                app_value = entry.get("app")
                if app_value is None:
                    return (
                        jsonify({"error": f"Schedule entry in {group_key!r} is missing 'app'"}),
                        400,
                    )
                if not is_valid_schedule_app_value(app_value):
                    return (
                        jsonify({"error": f"Invalid app value in schedule entry: {app_value!r}"}),
                        400,
                    )

        # Save to file
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedules, f, indent=2)

        scheduler_logger.info(f"Saved schedules to {SCHEDULE_FILE}")

        return jsonify({
            "success": True,
            "message": "Schedules saved successfully",
            "timestamp": datetime.now().isoformat(),
            "file": SCHEDULE_FILE
        })

    except Exception as e:
        error_msg = f"Error saving schedules: {str(e)}"
        scheduler_logger.error(error_msg)
        return jsonify({"error": error_msg}), 500
