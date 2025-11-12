"""
APIテストスクリプト
"""
import requests
import json
import time
from pathlib import Path

API_URL = "http://localhost:8000"

def test_health():
    """ヘルスチェック"""
    print("Testing health endpoint...")
    response = requests.get(f"{API_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_generate():
    """歌詞生成テスト"""
    print("Testing lyrics generation...")
    payload = {
        "theme": "love",
        "style": "rap",
        "bpm": 120,
        "key": "C"
    }
    response = requests.post(f"{API_URL}/generate", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Title: {result['song']['title']}")
        print(f"BPM: {result['song']['bpm']}, Key: {result['song']['key']}")
        print("Lyrics:")
        for line in result['song']['lyrics'][:8]:  # 最初の8行のみ表示
            print(f"  {line}")
    else:
        print(f"Error: {response.text}")
    print()

def test_compose():
    """作曲テスト"""
    print("Testing composition (this may take a while)...")
    payload = {
        "prompt": {
            "theme": "party",
            "style": "rap",
            "bpm": 140,
            "key": "Am"
        },
        "output_filename": "test_song.mp3"
    }
    
    start_time = time.time()
    response = requests.post(f"{API_URL}/compose", json=payload)
    elapsed = time.time() - start_time
    
    print(f"Status: {response.status_code}")
    print(f"Time elapsed: {elapsed:.2f} seconds")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Generated: {result['filename']}")
        print(f"Download URL: {result['download_url']}")
        
        # ダウンロード
        download_url = f"{API_URL}{result['download_url']}"
        mp3_response = requests.get(download_url)
        
        if mp3_response.status_code == 200:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / result['filename']
            with open(output_path, 'wb') as f:
                f.write(mp3_response.content)
            print(f"Downloaded to: {output_path}")
            print(f"File size: {output_path.stat().st_size / 1024:.2f} KB")
        else:
            print(f"Download failed: {mp3_response.status_code}")
    else:
        print(f"Error: {response.text}")
    print()

def test_list():
    """ファイルリスト取得テスト"""
    print("Testing file list...")
    response = requests.get(f"{API_URL}/list")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Total files: {result['count']}")
        for file_info in result['files'][:5]:  # 最初の5ファイルのみ表示
            print(f"  - {file_info['filename']} ({file_info['size'] / 1024:.2f} KB)")
    else:
        print(f"Error: {response.text}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("AI Rapper API Test Suite")
    print("=" * 50)
    print()
    
    try:
        test_health()
        test_generate()
        test_compose()
        test_list()
        
        print("=" * 50)
        print("All tests completed!")
        print("=" * 50)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Is the server running?")
        print("Start the server with: docker-compose up")
    except Exception as e:
        print(f"Error: {e}")

