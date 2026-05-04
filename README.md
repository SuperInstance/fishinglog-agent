# Fishing Log Agent — Captain's Mate

> PLATO-enabled fishing log agent. Logs sessions, detects hot spots, queries history.

## Installation

```bash
pip install fishinglog-agent
```

## Usage

```python
from fishinglog_agent import FishingLogAgent

agent = FishingLogAgent()

# Log a fishing session
agent.log_session(
    latitude=41.5,
    longitude=-71.3,
    depth_meters=45,
    species="tuna",
    catch_count=12,
    notes="Good action on the tide change"
)

# Query recent sessions
recent = agent.get_recent_sessions(limit=10)
for session in recent:
    print(f"{session['species']}: {session['catch_count']} at {session['latitude']}N")

# Detect hot spots using H1 emergence detection
hot_spots = agent.detect_hot_spots(species="tuna")
for spot in hot_spots:
    print(f"Hot spot at {spot['lat']}, {spot['lon']} (score: {spot['score']})")
```

## Features

- **PLATO integration** — sessions stored as tiles in `fishinglog-ai` room
- **H1 emergence detection** — fleet_math EmergenceDetector finds hot spots
- **Query by species/location/time** — flexible historical queries
- **Voice-ready** — compatible with PLATO Voice interface

## PLATO Room

Tiles are stored in `fishinglog-ai` room on the fleet PLATO server.

## Requirements

- Python 3.10+
- fleet-agent >= 0.2.0
- requests >= 2.31.0

## License

MIT
