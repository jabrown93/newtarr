#!/usr/bin/env python3
"""
Stateful Management API Routes
Handles API endpoints for stateful management
"""

from flask import Blueprint, jsonify, request
from src.primary.stateful_manager import (
    get_stateful_management_info,
    reset_stateful_management,
    update_lock_expiration
)
from src.primary.utils.logger import get_logger

# Create logger
stateful_logger = get_logger("stateful")

# Create blueprint
stateful_api = Blueprint('stateful_api', __name__)

@stateful_api.route('/info', methods=['GET'])
def get_info():
    """Get stateful management information."""
    try:
        info = get_stateful_management_info()
        return jsonify({
            "success": True,
            "created_at_ts": info.get("created_at_ts"),
            "expires_at_ts": info.get("expires_at_ts"),
            "interval_hours": info.get("interval_hours")
        })
    except Exception as e:
        stateful_logger.error(f"Error getting stateful info: {e}")
        return jsonify({"success": False, "message": f"Error getting stateful info: {str(e)}"}), 500

@stateful_api.route('/reset', methods=['POST'])
def reset_stateful():
    """Reset the stateful management system."""
    try:
        success = reset_stateful_management()
        if success:
            return jsonify({"success": True, "message": "Stateful management reset successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to reset stateful management"}), 500
    except Exception as e:
        stateful_logger.error(f"Error resetting stateful management: {e}")
        return jsonify({"error": str(e)}), 500

@stateful_api.route('/update-expiration', methods=['POST'])
def update_expiration():
    """Update the stateful management expiration time."""
    try:
        hours = request.json.get('hours')
        if hours is None or not isinstance(hours, int) or hours <= 0:
            stateful_logger.error(f"Invalid hours value for update-expiration: {hours}")
            return jsonify({"success": False, "message": f"Invalid hours value: {hours}. Must be a positive integer."}), 400

        updated = update_lock_expiration(hours)
        if updated:
            info = get_stateful_management_info()
            return jsonify({
                "success": True,
                "message": f"Expiration updated to {hours} hours",
                "expires_at": info.get("expires_at"),
                "expires_date": info.get("expires_date")
            })
        else:
            return jsonify({"success": False, "message": "Failed to update expiration"}), 500
    except Exception as e:
        stateful_logger.error(f"Error updating expiration: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Error updating expiration: {str(e)}"}), 500
