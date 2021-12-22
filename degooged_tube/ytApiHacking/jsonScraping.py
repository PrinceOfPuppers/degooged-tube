from typing import List, Union, Callable, Any
from dataclasses import dataclass
import json
import degooged_tube.config as cfg

class ScrapeError(Exception):
    pass

@dataclass
class ScrapeJsonTreeDebugData:
    missingLeaves: set
    requiredLeaves: set
    foundLeaves: set
    data: dict

def dumpDebugData(debugDataList: Union[list[ScrapeJsonTreeDebugData], None]):
    if debugDataList is None:
        if cfg.testing:
            raise Exception("ScrapeJsonTreeDebugData is None While Testing")
        return

    with open(cfg.testDataDumpPath, 'w') as f:
        for i,debugData in enumerate(debugDataList):
            data = debugData.data
            
            f.write(f"\nData Number {i}:\n==================================================\n")
            json.dump(data, f, indent=2)

            if len(debugData.missingLeaves) > 0:
                f.write('\n'+ f'Missing Leaves: {debugData.missingLeaves}')

            f.write('\n'+ f'Required Leaves: {debugData.requiredLeaves}')
            f.write('\n'+ f'Found Leaves: {debugData.foundLeaves}')




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




ScrapeElement = Union['_ScrapeNode', 'ScrapeUnion']

@dataclass
class ScrapeUnion:
    children: list[ScrapeElement]

    def __post_init__(self):
        if len(self.children) == 0:
            raise Exception("ScrapeUnion Cannot be Leaf Node")

    def getMissingLeaves(self, foundLeaves:set[str], missingLeaves:set[str], requiredLeaves:set[str]):
        child = self.children[0]
        mainMissingLeaves  = set()
        mainRequiredLeaves = set()
        child.getMissingLeaves(foundLeaves, mainMissingLeaves, mainRequiredLeaves)

        for i in range(1, len(self.children)):
            child = self.children[i]
            m:set[str] = set()
            r:set[str] = set()
            child.getMissingLeaves(foundLeaves, m, r)
            if mainMissingLeaves is None or len(m) < len(mainMissingLeaves):
                mainMissingLeaves = m
                mainRequiredLeaves = r


        missingLeaves = missingLeaves.intersection(mainMissingLeaves)
        requiredLeaves.update(mainRequiredLeaves)

    def _strIndent(self, numIndent):
        indent = numIndent*'  '
        indentp1 = indent + '  '
        s = f"{indent}{self.__class__.__name__}(\n"\
            f"{indentp1}children:\n" + \
                 "\n".join([child._strIndent(numIndent+2) for child in self.children]) + \
            f"\n{indent})"

        return s


    def __repr__(self):
        return self._strIndent(0)

    def __str__(self):
        return self.__repr__()

def _getMissingLeavesFromList(scrapeElements: list[ScrapeElement], foundLeaves:set[str], missingLeaves:set[str], requiredLeaves:set[str]):
    for child in scrapeElements:
        childMissingLeaves = set()
        child.getMissingLeaves(foundLeaves, childMissingLeaves, requiredLeaves)
        missingLeaves = missingLeaves.intersection(childMissingLeaves)
    return 

@dataclass
class _ScrapeNode:
    key: str
    children: list[ScrapeElement]
    rename: str
    collapse: bool
    optional: bool
    valContainerConstructor:Callable
    dataCondition:Union[ Callable[[Any],bool], None ]

    def getVal(self, _):
        raise NotImplementedError("Virtual Method, Must Be Overrided")

    def getMissingLeaves(self, foundLeaves:set[str], missingLeaves:set[str], requiredLeaves:set[str]):
        if self.optional:
            return

        if len(self.children) == 0:
            requiredLeaves.add(self.key)
            if self.key not in foundLeaves:
                missingLeaves.add(self.key)
            return

        _getMissingLeavesFromList(self.children, foundLeaves, missingLeaves, requiredLeaves)
        return 

    def _strIndent(self, numIndent):
        indent = numIndent*'  '
        indentp1 = indent + '  '
        s = f"{indent}{self.__class__.__name__}(\n"\
            f"{indentp1}key: {self.key}\n" \
            f"{indentp1}rename: {self.rename}\n" if self.rename else ""\
            f"{indentp1}collapse: {self.collapse}\n" if self.collapse else ""\

        if len(self.children) > 0:
            s += \
                f"{indentp1}children:\n" + \
                     "\n".join([child._strIndent(numIndent+2) for child in self.children]) + \
                f"\n{indent})"

        return s


    def __repr__(self):
        return self._strIndent(0)

    def __str__(self):
        return self.__repr__()



@dataclass
class ScrapeAll(_ScrapeNode):
    def __init__(self, key:str, children:list[ScrapeElement], collapse:bool = False, 
                       rename:str = "", optional:bool = False, dataCondition: Callable[[Any],bool]= None):
        super().__init__(key, children, rename, collapse, optional, list, dataCondition)
        self.key = key
        self.rename = rename

    def getVal(self, j):
        res = []
        scrapeJson(j, self.key, res)
        if len(res) == 0:
            return None

        if self.dataCondition is None:
            return res
        if self.dataCondition(res):
            return res
        return None

@dataclass
class ScrapeNth(_ScrapeNode):
    n:int

    def __init__(self, key:str, children:list[ScrapeElement], collapse:bool = False, 
                       rename:str = "", optional:bool = False, dataCondition: Callable[[Any],bool]= None, n:int = 1):
        super().__init__(key, children, rename, collapse, optional, list, dataCondition)
        self.n = n

    def getVal(self, j):
        if self.n == 1:
            return scrapeFirstJson(j, self.key)

        res = []
        scrapeJson(j, self.key, res)
        if len(res) == 0:
            return None
        try:
            data = res[self.n]
        except IndexError:
            return None

        if self.dataCondition is None:
            return data
        if self.dataCondition(data):
            return data
        return None

@dataclass
class ScrapeLongest(_ScrapeNode):

    def __init__(self, key:str, children:list[ScrapeElement], collapse:bool = False, 
                       rename:str = "", optional:bool = False, dataCondition: Callable[[Any],bool]= None):
        super().__init__(key, children, rename, collapse, optional, list, dataCondition)

    def getVal(self, j):
        res = []
        scrapeJson(j, self.key, res)
        if len(res) == 0:
            return None
        data = max(res, key=len)
        if self.dataCondition is None:
            return data
        if self.dataCondition(data):
            return data
        return None


def _update(src, dest: Union[dict, list]):
    if isinstance(dest, dict):
        if isinstance(src, dict):
            dest.update(src)
            return
        raise ValueError(
            f"Unable to Update Dictionary with Type: {type(src)}\n"
            f"src: \n{src}\n"
            f"dest:\n{dest}\n"
        )

    dest.append(src)
    return

def _put(src, dest: Union[list, dict], key: Union[str,None] = None):
    if isinstance(dest,list):
        dest.append(src)
        return

    elif type(dest) is dict:
        if key == None:
            raise KeyError("Key Required")

        if key in dest and isinstance(src, dict):
            if isinstance(dest[key], dict):
                dest[key].update(src)
                return
            if isinstance(dest[key], list):
                dest[key].append(src)

            raise KeyError("Key Already Exists, Unable to Insert Value")

        dest[key] = src

def _scrapeJsonTree(j, base: ScrapeElement, leavesFound: set[str], truncateThreashold:float) -> Union[dict, list, None]:
    isLeaf = len(base.children) == 0

    leavesFoundInBranch = set()

    if isinstance(base,ScrapeUnion):
        if isLeaf:
            raise ScrapeError("ScrapeUnion Cannot be Leaf Node")

        chosenChild = None
        childVal = None
        for child in base.children:
            l = set()
            c = _scrapeJsonTree(j, child, l, truncateThreashold)
            if childVal is not None:
                if len(l) > len(leavesFoundInBranch):
                    leavesFoundInBranch  = l
                    childVal = c
                    chosenChild = child

        if childVal is None:
            return None

        if isinstance(chosenChild, ScrapeUnion) or chosenChild.collapse:
            res = childVal

        else:
            childKey = chosenChild.rename if chosenChild.rename else chosenChild.key
            res = {childKey: childVal}


    else:
        res = base.valContainerConstructor()
        currentVal = base.getVal(j) 
        if currentVal is None:
            return None

        if isLeaf:
            leavesFound.add(base.key)
            return currentVal


        for child in base.children:
            childVal = _scrapeJsonTree(currentVal, child, leavesFoundInBranch, truncateThreashold)
            if childVal is None:
                continue
            if isinstance(child, ScrapeUnion) or child.collapse:
                _update(childVal, res)
                continue

            childKey = child.rename if child.rename else child.key
            _put(childVal, res, childKey)

    missingLeaves = set()
    requiredLeaves = set()
    base.getMissingLeaves(leavesFoundInBranch, missingLeaves, requiredLeaves)
    if 1 - len(missingLeaves) / len(requiredLeaves) < truncateThreashold:
        return None

    leavesFound.update(leavesFoundInBranch)
    return res


def scrapeJsonTree(j, fmt: Union[ScrapeElement, list[ScrapeElement]], debugDataList: list[ScrapeJsonTreeDebugData] = None, truncateThreashold:float = None):
    if truncateThreashold is None:
        truncateThreashold = 0.5 if debugDataList is None else 1.0

    if isinstance(fmt, list):
        bases = fmt
    else:
        bases = [fmt]

    res = {}
    leavesFound = set()
    missingLeaves = set()
    requiredLeaves = set()
    
    for base in bases:
        val = _scrapeJsonTree(j, base, leavesFound, truncateThreashold)
        if val is None:
            return None
        if isinstance(base, ScrapeUnion) or base.collapse:
            _update(val, res)
            continue
        key = base.rename if base.rename else base.key
        _put(base, res, key)

    missingLeaves = set()
    requiredLeaves = set()
    _getMissingLeavesFromList(bases, leavesFound, missingLeaves, requiredLeaves)
    if 1 - len(missingLeaves) / len(requiredLeaves) < truncateThreashold:
        if debugDataList is not None:
            debugDataList.append(ScrapeJsonTreeDebugData(missingLeaves, requiredLeaves, leavesFound, j))
        raise ScrapeError(f"Too Many Leaves Missing \nmissingLeaves: {missingLeaves} \nrequiredLeaves: {requiredLeaves}")

    return res

