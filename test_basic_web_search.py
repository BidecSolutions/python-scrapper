"""Test the basic web search source"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sources.basic_web_search import BasicWebSearchSource

def test_basic_search():
    print("=" * 70)
    print("Testing Basic Web Search Source")
    print("=" * 70)
    
    source = BasicWebSearchSource()
    print("\n✅ Basic web search source initialized")
    
    print("\n🔍 Testing search: 'dentist' in 'newyork'")
    try:
        leads = list(source.search("dentist", "newyork"))
        print(f"\n✅ Found {len(leads)} leads")
        
        if leads:
            print("\n📋 Sample leads:")
            for i, lead in enumerate(leads[:5], 1):
                print(f"\n  {i}. {lead.name}")
                print(f"     Website: {lead.website}")
                print(f"     Source: {lead.source}")
        else:
            print("\n⚠️  No leads found. This might be due to:")
            print("   - Network issues")
            print("   - DuckDuckGo HTML structure changes")
            print("   - Rate limiting")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_search()

