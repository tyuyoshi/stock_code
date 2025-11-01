"""
Tests for XBRL Parser
"""
import pytest
from decimal import Decimal
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from services.xbrl_parser import XBRLParser


class TestXBRLParser:
    """Test suite for XBRL Parser"""
    
    @pytest.fixture
    def parser(self):
        """Create XBRL parser instance"""
        return XBRLParser()
    
    @pytest.fixture
    def sample_xbrl_simple(self):
        """Simple XBRL sample for basic testing"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xmlns:jppfs="http://disclosure.edinet-fsa.go.jp/jppfs/2019-01-31">
            <context id="CurrentYearInstant">
                <entity>
                    <identifier scheme="http://disclosure.edinet-fsa.go.jp">E00001</identifier>
                </entity>
                <period>
                    <instant>2024-03-31</instant>
                </period>
            </context>
            <context id="CurrentYearDuration">
                <entity>
                    <identifier scheme="http://disclosure.edinet-fsa.go.jp">E00001</identifier>
                </entity>
                <period>
                    <startDate>2023-04-01</startDate>
                    <endDate>2024-03-31</endDate>
                </period>
            </context>
            <unit id="JPY">
                <measure>iso4217:JPY</measure>
            </unit>
            <jppfs:NetSales contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">1000000000</jppfs:NetSales>
            <jppfs:OperatingIncome contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">100000000</jppfs:OperatingIncome>
            <jppfs:OrdinaryIncome contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">95000000</jppfs:OrdinaryIncome>
            <jppfs:NetIncome contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">70000000</jppfs:NetIncome>
            <jppfs:TotalAssets contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">5000000000</jppfs:TotalAssets>
            <jppfs:ShareholdersEquity contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">2000000000</jppfs:ShareholdersEquity>
        </xbrl>"""
    
    @pytest.fixture
    def sample_xbrl_comprehensive(self):
        """Comprehensive XBRL sample with more financial items"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xmlns:jppfs="http://disclosure.edinet-fsa.go.jp/jppfs/2019-01-31"
              xmlns:jpdei="http://disclosure.edinet-fsa.go.jp/jpdei/2019-01-31">
            <context id="CurrentYearInstant">
                <entity>
                    <identifier scheme="http://disclosure.edinet-fsa.go.jp">E00001</identifier>
                </entity>
                <period>
                    <instant>2024-03-31</instant>
                </period>
            </context>
            <context id="CurrentYearDuration">
                <entity>
                    <identifier scheme="http://disclosure.edinet-fsa.go.jp">E00001</identifier>
                </entity>
                <period>
                    <startDate>2023-04-01</startDate>
                    <endDate>2024-03-31</endDate>
                </period>
            </context>
            <unit id="JPY">
                <measure>iso4217:JPY</measure>
            </unit>
            <unit id="shares">
                <measure>xbrli:shares</measure>
            </unit>
            <!-- Company Info -->
            <jpdei:CompanyNameInJapaneseDEI contextRef="CurrentYearInstant">テスト株式会社</jpdei:CompanyNameInJapaneseDEI>
            <jpdei:CompanyNameInEnglishDEI contextRef="CurrentYearInstant">Test Corporation</jpdei:CompanyNameInEnglishDEI>
            <jpdei:SecurityCodeDEI contextRef="CurrentYearInstant">1234</jpdei:SecurityCodeDEI>
            <!-- Income Statement -->
            <jppfs:NetSales contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">10000000000</jppfs:NetSales>
            <jppfs:CostOfSales contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">7000000000</jppfs:CostOfSales>
            <jppfs:GrossProfit contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">3000000000</jppfs:GrossProfit>
            <jppfs:SellingGeneralAndAdministrativeExpenses contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">2000000000</jppfs:SellingGeneralAndAdministrativeExpenses>
            <jppfs:OperatingIncome contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">1000000000</jppfs:OperatingIncome>
            <jppfs:OrdinaryIncome contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">950000000</jppfs:OrdinaryIncome>
            <jppfs:IncomeBeforeIncomeTaxes contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">900000000</jppfs:IncomeBeforeIncomeTaxes>
            <jppfs:IncomeTaxes contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">200000000</jppfs:IncomeTaxes>
            <jppfs:NetIncome contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">700000000</jppfs:NetIncome>
            <!-- Balance Sheet -->
            <jppfs:CurrentAssets contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">3000000000</jppfs:CurrentAssets>
            <jppfs:NonCurrentAssets contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">2000000000</jppfs:NonCurrentAssets>
            <jppfs:TotalAssets contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">5000000000</jppfs:TotalAssets>
            <jppfs:CurrentLiabilities contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">1500000000</jppfs:CurrentLiabilities>
            <jppfs:NonCurrentLiabilities contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">1500000000</jppfs:NonCurrentLiabilities>
            <jppfs:TotalLiabilities contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">3000000000</jppfs:TotalLiabilities>
            <jppfs:ShareholdersEquity contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">2000000000</jppfs:ShareholdersEquity>
            <jppfs:TotalNetAssets contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">2000000000</jppfs:TotalNetAssets>
            <!-- Cash Flow -->
            <jppfs:NetCashProvidedByOperatingActivities contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">800000000</jppfs:NetCashProvidedByOperatingActivities>
            <jppfs:NetCashProvidedByInvestingActivities contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">-300000000</jppfs:NetCashProvidedByInvestingActivities>
            <jppfs:NetCashProvidedByFinancingActivities contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">-200000000</jppfs:NetCashProvidedByFinancingActivities>
            <!-- Share Info -->
            <jppfs:NumberOfIssuedSharesAsOfFiscalYearEnd contextRef="CurrentYearInstant" decimals="0" unitRef="shares">100000000</jppfs:NumberOfIssuedSharesAsOfFiscalYearEnd>
        </xbrl>"""
    
    @pytest.mark.unit
    def test_init(self, parser):
        """Test parser initialization"""
        assert parser.root is None
        assert parser.contexts == {}
        assert parser.units == {}
    
    @pytest.mark.unit
    def test_parse_content_simple(self, parser, sample_xbrl_simple):
        """Test parsing simple XBRL content"""
        result = parser.parse_content(sample_xbrl_simple)
        
        assert result is not None
        assert "financial_data" in result
        
        financial_data = result["financial_data"]
        assert financial_data.get("revenue") == Decimal("1000000000")
        assert financial_data.get("operating_income") == Decimal("100000000")
        assert financial_data.get("net_income") == Decimal("70000000")
        assert financial_data.get("total_assets") == Decimal("5000000000")
        assert financial_data.get("shareholders_equity") == Decimal("2000000000")
    
    @pytest.mark.unit
    def test_parse_content_comprehensive(self, parser, sample_xbrl_comprehensive):
        """Test parsing comprehensive XBRL content"""
        result = parser.parse_content(sample_xbrl_comprehensive)
        
        assert result is not None
        
        # Check company info
        if "company_info" in result:
            company = result["company_info"]
            assert company.get("name_jp") == "テスト株式会社"
            assert company.get("name_en") == "Test Corporation"
            assert company.get("security_code") == "1234"
        
        # Check financial data
        financial_data = result["financial_data"]
        
        # Income statement
        assert financial_data.get("revenue") == Decimal("10000000000")
        assert financial_data.get("cost_of_sales") == Decimal("7000000000")
        assert financial_data.get("gross_profit") == Decimal("3000000000")
        assert financial_data.get("operating_income") == Decimal("1000000000")
        assert financial_data.get("net_income") == Decimal("700000000")
        
        # Balance sheet
        assert financial_data.get("current_assets") == Decimal("3000000000")
        assert financial_data.get("non_current_assets") == Decimal("2000000000")
        assert financial_data.get("total_assets") == Decimal("5000000000")
        assert financial_data.get("current_liabilities") == Decimal("1500000000")
        assert financial_data.get("total_liabilities") == Decimal("3000000000")
        assert financial_data.get("shareholders_equity") == Decimal("2000000000")
        
        # Cash flow
        assert financial_data.get("cash_flow_operating") == Decimal("800000000")
        assert financial_data.get("cash_flow_investing") == Decimal("-300000000")
        assert financial_data.get("cash_flow_financing") == Decimal("-200000000")
    
    @pytest.mark.unit
    def test_parse_invalid_xml(self, parser):
        """Test parsing invalid XML content"""
        invalid_xml = "This is not valid XML"
        
        with pytest.raises(ET.ParseError):
            parser.parse_content(invalid_xml)
    
    @pytest.mark.unit
    def test_parse_empty_xbrl(self, parser):
        """Test parsing empty but valid XBRL"""
        empty_xbrl = """<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance">
        </xbrl>"""
        
        result = parser.parse_content(empty_xbrl)
        
        assert result is not None
        assert "financial_data" in result
        assert result["financial_data"] == {}
    
    @pytest.mark.unit
    def test_safe_decimal_convert(self, parser):
        """Test safe decimal conversion"""
        # Valid conversions
        assert parser._safe_decimal_convert("1000000") == Decimal("1000000")
        assert parser._safe_decimal_convert("1,000,000") == Decimal("1000000")
        assert parser._safe_decimal_convert("1000000.50") == Decimal("1000000.50")
        assert parser._safe_decimal_convert("-500000") == Decimal("-500000")
        
        # Invalid conversions should return None
        assert parser._safe_decimal_convert("") is None
        assert parser._safe_decimal_convert(None) is None
        assert parser._safe_decimal_convert("invalid") is None
        assert parser._safe_decimal_convert("NaN") is None
    
    @pytest.mark.unit
    def test_parse_contexts(self, parser):
        """Test context parsing"""
        xbrl_with_contexts = """<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance">
            <context id="CurrentYear">
                <entity>
                    <identifier scheme="http://disclosure.edinet-fsa.go.jp">E00001</identifier>
                </entity>
                <period>
                    <startDate>2023-04-01</startDate>
                    <endDate>2024-03-31</endDate>
                </period>
            </context>
            <context id="PreviousYear">
                <entity>
                    <identifier scheme="http://disclosure.edinet-fsa.go.jp">E00001</identifier>
                </entity>
                <period>
                    <startDate>2022-04-01</startDate>
                    <endDate>2023-03-31</endDate>
                </period>
            </context>
        </xbrl>"""
        
        parser.parse_content(xbrl_with_contexts)
        
        assert len(parser.contexts) == 2
        assert "CurrentYear" in parser.contexts
        assert "PreviousYear" in parser.contexts
        
        current_context = parser.contexts["CurrentYear"]
        assert current_context["entity_id"] == "E00001"
        assert current_context["start_date"] == "2023-04-01"
        assert current_context["end_date"] == "2024-03-31"
    
    @pytest.mark.unit
    def test_parse_units(self, parser):
        """Test unit parsing"""
        xbrl_with_units = """<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance">
            <unit id="JPY">
                <measure>iso4217:JPY</measure>
            </unit>
            <unit id="shares">
                <measure>xbrli:shares</measure>
            </unit>
            <unit id="pure">
                <measure>xbrli:pure</measure>
            </unit>
        </xbrl>"""
        
        parser.parse_content(xbrl_with_units)
        
        assert len(parser.units) == 3
        assert "JPY" in parser.units
        assert "shares" in parser.units
        assert "pure" in parser.units
        
        assert parser.units["JPY"] == "iso4217:JPY"
        assert parser.units["shares"] == "xbrli:shares"
    
    @pytest.mark.unit
    def test_file_parsing(self, parser, tmp_path):
        """Test parsing from file"""
        # Create temporary XBRL file
        xbrl_file = tmp_path / "test.xbrl"
        xbrl_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance"
              xmlns:jppfs="http://disclosure.edinet-fsa.go.jp/jppfs/2019-01-31">
            <context id="CurrentYearDuration">
                <entity>
                    <identifier scheme="http://disclosure.edinet-fsa.go.jp">E00001</identifier>
                </entity>
                <period>
                    <startDate>2023-04-01</startDate>
                    <endDate>2024-03-31</endDate>
                </period>
            </context>
            <unit id="JPY">
                <measure>iso4217:JPY</measure>
            </unit>
            <jppfs:NetSales contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">2000000000</jppfs:NetSales>
        </xbrl>""", encoding="utf-8")
        
        result = parser.parse_file(str(xbrl_file))
        
        assert result is not None
        assert "financial_data" in result
        assert result["financial_data"].get("revenue") == Decimal("2000000000")
    
    @pytest.mark.unit
    def test_file_not_found(self, parser):
        """Test parsing non-existent file"""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/path/to/nonexistent/file.xbrl")
    
    @pytest.mark.unit
    def test_negative_values(self, parser):
        """Test parsing negative values"""
        xbrl_with_negative = """<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance"
              xmlns:jppfs="http://disclosure.edinet-fsa.go.jp/jppfs/2019-01-31">
            <context id="CurrentYearDuration">
                <entity>
                    <identifier scheme="http://disclosure.edinet-fsa.go.jp">E00001</identifier>
                </entity>
                <period>
                    <startDate>2023-04-01</startDate>
                    <endDate>2024-03-31</endDate>
                </period>
            </context>
            <unit id="JPY">
                <measure>iso4217:JPY</measure>
            </unit>
            <jppfs:NetIncome contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">-100000000</jppfs:NetIncome>
            <jppfs:NetCashProvidedByInvestingActivities contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">-500000000</jppfs:NetCashProvidedByInvestingActivities>
        </xbrl>"""
        
        result = parser.parse_content(xbrl_with_negative)
        
        financial_data = result["financial_data"]
        assert financial_data.get("net_income") == Decimal("-100000000")
        assert financial_data.get("cash_flow_investing") == Decimal("-500000000")


class TestXBRLParserIntegration:
    """Integration tests for XBRL Parser"""
    
    @pytest.mark.integration
    def test_parse_real_edinet_structure(self):
        """Test parsing structure similar to real EDINET documents"""
        parser = XBRLParser()
        
        # This would be a more complex test with actual EDINET document structure
        # For now, using a simplified version
        edinet_like_xbrl = """<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance"
              xmlns:xlink="http://www.w3.org/1999/xlink"
              xmlns:jppfs="http://disclosure.edinet-fsa.go.jp/jppfs/2019-01-31"
              xmlns:jpdei="http://disclosure.edinet-fsa.go.jp/jpdei/2019-01-31"
              xmlns:jpigp="http://disclosure.edinet-fsa.go.jp/jpigp/2019-01-31">
            <context id="FilingDateInstant">
                <entity>
                    <identifier scheme="http://disclosure.edinet-fsa.go.jp">E00001</identifier>
                </entity>
                <period>
                    <instant>2024-06-28</instant>
                </period>
            </context>
            <jpdei:EDINETCodeDEI contextRef="FilingDateInstant">E00001</jpdei:EDINETCodeDEI>
            <jpdei:FundCodeDEI contextRef="FilingDateInstant" xsi:nil="true"/>
            <jpdei:OrdinanceCodeDEI contextRef="FilingDateInstant">010</jpdei:OrdinanceCodeDEI>
            <jpdei:FormCodeDEI contextRef="FilingDateInstant">030000</jpdei:FormCodeDEI>
            <jpdei:DocTypeCodeDEI contextRef="FilingDateInstant">120</jpdei:DocTypeCodeDEI>
        </xbrl>"""
        
        result = parser.parse_content(edinet_like_xbrl)
        assert result is not None