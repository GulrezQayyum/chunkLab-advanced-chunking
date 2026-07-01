#!/usr/bin/env python3
"""
Quick diagnostic script to identify why Flutter queries are failing.
Run this when you get "query failed" errors.

Usage:
    python diagnose_query_failed.py
"""

import subprocess
import socket
import json
import sys

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def check_port(port=8001):
    """Check if port is in use."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def run_command(cmd, shell=False):
    """Run command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("\n" + "="*60)
    print("🔧 ChunkLab: Query Failed Diagnostic Tool")
    print("="*60)
    
    issues = []
    
    # Check 1: Backend running
    print_section("Check 1: Is Backend Running?")
    if check_port(8001):
        print("✅ Port 8001 is in use (backend likely running)")
    else:
        print("❌ Port 8001 is NOT in use (backend not running)")
        issues.append("Backend not running on port 8001")
        print("\nFix: Start the backend with:")
        print("  cd ~/Advanced-RAG-Project/chunkLab/app/")
        print("  python main.py")
    
    # Check 2: Backend responds
    print_section("Check 2: Backend Health Check")
    success, stdout, stderr = run_command(
        'curl -s http://localhost:8001/api/documents/health'
    )
    
    if success and '{"status"' in stdout:
        print("✅ Backend is responding")
        try:
            data = json.loads(stdout)
            print(f"   Status: {data.get('status')}")
        except:
            pass
    else:
        print("❌ Backend is NOT responding")
        issues.append("Backend health check failed")
        if stderr:
            print(f"   Error: {stderr}")
    
    # Check 3: Collections exist
    print_section("Check 3: ChromaDB Collections")
    success, stdout, stderr = run_command([
        'python', '-c',
        '''
import chromadb
client = chromadb.Client()
collections = [c.name for c in client.list_collections()]
for name in collections:
    col = client.get_collection(name)
    print(f"{name}: {col.count()} documents")
if not collections:
    print("NO_COLLECTIONS")
        '''
    ])
    
    if success:
        if "NO_COLLECTIONS" in stdout:
            print("❌ No collections found in ChromaDB")
            issues.append("No ChromaDB collections (need to ingest)")
            print("\nFix: Ingest data with:")
            print("  cd ~/Advanced-RAG-Project/chunkLab/app/")
            print("  python ingest_meditations.py")
            print("  python ingest_meditations_semantic.py")
        else:
            print("✅ Collections found:")
            for line in stdout.strip().split('\n'):
                if line:
                    print(f"   {line}")
    else:
        print("❌ Could not check collections")
        issues.append("Could not check ChromaDB")
        if stderr:
            print(f"   Error: {stderr}")
    
    # Check 4: Simulate query
    print_section("Check 4: Test Query")
    success, stdout, stderr = run_command(
        'curl -s -X POST http://localhost:8001/api/documents/query?strategy=parent_child '
        '-H "Content-Type: application/json" '
        '-d \'{"query":"virtue","n_results":5,"return_parents":true}\''
    )
    
    if success and '"strategy"' in stdout:
        print("✅ Query endpoint working")
        try:
            data = json.loads(stdout)
            print(f"   Strategy: {data.get('strategy')}")
            print(f"   Results: {data.get('total_results')}")
            print(f"   Avg Similarity: {data.get('metrics', {}).get('avg_similarity', 'N/A')}")
        except:
            pass
    else:
        print("❌ Query endpoint NOT working")
        issues.append("Query endpoint failed")
        if "Connection refused" in stderr or not success:
            print("   → Backend not running (see Check 1)")
        elif "Collection" in stderr and "not found" in stderr:
            print("   → Collections don't exist (see Check 3)")
        else:
            print(f"   Error: {stderr if stderr else stdout}")
    
    # Check 5: Check for common issues
    print_section("Check 5: Common Configuration Issues")
    
    # Try to read constants
    constants_file = "chunklab_flutter/lib/config/constants.dart"
    try:
        with open(constants_file, 'r') as f:
            content = f.read()
            if "localhost" in content:
                if "10.0.2.2" in content:
                    print("⚠️  Found both localhost and 10.0.2.2")
                    print("   Make sure to use 10.0.2.2 for Android emulator")
                elif "8001" in content:
                    print("✅ Constants file looks correct (localhost:8001)")
                else:
                    print("⚠️  Port 8001 not found in constants")
            else:
                print("❌ 'localhost' not found in constants.dart")
                issues.append("Wrong URL in constants.dart")
    except FileNotFoundError:
        print(f"⚠️  Could not find {constants_file}")
        print("   Make sure you're running from project root")
    
    # Summary
    print_section("Summary")
    
    if not issues:
        print("✅ Everything looks good!")
        print("\nIf you're still getting 'query failed', try:")
        print("  1. flutter clean")
        print("  2. flutter pub get")
        print("  3. flutter run")
    else:
        print(f"❌ Found {len(issues)} issue(s):\n")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
        
        print("\nStep-by-step fixes:")
        if "Backend not running" in issues:
            print("\n📍 Priority 1: Start backend")
            print("   cd ~/Advanced-RAG-Project/chunkLab/app/")
            print("   python main.py")
        
        if "No ChromaDB collections" in issues:
            print("\n📍 Priority 2: Ingest data")
            print("   cd ~/Advanced-RAG-Project/chunkLab/app/")
            print("   python ingest_meditations.py")
            print("   python ingest_meditations_semantic.py")
        
        if "Wrong URL in constants.dart" in issues:
            print("\n📍 Priority 3: Fix Flutter constants")
            print("   Edit: chunklab_flutter/lib/config/constants.dart")
            print("   Use: http://10.0.2.2:8001 (Android) or http://localhost:8001 (iOS)")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Diagnostic error: {e}")
        print("   Check that you're in the right directory")
        sys.exit(1)