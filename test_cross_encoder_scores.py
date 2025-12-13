#!/usr/bin/env python3
import json
from sentence_transformers import CrossEncoder
import numpy as np
import re

print("Loading: cross-encoder/nli-deberta-v3-small")
model = CrossEncoder("cross-encoder/nli-deberta-v3-small")
print("Loaded!\n")

with open('test_payload.json', 'r') as f:
    data = json.load(f)

vector_data = data['context_vectors']['data']['vector_data']
context_vectors = [vec['text'] for vec in vector_data[:3]]

print(f"Context vectors: {len(context_vectors)}\n")

ai_turns = [t for t in data['conversation']['conversation_turns'] if t['role'] == 'AI/Chatbot']

results = []

for ai_turn in ai_turns:
    turn_num = ai_turn['turn']
    ai_response = ai_turn['message']
    
    print(f"\nTURN {turn_num}: {ai_response[:100]}...")
    
    sentences = re.split(r'[.!?]+', ai_response)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    sentence_scores = []
    for sentence in sentences:
        max_score = 0
        for context in context_vectors:
            # NLI model returns [entailment, neutral, contradiction]
            scores = model.predict([(context, sentence)])[0]
            entailment_score = scores[0]  # First score is entailment
            # Convert to 0-1 scale
            score = 1 / (1 + np.exp(-entailment_score))
            max_score = max(max_score, score)
        sentence_scores.append(max_score)
        print(f"  {max_score:.3f} - {sentence[:60]}...")
    
    avg_confidence = np.mean(sentence_scores) if sentence_scores else 0.0
    is_hallucination = turn_num == 14
    
    print(f"  → Avg: {avg_confidence:.3f} {'[HALLUCINATION]' if is_hallucination else ''}")
    
    results.append({
        'turn': turn_num,
        'confidence': avg_confidence,
        'is_hallucination': is_hallucination
    })

print("\n" + "="*80)
print("THRESHOLD ANALYSIS")
print("="*80)

for threshold in [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6]:
    llm_calls = sum(1 for r in results if r['confidence'] < threshold)
    caught = sum(1 for r in results if r['is_hallucination'] and r['confidence'] < threshold)
    false_pos = sum(1 for r in results if not r['is_hallucination'] and r['confidence'] < threshold)
    
    print(f"Threshold {threshold:.2f}: {llm_calls}/{len(results)} LLM calls, caught {caught}/1 hallucinations, {false_pos} false positives")
