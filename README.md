# WILDFIRE — Flask project

A simple fictional strategy game. Protect the cabin until the fire stops.

## Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 (stop other apps using this address first).

## Rules

- 20×20 forest cells; exactly 20 randomly selected clearings (5%).
- Click green trees to create a firebreak. A firebreak blocks spreading fire.
- 12 total resources; at most 3 cuts each round.
- Cells within 2 steps of the cabin are restricted and visibly striped.
- Click **Next round** to spread fire; the wind turns every third round.
- You win if all fires burn out and the cabin survives, and lose if the cabin burns.
- After a win: **score = surviving trees × 10 + unspent resources × 20**.
- The high score is saved locally in `highscore.json` (created after the first win).

## Code in brief

`create_forest()` builds the grid; `get_neighbors()` finds adjacent cells; `place_firebreak()` handles clicks; `spread_fire()` advances the fire; `calculate_score()` adds points; `index()` handles Flask requests.

This is a teaching game, **not** a scientifically validated wildfire model. The game state is kept in server memory and is lost when Flask restarts; the record score survives. This is intended for local demos only.
