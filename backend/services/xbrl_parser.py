"""
XBRL Parser for financial data extraction
日本のEDINET XBRLファイルから財務データを抽出
"""
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from pathlib import Path
# Use defusedxml to prevent XXE attacks
from defusedxml.ElementTree import parse, fromstring
import xml.etree.ElementTree as ET  # For register_namespace only

logger = logging.getLogger(__name__)


class XBRLParser:
    """XBRL document parser for Japanese financial statements"""
    
    # Japanese GAAP namespaces
    NAMESPACES = {
        'xbrl': 'http://www.xbrl.org/2003/instance',
        'jp-gaap': 'http://info.edinet-fsa.go.jp/jp/fr/gaap/o/rt/',
        'jpdei': 'http://info.edinet-fsa.go.jp/jp/fr/gaap/o/dei/',
        'iso4217': 'http://www.xbrl.org/2003/iso4217',
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink'
    }
    
    # 財務項目のマッピング
    FINANCIAL_ITEMS = {
        # 貸借対照表
        'total_assets': 'jp-gaap:Assets',
        'current_assets': 'jp-gaap:CurrentAssets', 
        'noncurrent_assets': 'jp-gaap:NoncurrentAssets',
        'total_liabilities': 'jp-gaap:Liabilities',
        'current_liabilities': 'jp-gaap:CurrentLiabilities',
        'noncurrent_liabilities': 'jp-gaap:NoncurrentLiabilities',
        'net_assets': 'jp-gaap:NetAssets',
        'shareholders_equity': 'jp-gaap:ShareholdersEquity',
        
        # 損益計算書
        'net_sales': 'jp-gaap:NetSales',
        'cost_of_sales': 'jp-gaap:CostOfSales',
        'gross_profit': 'jp-gaap:GrossProfit',
        'operating_income': 'jp-gaap:OperatingIncome',
        'net_income': 'jp-gaap:NetIncome',
        
        # キャッシュフロー計算書
        'operating_cash_flow': 'jp-gaap:CashFlowsFromOperatingActivities',
        'investing_cash_flow': 'jp-gaap:CashFlowsFromInvestingActivities',
        'financing_cash_flow': 'jp-gaap:CashFlowsFromFinancingActivities',
        
        # 企業情報
        'company_name_jp': 'jpdei:CompanyNameInJapanese',
        'company_name_en': 'jpdei:CompanyNameInEnglish',
        'securities_code': 'jpdei:SecuritiesCode',
    }
    
    def __init__(self):
        self.root = None
        self.contexts = {}
        self.units = {}
        
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """XBRLファイルを解析"""
        try:
            tree = parse(file_path)
            self.root = tree.getroot()
            
            # ネームスペースを登録
            for prefix, uri in self.NAMESPACES.items():
                ET.register_namespace(prefix, uri)
            
            return self._extract_financial_data()
            
        except Exception as e:
            logger.error(f"XML parsing error: {e}")
            raise
    
    def parse_content(self, xbrl_content: bytes) -> Dict[str, Any]:
        """XBRLコンテンツ（bytes）を解析"""
        try:
            self.root = fromstring(xbrl_content)
            
            # ネームスペースを登録
            for prefix, uri in self.NAMESPACES.items():
                ET.register_namespace(prefix, uri)
            
            return self._extract_financial_data()
            
        except Exception as e:
            logger.error(f"XBRL parsing error: {e}")
            raise
    
    def _extract_financial_data(self) -> Dict[str, Any]:
        """財務データを抽出"""
        # コンテキストと単位を解析
        self._parse_contexts()
        self._parse_units()
        
        # 財務データを抽出
        financial_data = {
            'company_info': self._extract_company_info(),
            'balance_sheet': self._extract_balance_sheet(),
            'income_statement': self._extract_income_statement(),
            'cash_flow': self._extract_cash_flow(),
            'periods': list(self.contexts.keys())
        }
        
        return financial_data
    
    def _parse_contexts(self):
        """コンテキスト情報を解析"""
        contexts = self.root.findall('.//xbrl:context', self.NAMESPACES)
        
        for context in contexts:
            context_id = context.get('id')
            
            # 期間情報を取得
            period_elem = context.find('xbrl:period', self.NAMESPACES)
            if period_elem is not None:
                # 時点（instant）か期間（duration）か判定
                instant = period_elem.find('xbrl:instant', self.NAMESPACES)
                if instant is not None:
                    period_info = {
                        'type': 'instant',
                        'date': instant.text
                    }
                else:
                    start = period_elem.find('xbrl:startDate', self.NAMESPACES)
                    end = period_elem.find('xbrl:endDate', self.NAMESPACES)
                    if start is not None and end is not None:
                        period_info = {
                            'type': 'duration',
                            'start_date': start.text,
                            'end_date': end.text
                        }
                    else:
                        continue
                
                self.contexts[context_id] = period_info
    
    def _parse_units(self):
        """単位情報を解析"""
        units = self.root.findall('.//xbrl:unit', self.NAMESPACES)
        
        for unit in units:
            unit_id = unit.get('id')
            measure = unit.find('xbrl:measure', self.NAMESPACES)
            if measure is not None:
                self.units[unit_id] = measure.text
    
    def _extract_company_info(self) -> Dict[str, Any]:
        """企業情報を抽出"""
        company_info = {}
        
        for key, xpath in self.FINANCIAL_ITEMS.items():
            if key.startswith('company_') or key == 'securities_code':
                elements = self.root.findall(f'.//{xpath}', self.NAMESPACES)
                if elements:
                    company_info[key] = elements[0].text
        
        return company_info
    
    def _extract_balance_sheet(self) -> Dict[str, Any]:
        """貸借対照表データを抽出"""
        bs_items = [
            'total_assets', 'current_assets', 'noncurrent_assets',
            'total_liabilities', 'current_liabilities', 'noncurrent_liabilities',
            'net_assets', 'shareholders_equity'
        ]
        
        balance_sheet = {}
        for item in bs_items:
            if item in self.FINANCIAL_ITEMS:
                value = self._get_financial_value(item, period_type='instant')
                if value is not None:
                    balance_sheet[item] = value
        
        return balance_sheet
    
    def _extract_income_statement(self) -> Dict[str, Any]:
        """損益計算書データを抽出"""
        pl_items = [
            'net_sales', 'cost_of_sales', 'gross_profit', 
            'operating_income', 'net_income'
        ]
        
        income_statement = {}
        for item in pl_items:
            if item in self.FINANCIAL_ITEMS:
                current = self._get_financial_value(item, period_type='duration', period='current')
                prior = self._get_financial_value(item, period_type='duration', period='prior')
                
                income_statement[item] = {
                    'current': current,
                    'prior': prior
                }
        
        return income_statement
    
    def _extract_cash_flow(self) -> Dict[str, Any]:
        """キャッシュフロー計算書データを抽出"""
        cf_items = [
            'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow'
        ]
        
        cash_flow = {}
        for item in cf_items:
            if item in self.FINANCIAL_ITEMS:
                current = self._get_financial_value(item, period_type='duration', period='current')
                prior = self._get_financial_value(item, period_type='duration', period='prior')
                
                cash_flow[item] = {
                    'current': current,
                    'prior': prior
                }
        
        return cash_flow
    
    def _safe_decimal_convert(self, text: str) -> Optional[Decimal]:
        """安全な Decimal 変換"""
        if not text or text.strip() == '':
            return None
        try:
            return Decimal(text.strip())
        except (ValueError, TypeError, InvalidOperation):
            logger.warning(f"Invalid decimal value: {text}")
            return None
    
    def _get_financial_value(self, item_key: str, period_type: str = 'instant', period: str = 'current') -> Optional[Decimal]:
        """財務項目の値を取得"""
        xpath = self.FINANCIAL_ITEMS.get(item_key)
        if not xpath:
            return None
        
        elements = self.root.findall(f'.//{xpath}', self.NAMESPACES)
        
        for element in elements:
            context_ref = element.get('contextRef')
            if context_ref and context_ref in self.contexts:
                context_info = self.contexts[context_ref]
                
                # 期間タイプをチェック
                if context_info['type'] != period_type:
                    continue
                
                # 期間指定がある場合（current/prior）
                if period_type == 'duration' and period:
                    # 動的な期間判定ロジック
                    end_date = context_info.get('end_date', '')
                    current_year = datetime.now().year
                    
                    if period == 'current' and str(current_year) not in end_date:
                        continue
                    elif period == 'prior' and str(current_year - 1) not in end_date:
                        continue
                
                # 値を取得
                value = self._safe_decimal_convert(element.text)
                if value is not None:
                    return value
        
        return None


def test_xbrl_parser():
    """XBRL Parserのテスト"""
    parser = XBRLParser()
    
    # サンプルファイルを解析
    sample_file = Path(__file__).parent.parent / "sample_financial_data.xml"
    
    try:
        result = parser.parse_file(str(sample_file))
        print("🎉 XBRL解析成功!")
        
        # 結果を表示
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        
    except Exception as e:
        print(f"❌ エラー: {e}")


if __name__ == "__main__":
    test_xbrl_parser()