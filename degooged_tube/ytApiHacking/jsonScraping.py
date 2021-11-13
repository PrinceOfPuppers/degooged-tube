from typing import List, Union
from enum import Enum
from dataclasses import dataclass
import json
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
    children: list['ScrapeNode']

    collapse: bool = False
    rename: str = ""

    def _strIndent(self, numIndent):
        indent = numIndent*'  '
        indentp1 = indent + '  '
        return f"{indent}ScrapeNode(\n"\
               f"{indentp1}key: {self.key}\n" \
               f"{indentp1}ScrapeNum: {self.scrapeNum}\n" \
               f"{indentp1}rename: {self.rename}\n" \
               f"{indentp1}collapse: {self.collapse}\n" \
               f"{indentp1}children:\n" + \
                    "\n".join([child._strIndent(numIndent+2) for child in self.children]) + \
               f"\n{indent})"

    def __repr__(self):
        return self._strIndent(0)

    def __str__(self):
        return self.__repr__()

    def getKeys(self, result:set[str]):
        for child in self.children:
            child.getKeys(result)

        if self.collapse:
            return

        if self.rename:
            result.add(self.rename)
            return

        result.add(self.key)

    def getOldKeyToNewKeyMap(self, result:dict):
        for child in self.children:
            child.getOldKeyToNewKeyMap(result)

        if self.collapse:
            return

        if self.rename:
            result[self.rename] = self.key
            return

        result[self.key] = self.key


def _put(src, dest: Union[list, dict], keys: set[str], key: Union[str,None] = None):
    if type(dest) is list:
        dest.append(src)
        return

    elif type(dest) is dict:
        if key == None:
            raise KeyError("Key Required")

        if key in dest and type(src) is dict:
            for srcKey in src.keys():
                dest[key][srcKey] = src[srcKey]
            return

        dest[key] = src
        keys.add(key)


def _scrapeJsonTree(j, base: ScrapeNode, result: Union[dict, list], keys: set[str], parentKey: str = None):
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
            logMsg = f"Missing Field in JSON: {base.key}"
            cfg.logger.debug(logMsg)
            return

        if len(base.children) == 0:
            _put(data, result, keys, putKey)
            return

        for child in base.children:
            if child.collapse:
                _scrapeJsonTree(data, child, result, keys, putKey)
            else:
                x = {}
                _scrapeJsonTree(data, child, x, keys)
                _put(x, result, keys, putKey)

    else: # all, unique and longest
        data = []
        scrapeJson(j, base.key, data)

        if len(base.children) == 0:
            _put(data, result, keys, putKey)
            return

        x = []

        for datum in data:
            y = {}

            for child in base.children:
                if child.collapse:
                    _scrapeJsonTree(datum, child, x, keys, putKey)
                else:
                    _scrapeJsonTree(datum, child, y, keys)

            if len(y) != 0: 
                x.append(y)

        if base.scrapeNum == ScrapeNum.Longest and len(x)!=0:
            _put(max(x, key=len), result, keys, putKey)

        elif base.scrapeNum == ScrapeNum.Unique:
            if result not in x:
                _put(x, result, keys, putKey)
        else:
            _put(x, result, keys, putKey)


def scrapeJsonTree(j, base: ScrapeNode, allowMissingKey:bool = False) -> Union[list,dict]:
    result = {}
    keys = set()
    _scrapeJsonTree(j, base, result, keys)

    if base.collapse:
        try:
            keys.remove(base.key)
        except:
            pass

    if not allowMissingKey:
        requiredKeys = set()
        base.getKeys(requiredKeys)

        if keys != requiredKeys:
            cfg.logger.debug(f"Scraped Keys Not Equal To Required Keys \nScrapedKeys: {keys} \nRequired Keys: {requiredKeys}")
            if cfg.testing:
                with open(cfg.testDataDumpPath, 'w') as f:
                    json.dump(j, f, indent=2)
                    map = {}
                    base.getOldKeyToNewKeyMap(map)
                    missingKeys = [(f"{map[k]} " + (f"(renamed: {k})" if map[k] != k else "")) for k in requiredKeys if k not in keys]
                    surplusKeys = [(f"{map[k]} " + (f"(renamed: {k})" if map[k] != k else "")) for k in keys if k not in requiredKeys]

                    if len(missingKeys) > 0:
                        f.write('\n'+ f'Missing Keys: {missingKeys}')

                    if len(surplusKeys) > 0:
                        f.write('\n'+ f'Surplus Keys: {surplusKeys}')

            raise KeyError


    if len(result) == 0:
        requiredKeys = set()
        base.getKeys(requiredKeys)
        print(keys, requiredKeys)
        raise KeyError("Empty Result")

    if base.collapse:
        return result[base.key]

    return result
