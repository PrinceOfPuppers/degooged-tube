from typing import List, Union
from enum import Enum
from dataclasses import dataclass
import json
import degooged_tube.config as cfg

class ScrapeError(Exception):
    pass

@dataclass
class ScrapeJsonTreeDebugData:
    requiredKeys: set
    foundKeys: set
    data: dict
    oldKeyToNewKeyMap: dict

def dumpDebugData(debugDataList: Union[list[ScrapeJsonTreeDebugData], None]):
    if debugDataList is None:
        if cfg.testing:
            raise Exception("ScrapeJsonTreeDebugData is None While Testing")
        return

    for i,debugData in enumerate(debugDataList):
        requiredKeys = debugData.requiredKeys
        foundKeys = debugData.foundKeys
        data = debugData.data
        map = debugData.oldKeyToNewKeyMap
        
        with open(cfg.testDataDumpPath, 'w') as f:
            f.write(f"\nData Number {i}:\n==================================================\n")
            json.dump(data, f, indent=2)
            missingKeys = [(f"{map[k]} " + (f"(renamed: {k})" if map[k] != k else "")) for k in requiredKeys if k not in foundKeys]
            surplusKeys = [(f"{map[k]} " + (f"(renamed: {k})" if map[k] != k else "")) for k in foundKeys if k not in requiredKeys]

            if len(missingKeys) > 0:
                f.write('\n'+ f'Missing Keys: {missingKeys}')

            if len(surplusKeys) > 0:
                f.write('\n'+ f'Surplus Keys: {surplusKeys}')




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


def scrapeJsonTree(j, fmt: Union[ScrapeNode, list[ScrapeNode]], debugDataList:list[ScrapeJsonTreeDebugData] = None, percentRequiredKeys:float = None) -> Union[list,dict]:
    # default value of percentRequiredKeys depends on if we are in debug mode, if so then we dont allow any missing keys so we can check the formatting
    if percentRequiredKeys is None:
        percentRequiredKeys = 0.5 if debugDataList is None else 1.0

    if isinstance(fmt,list):
        baseNodes = fmt
    else:
        baseNodes = [fmt]

    result = []
    keys = set()
    requiredKeys = set()
    map = {}
    for base in baseNodes:
        r = {}
        _scrapeJsonTree(j, base, r, keys)
        base.getKeys(requiredKeys)
        base.getOldKeyToNewKeyMap(map)

        if len(r) > 0:
            if base.collapse:
                result.append(r[base.key])
                try:
                    keys.remove(base.key)
                except:
                    pass
            else:
                result.append(r)


    if percentRequiredKeys != 0.0:
        ratio = 1.0 if len(requiredKeys) == 0 else len(keys)/len(requiredKeys)

        if ratio < percentRequiredKeys:
            cfg.logger.debug(f"Too Many Required Keys Missing \nScrapedKeys: {keys} \nRequired Keys: {requiredKeys}")
            
            if debugDataList is not None:
                cfg.logger.debug(f"Adding ScrapeJsonTreeDebugData to debugDataList")
                debugDataList.append(ScrapeJsonTreeDebugData(requiredKeys, keys, j, map))

            raise ScrapeError(f"Too Many Required Keys Missing \nScrapedKeys: {keys} \nRequired Keys: {requiredKeys}")


    
    if not isinstance(fmt, list):
        return result[0]

    return result

