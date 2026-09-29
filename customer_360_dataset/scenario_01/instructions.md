# Scenario Data Package

This package contains a simulated event stream for one customer account.

- `entities.json` — customer and account reference data.
- `history_seed.jsonl` — historical events preceding the live window. Load this
  before processing the live stream.
- `live_stream.jsonl` — the live event stream, to be consumed in event_time order.
- `replay_config.json` — pacing configuration if you are replaying this as a
  timed stream rather than reading the file directly.

Follow the event schema exactly as documented separately. Your system is
expected to emit its own inferred-state and action outputs in the required
inferred-events schema as it processes the stream.
