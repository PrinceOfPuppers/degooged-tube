from pathlib import Path
import os
from typing import Tuple

def createPath(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def ignoreReturn(x):
    return

def getTerminalSize() -> Tuple[int,int]:
    size = os.get_terminal_size()
    return(size.columns, size.lines)

def paginationCalculator(pageNum, pageSize):
    pageNum = max(1, pageNum)
    limit = pageSize
    offset = (pageNum - 1)*pageSize

    return limit, offset

def sanitizeFileName(f:str):
    return "".join(x for x in f if x not in "\\/:*?<>|")
