import os
import re

def search_for_hex_keys(directory="."):
    print("🔎 SCANNING FOR 32-BYTE (256-BIT) CRYPTO KEYS...")
    # Looking for exactly 64 hex characters in a row
    regex = r'[0-9a-fA-F]{64}'
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.md', '.txt')):
                path = os.path.join(root, file)
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
                    matches = re.findall(regex, content)
                    for match in matches:
                        print(f"✅ FOUND POTENTIAL KEY in {file}:")
                        print(f"   {match}")

search_for_hex_keys()
