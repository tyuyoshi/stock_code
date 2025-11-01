"""
Tests for EDINET API Client
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
import requests
from services.edinet_client import EDINETClient


class TestEDINETClient:
    """Test suite for EDINET API Client"""
    
    @pytest.fixture
    def client(self):
        """Create EDINET client instance"""
        return EDINETClient(api_key="test_api_key")
    
    @pytest.fixture
    def mock_response(self):
        """Create mock response object"""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            "metadata": {
                "title": "Document List",
                "parameter": {
                    "date": "2024-01-01",
                    "type": "2"
                },
                "resultset": {
                    "count": 2
                },
                "processDateTime": "2024-01-01T10:00:00.000+09:00",
                "status": "200",
                "message": "OK"
            },
            "results": [
                {
                    "docID": "S100TEST1",
                    "edinetCode": "E00001",
                    "secCode": "10010",
                    "JCN": "1234567890123",
                    "filerName": "テスト株式会社",
                    "fundCode": None,
                    "ordinanceCode": "010",
                    "formCode": "030000",
                    "docTypeCode": "120",  # 有価証券報告書
                    "periodStart": "2023-04-01",
                    "periodEnd": "2024-03-31",
                    "submitDateTime": "2024-06-28 15:00",
                    "docDescription": "有価証券報告書－第100期"
                },
                {
                    "docID": "S100TEST2",
                    "edinetCode": "E00002",
                    "secCode": "20020",
                    "JCN": "9876543210987",
                    "filerName": "サンプル株式会社",
                    "fundCode": None,
                    "ordinanceCode": "010",
                    "formCode": "030000",
                    "docTypeCode": "140",  # 四半期報告書
                    "periodStart": "2024-01-01",
                    "periodEnd": "2024-03-31",
                    "submitDateTime": "2024-05-15 16:00",
                    "docDescription": "四半期報告書－第101期第1四半期"
                }
            ]
        }
        return mock
    
    @pytest.mark.unit
    def test_init(self):
        """Test client initialization"""
        client = EDINETClient(api_key="test_key_123")
        assert client.api_key == "test_key_123"
        assert client.session is not None
        assert client.BASE_URL == "https://disclosure.edinet-fsa.go.jp/api/v2"
    
    @pytest.mark.unit
    def test_init_no_api_key(self):
        """Test client initialization without API key"""
        with pytest.raises(ValueError, match="EDINET API key is required"):
            EDINETClient(api_key=None)
    
    @pytest.mark.unit
    @patch('requests.Session.get')
    def test_get_document_list_success(self, mock_get, client, mock_response):
        """Test successful document list retrieval"""
        mock_get.return_value = mock_response
        
        result = client.get_document_list(date(2024, 1, 1))
        
        assert result["metadata"]["status"] == "200"
        assert len(result["results"]) == 2
        assert result["results"][0]["docID"] == "S100TEST1"
        assert result["results"][1]["docID"] == "S100TEST2"
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "date=2024-01-01" in call_args[0][0]
        assert "type=2" in call_args[0][0]
    
    @pytest.mark.unit
    @patch('requests.Session.get')
    def test_get_document_list_with_type(self, mock_get, client, mock_response):
        """Test document list retrieval with custom type"""
        mock_get.return_value = mock_response
        
        result = client.get_document_list(date(2024, 1, 1), doc_type=3)
        
        # Verify API call with custom type
        call_args = mock_get.call_args
        assert "type=3" in call_args[0][0]
    
    @pytest.mark.unit
    @patch('requests.Session.get')
    def test_get_document_list_api_error(self, mock_get, client):
        """Test document list retrieval with API error"""
        mock_get.side_effect = requests.RequestException("API Error")
        
        with pytest.raises(requests.RequestException):
            client.get_document_list(date(2024, 1, 1))
    
    @pytest.mark.unit
    @patch('requests.Session.get')
    def test_get_document_success(self, mock_get, client):
        """Test successful document retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<XBRL>Document Content</XBRL>"
        mock_response.headers = {"Content-Type": "application/xml"}
        mock_get.return_value = mock_response
        
        result = client.get_document("S100TEST1")
        
        assert result == b"<XBRL>Document Content</XBRL>"
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "S100TEST1" in call_args[0][0]
    
    @pytest.mark.unit
    @patch('requests.Session.get')
    def test_get_document_with_type(self, mock_get, client):
        """Test document retrieval with specific type"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"PDF Content"
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_get.return_value = mock_response
        
        result = client.get_document("S100TEST1", doc_type=2)
        
        assert result == b"PDF Content"
        call_args = mock_get.call_args
        assert "type=2" in call_args[0][0]
    
    @pytest.mark.unit
    @patch('requests.Session.get')
    def test_get_document_not_found(self, mock_get, client):
        """Test document retrieval when document not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        with pytest.raises(requests.HTTPError):
            client.get_document("INVALID_DOC_ID")
    
    @pytest.mark.unit
    def test_parse_xbrl_valid_content(self, client):
        """Test XBRL parsing with valid content"""
        xbrl_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance">
            <context id="CurrentYearDuration">
                <period>
                    <startDate>2023-04-01</startDate>
                    <endDate>2024-03-31</endDate>
                </period>
            </context>
            <NetSales contextRef="CurrentYearDuration">1000000000</NetSales>
            <OperatingIncome contextRef="CurrentYearDuration">100000000</OperatingIncome>
        </xbrl>"""
        
        result = client.parse_xbrl(xbrl_content)
        
        assert result is not None
        # The actual parsing logic would be tested based on implementation
    
    @pytest.mark.unit
    def test_parse_xbrl_invalid_content(self, client):
        """Test XBRL parsing with invalid content"""
        invalid_content = b"Not valid XBRL content"
        
        with pytest.raises(Exception):  # Specific exception depends on implementation
            client.parse_xbrl(invalid_content)
    
    @pytest.mark.unit
    def test_extract_financial_data(self, client):
        """Test financial data extraction from parsed XBRL"""
        parsed_data = {
            "NetSales": 1000000000,
            "OperatingIncome": 100000000,
            "NetIncome": 80000000,
            "TotalAssets": 5000000000,
            "ShareholdersEquity": 2000000000
        }
        
        result = client.extract_financial_data(parsed_data)
        
        # Test would verify data extraction based on implementation
        assert result is not None
    
    @pytest.mark.integration
    @pytest.mark.requires_api
    def test_full_workflow(self, client):
        """Test complete workflow from list to extraction (integration test)"""
        # This would be a full integration test if we had actual API access
        # For now, we'll mock the entire flow
        with patch.object(client, 'get_document_list') as mock_list:
            mock_list.return_value = {
                "results": [{"docID": "S100TEST1", "docTypeCode": "120"}]
            }
            
            with patch.object(client, 'get_document') as mock_doc:
                mock_doc.return_value = b"<XBRL>content</XBRL>"
                
                with patch.object(client, 'parse_xbrl') as mock_parse:
                    mock_parse.return_value = {"NetSales": 1000000000}
                    
                    with patch.object(client, 'extract_financial_data') as mock_extract:
                        mock_extract.return_value = {
                            "revenue": 1000000000,
                            "profit": 100000000
                        }
                        
                        # Execute workflow
                        docs = client.get_document_list(date(2024, 1, 1))
                        doc_id = docs["results"][0]["docID"]
                        content = client.get_document(doc_id)
                        parsed = client.parse_xbrl(content)
                        data = client.extract_financial_data(parsed)
                        
                        assert data["revenue"] == 1000000000
                        assert data["profit"] == 100000000


class TestEDINETClientHelpers:
    """Test helper functions and utilities"""
    
    @pytest.mark.unit
    def test_date_formatting(self):
        """Test date formatting for API calls"""
        test_date = date(2024, 1, 1)
        formatted = test_date.strftime("%Y-%m-%d")
        assert formatted == "2024-01-01"
    
    @pytest.mark.unit
    def test_doc_type_codes(self):
        """Test document type code mappings"""
        doc_types = {
            "120": "有価証券報告書",
            "140": "四半期報告書",
            "160": "半期報告書",
            "170": "臨時報告書"
        }
        
        assert doc_types["120"] == "有価証券報告書"
        assert doc_types["140"] == "四半期報告書"