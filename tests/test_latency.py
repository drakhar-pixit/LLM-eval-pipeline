from datetime import datetime
from dateutil import parser

# Test with sample timestamps from your data
timestamp_user = "2025-11-16T17:06:58.000000Z"
timestamp_ai = "2025-11-16T17:07:10.000000Z"

time_user = parser.parse(timestamp_user)
time_ai = parser.parse(timestamp_ai)

latency_seconds = (time_ai - time_user).total_seconds()
latency_ms = latency_seconds * 1000

print(f"User message: {timestamp_user}")
print(f"AI response:  {timestamp_ai}")
print(f"Latency: {latency_seconds}s = {latency_ms}ms")
print(f"\n✅ This is the AGENT's response time, not our evaluation time")
