"""
Basic Tech API Utility for Fixer AI

This module handles interactions with Basic Tech API for storing and accessing user context
to enhance personalization of responses and repair suggestions.
"""

import os
import requests
import json
from typing import Dict, Any, Optional

from utils import logger

# Initialize logger
log = logger.get_logger(__name__)

# Basic Tech API configuration
# These should be set in environment variables or a secure config file
BASIC_TECH_API_KEY = os.environ.get('BASIC_TECH_API_KEY', '')
BASIC_TECH_PROJECT_ID = os.environ.get('BASIC_TECH_PROJECT_ID', '')
BASIC_TECH_API_BASE_URL = 'https://api.basic.tech'

class BasicTechAPI:
    """Class to handle Basic Tech API interactions for user context storage and retrieval."""
    
    def __init__(self, api_key: str = BASIC_TECH_API_KEY, project_id: str = BASIC_TECH_PROJECT_ID):
        self.api_key = api_key
        self.project_id = project_id
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        if not self.api_key or not self.project_id:
            log.warning("Basic Tech API key or Project ID not set. User context storage will not function.")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make a request to Basic Tech API."""
        url = f"{BASIC_TECH_API_BASE_URL}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log.error(f"Error making request to Basic Tech API: {e}")
            return None
    
    def get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user context from Basic Tech datastore."""
        if not self.api_key or not self.project_id:
            return None
        endpoint = f"project/{self.project_id}/user/{user_id}/data"
        result = self._make_request('GET', endpoint)
        if result and 'data' in result:
            return result['data']
        return None
    
    def update_user_context(self, user_id: str, context_data: Dict[str, Any]) -> bool:
        """Update user context in Basic Tech datastore."""
        if not self.api_key or not self.project_id:
            return False
        endpoint = f"project/{self.project_id}/user/{user_id}/data"
        result = self._make_request('POST', endpoint, {'data': context_data})
        return bool(result and 'success' in result and result['success'])
    
    def add_interaction_to_context(self, user_id: str, interaction: Dict[str, Any]) -> bool:
        """Add a specific interaction to user context."""
        if not self.api_key or not self.project_id:
            return False
        current_context = self.get_user_context(user_id) or {}
        if 'interactions' not in current_context:
            current_context['interactions'] = []
        current_context['interactions'].append(interaction)
        # Limit to last 10 interactions to prevent unlimited growth
        current_context['interactions'] = current_context['interactions'][-10:]
        return self.update_user_context(user_id, current_context)

# Initialize the API client
basic_tech_client = BasicTechAPI()
