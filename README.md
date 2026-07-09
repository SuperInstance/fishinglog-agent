# Fishing Log Agent — Captain's Mate

A Python client for logging fishing sessions to a PLATO server and querying
them back by species, recency, or location, with a simple natural-language
question interface. Requires a live PLATO server — see "Requirements" below.

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

# Query sessions by species, recency, or location
recent = agent.query(species="tuna", days_back=7)
for session in recent:
    content = session["content"]
    print(f"{content['species']}: {content['catch_count']} at {content['latitude']}N")

# Ask a natural-language question (keyword matching + summarization, not NLP)
answer = agent.query_natural_language("where were tuna last week?")
print(answer)
```

## Features

- **PLATO integration** — sessions stored as tiles in the `fishinglog-ai` room
- **Query by species/location/time** — filter past sessions by any combination
- **Natural-language Q&A** — `query_natural_language()` matches known species
  and time-range keywords (e.g. "yesterday", "last week") and summarizes the
  matching sessions; it does not do general-purpose language understanding
- **Distance filtering** — when latitude and longitude are supplied, tiles are
  filtered by a planar distance approximation (flat-earth, ~111 km per degree
  latitude and ~85 km per degree longitude) against a `radius_km` threshold

## PLATO Room

Tiles are stored in the `fishinglog-ai` room on a PLATO server you run or
point this client at (`plato_url`, default `http://localhost:8847`).

PLATO is the SuperInstance sketchbook's shared tile-server memory: a **room**
is a named collection on the server, a **tile** is one JSON record in it.
Sibling clients of the same protocol:
[activeledger-agent](https://github.com/SuperInstance/activeledger-agent),
[reallog-agent](https://github.com/SuperInstance/reallog-agent).

## Requirements

- Python 3.10+
- requests >= 2.31.0
- A reachable PLATO server — this package is a client only; it does not
  ship or run PLATO itself

## License

MIT
