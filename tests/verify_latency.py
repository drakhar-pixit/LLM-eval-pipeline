from dateutil import parser

# AI responses with their corresponding user queries
pairs = [
    # Turn 6: User turn 5 → AI turn 6
    ("2025-11-16T17:06:58.000000Z", "2025-11-16T17:07:10.000000Z"),
    # Turn 8: User turn 7 → AI turn 8
    ("2025-11-16T17:09:27.000000Z", "2025-11-16T17:09:39.000000Z"),
    # Turn 10: User turn 9 → AI turn 10
    ("2025-11-16T17:10:49.000000Z", "2025-11-16T17:10:55.000000Z"),
    # Turn 12: User turn 11 → AI turn 12
    ("2025-11-16T20:27:51.000000Z", "2025-11-16T20:27:57.000000Z"),
    # Turn 14: User turn 13 → AI turn 14
    ("2025-11-16T20:42:07.000000Z", "2025-11-16T20:42:16.000000Z"),
    # Turn 18: User turn 17 → AI turn 18
    ("2025-11-16T22:23:17.000000Z", "2025-11-16T22:23:26.000000Z"),
]

latencies = []
print("AI Response Latencies:\n")
for i, (user_time, ai_time) in enumerate(pairs, 1):
    t_user = parser.parse(user_time)
    t_ai = parser.parse(ai_time)
    latency_s = (t_ai - t_user).total_seconds()
    latency_ms = latency_s * 1000
    latencies.append(latency_ms)
    print(f"Turn {i}: {latency_s}s = {latency_ms}ms")

avg_latency = sum(latencies) / len(latencies)
print(f"\n✅ Average Latency: {avg_latency:.1f}ms = {avg_latency/1000:.1f}s")
