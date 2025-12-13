#!/usr/bin/env python3
import json
import re
import sys

def clean_json(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Remove comments
    content = re.sub(r'//[^\n]*', '', content)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Remove trailing commas
    content = re.sub(r',\s*([}\]])', r'\1', content)
    
    # Remove control characters
    content = ''.join(c if ord(c) >= 32 or c in '\n\t\r' else ' ' for c in content)
    
    data = json.loads(content)
    return json.dumps(data, ensure_ascii=False)

if __name__ == '__main__':
    print(clean_json(sys.argv[1]))
