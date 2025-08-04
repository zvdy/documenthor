#!/usr/bin/env python3
"""
Test script for Documenthor
"""

import requests
import json
from pathlib import Path

def test_ollama_connection(host="http://localhost:11434"):
    """Test connection to Ollama"""
    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json()
        print(f"✅ Connected to Ollama at {host}")
        print(f"Available models: {len(models.get('models', []))}")
        for model in models.get('models', []):
            print(f"  - {model['name']}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        return False

def test_model_generation(host="http://localhost:11434", model="codellama:7b"):
    """Test model generation"""
    try:
        url = f"{host}/api/generate"
        payload = {
            "model": model,
            "prompt": "Write a simple hello world function in Python",
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Model {model} is working")
        print("Sample output:")
        print(result.get("response", "")[:200] + "...")
        return True
        
    except Exception as e:
        print(f"❌ Model generation failed: {e}")
        return False

def test_documenthor_script():
    """Test the documenthor script"""
    try:
        import subprocess
        
        # Test listing models
        result = subprocess.run([
            "python", "documentator.py", "--list-models"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Documenthor script is working")
            print("Output:", result.stdout.strip())
            return True
        else:
            print(f"❌ Documenthor script failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing documenthor script: {e}")
        return False

def main():
    print("🧪 Testing Documenthor Setup\n")
    
    # Test Ollama connection
    print("1. Testing Ollama connection...")
    ollama_ok = test_ollama_connection()
    print()
    
    if not ollama_ok:
        print("Please ensure Ollama is running and accessible")
        return
    
    # Test model generation
    print("2. Testing model generation...")
    model_ok = test_model_generation()
    print()
    
    # Test documenthor script
    print("3. Testing documenthor script...")
    script_ok = test_documenthor_script()
    print()
    
    # Summary
    print("📊 Test Summary:")
    print(f"  Ollama Connection: {'✅' if ollama_ok else '❌'}")
    print(f"  Model Generation: {'✅' if model_ok else '❌'}")
    print(f"  Documenthor Script: {'✅' if script_ok else '❌'}")
    
    if all([ollama_ok, model_ok, script_ok]):
        print("\n🎉 All tests passed! Documenthor is ready to use.")
    else:
        print("\n❌ Some tests failed. Please check the setup.")

if __name__ == "__main__":
    main()
