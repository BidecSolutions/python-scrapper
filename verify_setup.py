"""Quick verification script to check if Google Custom Search is configured correctly"""
import os
import sys

# Load .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def check_env_setup():
    """Check if required environment variables are set"""
    print("=" * 60)
    print("Checking Google Custom Search API Configuration")
    print("=" * 60)
    print()
    
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_CX")
    
    issues = []
    
    if not api_key:
        issues.append("[X] GOOGLE_SEARCH_API_KEY is not set")
    else:
        print(f"[OK] GOOGLE_SEARCH_API_KEY is set: {api_key[:10]}...{api_key[-4:]}")
    
    if not cx:
        issues.append("[X] GOOGLE_SEARCH_CX is not set")
    else:
        print(f"[OK] GOOGLE_SEARCH_CX is set: {cx}")
    
    print()
    
    if issues:
        print("[!] Issues found:")
        for issue in issues:
            print(f"   {issue}")
        print()
        print("To fix:")
        print("  1. Create a .env file in the project root")
        print("  2. Add these lines:")
        print("     GOOGLE_SEARCH_API_KEY=your_api_key_here")
        print("     GOOGLE_SEARCH_CX=your_cx_id_here")
        print("  3. Restart your backend server")
        return False
    else:
        print("[OK] All required environment variables are configured!")
        print()
        print("Next steps:")
        print("  1. Make sure your backend server is running")
        print("  2. Create a job from the frontend or via API")
        print("  3. Check the job details to see leads")
        return True

def test_import():
    """Test if the GoogleSearchSource can be imported and initialized"""
    print()
    print("=" * 60)
    print("Testing GoogleSearchSource Import")
    print("=" * 60)
    print()
    
    try:
        from app.sources.google_search import GoogleSearchSource
        from app.core.config import settings
        
        print("[OK] GoogleSearchSource imported successfully")
        
        # Try to initialize (will fail if keys are missing, which is expected)
        try:
            source = GoogleSearchSource()
            print("[OK] GoogleSearchSource initialized successfully")
            return True
        except ValueError as e:
            print(f"[!] GoogleSearchSource initialization failed: {e}")
            print("   This is expected if environment variables are not set")
            return False
        except Exception as e:
            print(f"[X] Unexpected error: {e}")
            return False
            
    except ImportError as e:
        print(f"[X] Failed to import GoogleSearchSource: {e}")
        return False

if __name__ == "__main__":
    env_ok = check_env_setup()
    import_ok = test_import()
    
    print()
    print("=" * 60)
    if env_ok and import_ok:
        print("[OK] Setup verification PASSED - Ready to use!")
        sys.exit(0)
    else:
        print("[!] Setup verification found issues - Please fix them above")
        sys.exit(1)

