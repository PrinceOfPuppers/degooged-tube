from pathlib import Path
import os
from typing import Tuple

def createPath(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def getTerminalSize() -> Tuple[int,int]:
    size = os.get_terminal_size()
    return(size.columns, size.lines)
