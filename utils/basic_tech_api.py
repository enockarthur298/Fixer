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
BASIC_TECH_TABLE_ID = 'user_context'  # Table name for storing user context

class BasicTechAPI:
    """Class to handle Basic Tech API interactions for user context storage and retrieval."""
    
    def __init__(self, api_key: str = BASIC_TECH_API_KEY, project_id: str = BASIC_TECH_PROJECT_ID):
        self.api_key = api_key
        self.project_id = project_id
        self.table_id = BASIC_TECH_TABLE_ID
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
        except requests.exceptions.HTTPError as e:
            if response.status_code == 500:
                log.error(f"Basic Tech API server error (500) - Table '{self.table_id}' may not exist in project")
                log.info("Please create the 'user_context' table in your Basic Tech project at https://app.basic.tech")
            elif response.status_code == 404:
                log.error(f"Basic Tech API not found (404) - Check project ID and table name")
            else:
                log.error(f"HTTP error making request to Basic Tech API: {e}")
            return None
        except requests.exceptions.RequestException as e:
            log.error(f"Error making request to Basic Tech API: {e}")
            return None
    
    def get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user context from Basic Tech datastore."""
        if not self.api_key or not self.project_id:
            return None
        
        # Get all items from user's context table
        endpoint = f"project/{self.project_id}/user/{user_id}/db/{self.table_id}"
        result = self._make_request('GET', endpoint)
        
        if result and 'data' in result and len(result['data']) > 0:
            # Return the most recent context data
            return result['data'][0].get('value', {})
        elif result is None:
            # API call failed, might be due to missing table or user data
            log.info(f"No user context found for user {user_id}. Table '{self.table_id}' may not exist.")
        
        return None
    
    def update_user_context(self, user_id: str, context_data: Dict[str, Any]) -> bool:
        """Update user context in Basic Tech datastore."""
        if not self.api_key or not self.project_id:
            return False
        
        # Create or update user context item
        endpoint = f"project/{self.project_id}/user/{user_id}/db/{self.table_id}"
        payload = {"value": context_data}
        
        result = self._make_request('POST', endpoint, payload)
        if result is None:
            log.warning(f"Failed to update user context. Table '{self.table_id}' may not exist in Basic Tech project.")
            return False
        
        return bool(result and 'data' in result)
    
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
