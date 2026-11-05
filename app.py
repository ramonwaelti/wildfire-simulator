#Wildfire: a small, fictional firebreak strategy game built with Flask
import json
import random
import secrets
from pathlib import Path
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)  #local demo; new secret each server restart.

SIZE = 20
HOUSE = (10, 14)
START_FIRE = [(9, 2), (10, 2), (11, 2)]
CLEARINGS = 20  #5% of 400 cells.
BUDGET = 12
ACTIONS_PER_ROUND = 3
WINDS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
WIND_LABELS = ['E →', 'S ↓', 'W ←', 'N ↑']
GAMES = {}  #game state for the local demo.
SCORE_FILE = Path(__file__).resolve().parent / 'highscore.json'


def load_highscore():
    #read the best score, or return zero for a new installation
    try:
        return int(json.loads(SCORE_FILE.read_text(encoding='utf-8'))['score'])
    except (FileNotFoundError, ValueError, KeyError, TypeError):
        return 0


def calculate_score(game):
    #Reward surviving forest and unused firebreaks after a victory
    trees = sum(cell == 'tree' for row in game['board'] for cell in row)
    return trees * 10 + game['budget'] * 20


def save_highscore(score):
    #Keep the best result across new games and server restarts
    if score > load_highscore():
        SCORE_FILE.write_text(json.dumps({'score': score}) + '\n', encoding='utf-8')
        return True
    return False


def create_forest():
    #Create a new forest with a cabin, three flames, and 20 random clearings
    board = [['tree' for _ in range(SIZE)] for _ in range(SIZE)]
    reserved = {HOUSE, *START_FIRE}
    positions = [(r, c) for r in range(SIZE) for c in range(SIZE)
                 if (r, c) not in reserved]
    for r, c in random.sample(positions, CLEARINGS):
        board[r][c] = 'empty'
    for r, c in START_FIRE:
        board[r][c] = 'fire'
    board[HOUSE[0]][HOUSE[1]] = 'house'
    return {'board': board, 'round': 0, 'budget': BUDGET, 'actions': 0,
            'wind': 0, 'status': 'playing', 'message': '',
            'seed': random.randrange(1_000_000_000), 'score': None,
            'new_record': False}


def get_neighbors(row, col):
    #Return orthogonal neighbors and their direction, skipping outer borders
    for dr, dc in WINDS:
        nr, nc = row + dr, col + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            yield nr, nc, (dr, dc)


def place_firebreak(game, row, col):
    #Spend one resource to remove a tree; no construction next to the cabin
    if game['status'] != 'playing':
        return
    if game['budget'] == 0:
    game['message'] = 'No firebreaks left.'
        return
    if game['actions'] >= ACTIONS_PER_ROUND:
        game['message'] = 'No actions left this round.'
        return
    if not (0 <= row < SIZE and 0 <= col < SIZE):
        return
    if max(abs(row - HOUSE[0]), abs(col - HOUSE[1])) <= 2:
        game['message'] = 'Build firebreaks farther from the cabin.'
        return
    if game['board'][row][col] != 'tree':
        game['message'] = 'Only forest cells can become firebreaks.'
        return
    game['board'][row][col] = 'break'
    game['budget'] -= 1
    game['actions'] += 1
    game['message'] = ''


def spread_fire(game):
    #Burn existing flames out; ignite neighbors from the previous board only
    old = game['board']
    new = [row[:] for row in old]
    rng = random.Random(game['seed'] + game['round'])
    wind = WINDS[game['wind']]
    for r in range(SIZE):
        for c in range(SIZE):
            if old[r][c] != 'fire':
                continue
            new[r][c] = 'burned'
            for nr, nc, direction in get_neighbors(r, c):
                if old[nr][nc] not in ('tree', 'house'):
                    continue
                probability = (0.88 if direction == wind else
                               0.36 if direction == (-wind[0], -wind[1]) else 0.66)
                if rng.random() < probability:
                    new[nr][nc] = 'lost' if old[nr][nc] == 'house' else 'fire'
    game['board'] = new
    game['round'] += 1
    game['actions'] = 0
    if game['round'] % 3 == 0:
        game['wind'] = (game['wind'] + 1) % 4
    if new[HOUSE[0]][HOUSE[1]] == 'lost':
        game['status'] = 'lost'
        game['message'] = 'The cabin burned down.'
    elif not any(cell == 'fire' for row in new for cell in row):
        game['status'] = 'won'
        game['score'] = calculate_score(game)
        game['new_record'] = save_highscore(game['score'])
        game['message'] = 'The fire is out. The cabin is safe.'
    else:
        game['message'] = ''


@app.route('/', methods=['GET', 'POST'])
def index():
    #show the board and process one button click per request
    game_id = session.get('game_id')
    if game_id not in GAMES:
        game_id = secrets.token_hex(12)
        session['game_id'] = game_id
        GAMES[game_id] = create_forest()
    game = GAMES[game_id]
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'reset':
            GAMES[game_id] = create_forest()
        elif action == 'next' and game['status'] == 'playing':
            spread_fire(game)
        elif action == 'cut':
            try:
                place_firebreak(game, int(request.form['row']), int(request.form['col']))
            except (ValueError, KeyError):
                pass
        return redirect(url_for('index'))
    active = sum(cell == 'fire' for row in game['board'] for cell in row)
    burned = sum(cell == 'burned' for row in game['board'] for cell in row)
    saved_trees = sum(cell == 'tree' for row in game['board'] for cell in row)
    return render_template('index.html', game=game, active=active,
                           saved_trees=saved_trees, burned=burned,
                           house_row=HOUSE[0], house_col=HOUSE[1], highscore=load_highscore(),
                           wind=WIND_LABELS[game['wind']],
                           limit=ACTIONS_PER_ROUND, size=SIZE)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
