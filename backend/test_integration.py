#!/usr/bin/env python3
"""
EDINET API + XBRL Parser 統合テスト
"""
import sys
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).parent))

from services.edinet_client import EDINETClient


def test_xbrl_parsing():
    """XBRL Parsingの統合テスト"""
    print("🧪 EDINET + XBRL Parser 統合テスト")
    
    # サンプルXBRLファイルを読み込み
    sample_file = Path(__file__).parent / "sample_financial_data.xml"
    
    try:
        # XBRLファイルを読み込み
        with open(sample_file, 'rb') as f:
            xbrl_content = f.read()
        
        # EDINETクライアントでXBRLを解析
        client = EDINETClient()
        result = client.parse_xbrl(xbrl_content)
        
        print("✅ 統合テスト成功!")
        
        # 結果の要約を表示
        company = result.get('company_info', {})
        print(f"\n📊 解析結果:")
        print(f"  企業名: {company.get('company_name_jp')}")
        print(f"  証券コード: {company.get('securities_code')}")
        
        # 主要財務指標
        bs = result.get('balance_sheet', {})
        pl = result.get('income_statement', {})
        
        if bs.get('total_assets'):
            assets = int(bs['total_assets']) / 1000000000  # 億円
            print(f"  総資産: {assets:,.0f}億円")
        
        if bs.get('net_assets'):
            net_assets = int(bs['net_assets']) / 1000000000
            print(f"  純資産: {net_assets:,.0f}億円")
        
        if pl.get('net_sales', {}).get('current'):
            sales = int(pl['net_sales']['current']) / 1000000000
            print(f"  売上高: {sales:,.0f}億円")
        
        if pl.get('net_income', {}).get('current'):
            income = int(pl['net_income']['current']) / 1000000000
            print(f"  純利益: {income:,.0f}億円")
        
        return True
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")
        return False


def test_financial_ratios():
    """財務指標計算のテスト"""
    print("\n📈 財務指標計算テスト")
    
    sample_file = Path(__file__).parent / "sample_financial_data.xml"
    
    try:
        with open(sample_file, 'rb') as f:
            xbrl_content = f.read()
        
        client = EDINETClient()
        data = client.parse_xbrl(xbrl_content)
        
        # 主要財務指標を計算
        bs = data.get('balance_sheet', {})
        pl = data.get('income_statement', {})
        
        # ROE計算（自己資本利益率）
        if bs.get('shareholders_equity') and pl.get('net_income', {}).get('current'):
            equity = float(bs['shareholders_equity'])
            net_income = float(pl['net_income']['current'])
            roe = (net_income / equity) * 100
            print(f"  ROE: {roe:.2f}%")
        
        # 自己資本比率
        if bs.get('total_assets') and bs.get('shareholders_equity'):
            assets = float(bs['total_assets'])
            equity = float(bs['shareholders_equity'])
            equity_ratio = (equity / assets) * 100
            print(f"  自己資本比率: {equity_ratio:.2f}%")
        
        # 売上高営業利益率
        if pl.get('net_sales', {}).get('current') and pl.get('operating_income', {}).get('current'):
            sales = float(pl['net_sales']['current'])
            op_income = float(pl['operating_income']['current'])
            op_margin = (op_income / sales) * 100
            print(f"  営業利益率: {op_margin:.2f}%")
        
        print("✅ 財務指標計算成功!")
        return True
        
    except Exception as e:
        print(f"❌ 財務指標計算エラー: {e}")
        return False


if __name__ == "__main__":
    success1 = test_xbrl_parsing()
    success2 = test_financial_ratios()
    
    if success1 and success2:
        print("\n🎉 全ての統合テストが成功しました!")
        print("\n📝 次のステップ:")
        print("  1. EDINET API認証方法の調査")
        print("  2. 実際の有価証券報告書での動作確認")
        print("  3. データベース連携機能の実装")
        print("  4. 財務指標計算エンジンとの統合")
    else:
        print("\n❌ 一部のテストが失敗しました")