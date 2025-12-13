import asyncio
import time

# Current approach (Sequential)
async def evaluate_sequential(turns):
    results = []
    for turn in turns:
        await asyncio.sleep(9)  # Simulates 9s per turn
        results.append(f"Turn {turn}")
    return results

# Optimized approach (Parallel)
async def evaluate_parallel(turns):
    tasks = [asyncio.sleep(9) for turn in turns]  # All at once
    await asyncio.gather(*tasks)
    return [f"Turn {turn}" for turn in turns]

async def test():
    turns = [1, 2, 3, 4, 5, 6]
    
    # Sequential
    start = time.time()
    await evaluate_sequential(turns)
    seq_time = time.time() - start
    print(f"Sequential: {seq_time:.1f}s (6 turns × 9s)")
    
    # Parallel
    start = time.time()
    await evaluate_parallel(turns)
    par_time = time.time() - start
    print(f"Parallel: {par_time:.1f}s (all at once)")
    print(f"Speedup: {seq_time/par_time:.1f}x faster")

asyncio.run(test())
