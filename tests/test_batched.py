import asyncio
import time

async def evaluate_turn(turn_id):
    """Simulates evaluating one turn"""
    await asyncio.sleep(9)
    return f"Turn {turn_id} done"

async def process_in_batches(turns, batch_size=5):
    """Process turns in batches to avoid overwhelming the system"""
    results = []
    
    for i in range(0, len(turns), batch_size):
        batch = turns[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}: turns {batch}")
        
        # Process this batch in parallel
        batch_results = await asyncio.gather(*[evaluate_turn(t) for t in batch])
        results.extend(batch_results)
    
    return results

async def test():
    turns = list(range(1, 21))  # 20 turns
    
    print(f"Total turns: {len(turns)}\n")
    
    # Fully parallel (all at once)
    print("=== Fully Parallel (all 20 at once) ===")
    start = time.time()
    await asyncio.gather(*[evaluate_turn(t) for t in turns])
    print(f"Time: {time.time() - start:.1f}s\n")
    
    # Batched (5 at a time)
    print("=== Batched (5 at a time) ===")
    start = time.time()
    await process_in_batches(turns, batch_size=5)
    print(f"Time: {time.time() - start:.1f}s")
    print(f"Batches: 4 batches × 9s = 36s")

asyncio.run(test())
