#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import keys_manager
from src.primary.state import get_state_file_path, reset_state_file
from src.primary.utils.logger import get_logger
from src.primary.utils.url_validation import validate_url, make_validated_request
from src.primary.settings_manager import get_ssl_verify_setting
import traceback
from urllib.parse import urlparse

radarr_bp = Blueprint('radarr', __name__)
radarr_logger = get_logger("radarr")

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("radarr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("radarr", "processed_upgrades")

@radarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Radarr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    api_timeout = data.get('api_timeout', 30)  # Use longer timeout for connection test
    
    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400
        
    radarr_logger.info(f"Testing connection to Radarr API at {api_url}")
    
    # Validate URL format
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        error_msg = "API URL must start with http:// or https://"
        radarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 400

    # SSRF protection
    url_valid, url_error, resolved_ip = validate_url(api_url)
    if not url_valid:
        return jsonify({"success": False, "message": url_error}), 400

    # For Radarr, use api/v3
    url = f"{api_url.rstrip('/')}/api/v3/system/status"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Get SSL verification setting
    verify_ssl = get_ssl_verify_setting()
    
    if not verify_ssl:
        radarr_logger.debug("SSL verification disabled by user setting for connection test")
    
    try:
        response = make_validated_request(url, resolved_ip, headers=headers, timeout=(10, api_timeout), verify=verify_ssl)
        
        # For HTTP errors, provide more specific feedback
        if response.status_code == 401:
            error_msg = "Authentication failed: Invalid API key"
            radarr_logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), 401
        elif response.status_code == 403:
            error_msg = "Access forbidden: Check API key permissions"
            radarr_logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), 403
        elif response.status_code == 404:
            error_msg = "API endpoint not found: This doesn't appear to be a valid Radarr server. Check your URL."
            radarr_logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), 404
        elif response.status_code >= 500:
            error_msg = f"Radarr server error (HTTP {response.status_code}): The Radarr server is experiencing issues"
            radarr_logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), response.status_code
            
        # Raise for other HTTP errors
        response.raise_for_status()
        
        try:
            response_data = response.json()
            version = response_data.get('version', 'unknown')
            radarr_logger.info(f"Successfully connected to Radarr API version: {version}")
            
            return jsonify({
                "success": True,
                "message": "Successfully connected to Radarr API",
                "version": version
            })
        except ValueError:
            error_msg = "Invalid JSON response from Radarr API - This doesn't appear to be a valid Radarr server"
            radarr_logger.error(f"{error_msg}. Response content: {response.text[:200]}")
            return jsonify({"success": False, "message": error_msg}), 500
            
    except requests.exceptions.ConnectionError as e:
        # Handle different types of connection errors
        error_details = str(e)
        if "Connection refused" in error_details:
            error_msg = f"Connection refused - Radarr is not running on {api_url} or the port is incorrect"
        elif "Name or service not known" in error_details or "getaddrinfo failed" in error_details:
            error_msg = f"DNS resolution failed - Cannot find host '{urlparse(api_url).hostname}'. Check your URL."
        else:
            error_msg = f"Connection error - Check if Radarr is running: {error_details}"
            
        radarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 404
    except requests.exceptions.Timeout:
        error_msg = f"Connection timed out - Radarr took too long to respond"
        radarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 504
    except requests.exceptions.RequestException as e:
        error_msg = f"Connection test failed: {str(e)}"
        radarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500
