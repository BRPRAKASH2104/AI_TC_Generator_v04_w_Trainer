import sys

import requests

BASE_URL = "http://127.0.0.1:11434"

import pytest

@pytest.mark.skip(reason="Not a standard pytest test")

def test_version():
    print("Testing /api/version...")
    try:
        resp = requests.get(f"{BASE_URL}/api/version")
        resp.raise_for_status()
        print(f"Success: {resp.json()}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

@pytest.mark.skip(reason="Not a standard pytest test")
def test_tags():
    print("\nTesting /api/tags...")
    try:
        resp = requests.get(f"{BASE_URL}/api/tags")
        resp.raise_for_status()
        models = resp.json().get("models", [])
        print(f"Success: Found {len(models)} models")
        if models:
            return models[0]["name"]
        return None
    except Exception as e:
        print(f"Failed: {e}")
        return None

@pytest.mark.skip(reason="Not a standard pytest test")
def test_generate(model_name):
    print(f"\nTesting /api/generate with model '{model_name}'...")
    payload = {
        "model": model_name,
        "prompt": "Hello, are you working?",
        "stream": False,
        "options": {
            "temperature": 0
        }
    }
    try:
        resp = requests.post(f"{BASE_URL}/api/generate", json=payload)
        resp.raise_for_status()
        res = resp.json()
        print(f"Success: Response length {len(res.get('response', ''))}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

def main():
    if not test_version():
        sys.exit(1)

    model_name = test_tags()
    if not model_name:
        print("No models found to test generation.")
        sys.exit(1)

    if not test_generate(model_name):
        sys.exit(1)

    print("\nAll compatibility tests passed!")

if __name__ == "__main__":
    main()
