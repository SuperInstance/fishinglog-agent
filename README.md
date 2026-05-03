# PLATO Fishing Log Agent - Captain's Mate for fishinglog.ai

A git-agent pattern for fishing logs. Every fishing session is a committed tile to PLATO.

## Features

- **Sonar data logging** → writes functional tiles to PLATO
- **Natural language queries** → "where were tuna last Tuesday?" → answer from PLATO
- **Session tracking** → each fishing trip is a committed tile with location, depth, species, catch
- **Vessel accumulation** → learns from past sessions over time

## Architecture

- **PLATO room**: `fishinglog-ai` — stores all fishing tiles
- **Tile schema**: timestamp, latitude, longitude, depth_meters, species, catch_count, session_id, notes
- **Agent pattern**: git-agent writes tiles, reads tiles to answer questions

## Quick Start

```bash
pip install fishinglog-agent
```

### Log a fishing session

```python
from fishinglog_agent import FishingLogAgent

agent = FishingLogAgent()
agent.log_session(
    latitude=41.5,
    longitude=-71.3,
    depth_meters=45,
    species="tuna",
    catch_count=12,
    notes="Good catch near the shipping lanes"
)
```

### Query past catches

```python
# Where were tuna last Tuesday?
results = agent.query(species="tuna", days_back=7)

# What species at this location?
results = agent.query(latitude=41.5, longitude=-71.3, radius_km=5)
```

## Development

```bash
git clone https://github.com/SuperInstance/fishinglog-agent.git
cd fishinglog-agent
pip install -e .
pytest
```

## License

MIT