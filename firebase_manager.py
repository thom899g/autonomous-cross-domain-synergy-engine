"""
Firebase Firestore manager for state persistence, real-time updates, and cross-domain data storage.
Implements robust error handling, connection pooling, and automatic reconnection.
"""
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
import firebase_admin
from firebase_admin import credentials, firestore, exceptions
from firebase_admin.firestore import SERVER_TIMESTAMP

from config import config

class FirebaseManager:
    """Managed Firebase Firestore client with error recovery and state management"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._app = None
        self._client = None
        self._initialized = False
        self._initialize_firebase()
        
    def _initialize_firebase(self) -> None:
        """Initialize Firebase with exponential backoff retry logic"""
        for attempt in range(self.max_retries):
            try:
                if not firebase_admin._apps:
                    cred_dict = {
                        "type": "service_account",
                        "project_id": config.firebase.project_id,
                        "private_key_id": config.firebase.private_key_id,
                        "private_key": config.firebase.private_key,
                        "client_email": config.firebase.client_email,
                        "client_id": config.firebase.client_id,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_x509_cert_url": config.firebase.client_x509_cert_url
                    }
                    
                    cred = credentials.Certificate(cred_dict)
                    self._app = firebase_admin.initialize_app(cred)
                    logger.info(f"Firebase app initialized for project: {config.firebase.project_id}")
                
                self._client = firestore.client()
                # Test connection
                self._client.collection('system_health').document('connection_test').set({
                    'timestamp': SERVER_TIMESTAMP,
                    'status': 'connected'
                }, merge=True)
                
                self._initialized = True
                logger.success("Firebase initialization successful")
                return
                
            except exceptions.FirebaseError as e:
                logger.error(f"Firebase initialization attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.critical("All Firebase initialization attempts failed")
                    raise ConnectionError(f"Cannot connect to Firebase: {str