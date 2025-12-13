import json

with open('data/sample_context_vectors-01.json', 'r') as f:
    ctx = json.load(f)

vector_data = ctx['data'].get('vector_data', [])
context_texts = [vec.get("text", "") for vec in vector_data if vec.get("text")]

print(f"✅ Successfully extracted {len(context_texts)} context texts (filtered out {len(vector_data) - len(context_texts)} without text)")
print(f"First text preview: {context_texts[0][:100]}...")
