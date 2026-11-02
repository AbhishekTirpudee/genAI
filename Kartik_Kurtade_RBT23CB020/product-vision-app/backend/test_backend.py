"""
Quick test to verify the backend is set up correctly.
Run from the backend/ folder: python test_backend.py
"""
import os
import sys

def check_env():
    print("Checking environment...\n")

    # Check .env
    if os.path.exists('.env'):
        print("✅ .env file found")
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv('GEMINI_API_KEY')
        if key and key != 'your_gemini_api_key_here':
            print("✅ GEMINI_API_KEY is set")
        else:
            print("❌ GEMINI_API_KEY is not set or still has placeholder value")
            print("   Please edit backend/.env and add your actual API key")
            sys.exit(1)
    else:
        print("❌ .env file not found")
        print("   Copy .env.example to .env and add your GEMINI_API_KEY")
        sys.exit(1)

    # Check imports
    try:
        import flask
        print(f"✅ Flask {flask.__version__} installed")
    except ImportError:
        print("❌ Flask not installed. Run: pip install flask flask-cors")
        sys.exit(1)

    try:
        import flask_cors  # noqa
        print("✅ Flask-CORS installed")
    except ImportError:
        print("❌ Flask-CORS not installed. Run: pip install flask-cors")
        sys.exit(1)

    try:
        from google import genai
        from google.genai import types
        print("✅ google-genai SDK installed")

        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        resp = client.models.generate_content(
            model="gemini-3.8-flash",
            contents="Say 'OK' in one word only.",
            config=types.GenerateContentConfig(max_output_tokens=10),
        )
        print(f"✅ Gemini API connection successful! Response: {resp.text.strip()}")

    except ImportError:
        print("❌ google-genai not installed. Run: pip install google-genai")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        sys.exit(1)

    print("\n🎉 All checks passed! You can now run the backend:")
    print("   python app.py")

if __name__ == '__main__':
    check_env()
