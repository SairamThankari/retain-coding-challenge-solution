import time
import threading
from datetime import datetime
from typing import Dict, Optional

class URLStore:
    """In-memory storage for URL mappings and analytics"""
    
    def __init__(self):
        self._urls: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def create_url_mapping(self, short_code: str, original_url: str) -> Dict:
        """Create a new URL mapping"""
        with self._lock:
            if short_code in self._urls:
                raise ValueError(f"Short code '{short_code}' already exists")
            
            url_data = {
                'original_url': original_url,
                'short_code': short_code,
                'clicks': 0,
                'created_at': datetime.now().isoformat()
            }
            
            self._urls[short_code] = url_data
            return url_data.copy()
    
    def get_url_mapping(self, short_code: str) -> Optional[Dict]:
        """Get URL mapping by short code"""
        with self._lock:
            return self._urls.get(short_code)
    
    def increment_clicks(self, short_code: str) -> bool:
        """Increment click count for a URL"""
        with self._lock:
            if short_code in self._urls:
                self._urls[short_code]['clicks'] += 1
                return True
            return False
    
    def get_stats(self, short_code: str) -> Optional[Dict]:
        """Get analytics for a URL"""
        with self._lock:
            url_data = self._urls.get(short_code)
            if url_data:
                return {
                    'url': url_data['original_url'],
                    'clicks': url_data['clicks'],
                    'created_at': url_data['created_at']
                }
            return None
    
    def url_exists(self, short_code: str) -> bool:
        """Check if a short code exists"""
        with self._lock:
            return short_code in self._urls

# Global instance
url_store = URLStore()