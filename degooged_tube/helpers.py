from pathlib import Path

def createPath(path):
    Path(path).mkdir(parents=True, exist_ok=True)

