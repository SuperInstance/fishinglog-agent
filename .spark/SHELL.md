# Spark Shell — fishinglog-agent

## Protocol
Version: 1.0 | Storage: `.spark/` directory (git-tracked)

## What is fishinglog-agent
Tracks fishing operations, catch data, weather conditions, and crew activities.
Part of the Cocapn Fleet — fleet coordination via PLATO, deployment via greenhorn-runtime.

## Rooms
- **domain/** — what this agent does
- **lessons/** — what happened (fishing seasons, patterns)
- **active/** — what's happening now
- **decisions/** — choices made (route planning, catch handling)
- **questions/** — what we don't know

## Connection to Fleet
Bootstrap Spark → Bootstrap Bomb → PLATO → greenhorn → fishinglog-agent

See: github.com/SuperInstance/fishinglog-agent
