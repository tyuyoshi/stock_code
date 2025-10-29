"""EDINET API Client Service"""

import requests
from typing import Optional, Dict, List, Any
from datetime import datetime, date
import time
import logging

logger = logging.getLogger(__name__)


class EDINETClient:
    """Client for EDINET API"""

    BASE_URL = "https://disclosure.edinet-fsa.go.jp/api/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "StockCode/1.0"
        })
    
    def get_document_list(self, date: date) -> Dict[str, Any]:
        """Get document list for a specific date"""
        url = f"{self.BASE_URL}/documents.json"
        params = {
            "date": date.strftime("%Y-%m-%d"),
            "type": 2  # 有価証券報告書
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch document list: {e}")
            raise
    
    def get_document(self, doc_id: str, output_format: str = "xbrl") -> bytes:
        """Get document content"""
        url = f"{self.BASE_URL}/documents/{doc_id}"
        params = {
            "type": output_format
        }
        
        try:
            response = self.session.get(url, params=params, stream=True)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch document {doc_id}: {e}")
            raise
    
    def parse_xbrl(self, xbrl_content: bytes) -> Dict[str, Any]:
        """Parse XBRL content to extract financial data"""
        # TODO: Implement XBRL parsing logic
        # This would typically use libraries like python-xbrl or arelle
        pass
    
    def extract_financial_data(self, doc_id: str) -> Dict[str, Any]:
        """Extract financial data from a document"""
        xbrl_content = self.get_document(doc_id)
        return self.parse_xbrl(xbrl_content)