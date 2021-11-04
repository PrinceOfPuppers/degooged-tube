from typing import List, Union
from enum import Enum
from dataclasses import dataclass
import degooged_tube.config as cfg


def scrapeJson(j, desiredKey: str, results:List):
    if isinstance(j,List):
        for value in j:
            if isinstance(value,List) or isinstance(value,dict):
                scrapeJson(value, desiredKey, results)
        return

    if isinstance(j, dict):
        for key,value in j.items():
            if key == desiredKey:
                results.append(value)
            elif isinstance(value, dict) or isinstance(value, List):
                scrapeJson(value, desiredKey, results)
        return

def scrapeFirstJson(j, desiredKey: str):
    if isinstance(j,List):
        for value in j:
            if isinstance(value,List) or isinstance(value,dict):
                res = scrapeFirstJson(value, desiredKey)
                if res is not None:
                    return res
        return None

    if isinstance(j, dict):
        for key,value in j.items():
            if key == desiredKey:
                return value
            elif isinstance(value, dict) or isinstance(value, List):
                res = scrapeFirstJson(value, desiredKey)
                if res is not None:
                    return res
        return None

    return None



class ScrapeNum(Enum):
    First = 1
    All = 2
    Longest = 3
    Unique = 4

@dataclass()
class ScrapeNode:
    key: str
    scrapeNum: ScrapeNum
    children: list

    collapse: bool = False
    rename: str = ""

    def _strIndent(self, numIndent):
        indent = numIndent*'  '
        indentp1 = indent + '  '
        return f"{indent}ScrapeNode(\n{indentp1}key: {self.key}\n{indentp1}ScrapeNum: {self.scrapeNum}\n{indentp1}children:\n" + \
                "\n".join([child._strIndent(numIndent+2) for child in self.children]) + \
                f"\n{indent})"

    def __repr__(self):
        return self._strIndent(0)

    def __str__(self):
        return self.__repr__()

def _put(src, dest: Union[list, dict], key: Union[str,None] = None):
    if type(dest) is list:
        dest.append(src)
        return

    elif type(dest) is dict:
        if key == None:
            cfg.logger.error("Key Required")
            return

        dest[key] = src


def _scrapeJsonTree(j, base: ScrapeNode, result: Union[dict, list], parentKey: str = None):
    # if parent key is provided, put data under parents key
    if parentKey == None:
        if base.rename:
            putKey = base.rename
        else:
            putKey = base.key
    else:
        putKey = parentKey

    if base.scrapeNum == ScrapeNum.First: 
        data = scrapeFirstJson(j, base.key)

        if data is None:
            cfg.logger.error(f"Missing Field in JSON: {base.key}")
            return

        if len(base.children) == 0:
            _put(data, result, putKey)
            return

        for child in base.children:
            if child.collapse:
                _scrapeJsonTree(data, child, result, putKey)
            else:
                x = {}
                _scrapeJsonTree(data, child, x)
                _put(x, result, putKey)

    else: # all, unique and longest
        data = []
        scrapeJson(j, base.key, data)

        if len(base.children) == 0:
            _put(data, result, putKey)
            return

        x = []
        for datum in data:
            y = {}

            for child in base.children:
                if child.collapse:
                    _scrapeJsonTree(datum, child, x, putKey)
                else:
                    _scrapeJsonTree(datum, child, y)

            if len(y) != 0: 
                x.append(y)

        if base.scrapeNum == ScrapeNum.Longest and len(x)!=0:
            _put(max(x, key=len), result, putKey)

        elif base.scrapeNum == ScrapeNum.Unique:
            if result not in x:
                _put(x, result, putKey)
        else:
            _put(x, result, putKey)


def scrapeJsonTree(j, base: ScrapeNode):
    result = {}
    _scrapeJsonTree(j, base, result)

    if base.collapse:
        return result[base.key]

    return result

