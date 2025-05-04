import os, pickle
SAVE_DIR = "saves"

def _path(user: str):                       # create dir on first use
    os.makedirs(SAVE_DIR, exist_ok=True)
    return os.path.join(SAVE_DIR, f"{user}.pkl")

def save_game(state: dict, user: str):
    with open(_path(user), "wb") as f:
        pickle.dump(state, f)

def load_game(user: str):
    try:
        with open(_path(user), "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None

def delete_game(user: str):
    try: os.remove(_path(user))
    except FileNotFoundError: pass

def list_users():
    if not os.path.isdir(SAVE_DIR): return []
    return [f[:-4] for f in os.listdir(SAVE_DIR) if f.endswith(".pkl")]
