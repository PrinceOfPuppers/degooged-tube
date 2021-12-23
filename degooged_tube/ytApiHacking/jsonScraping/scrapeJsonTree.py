from typing import Union, Callable, Any
from dataclasses import dataclass
import json

from .basicScraping import scrapeFirstJson, scrapeJson, scrapeJsonMultiKey

class ScrapeError(Exception):
    pass

@dataclass
class ScrapeJsonTreeDebugData:
    missingLeaves: set
    requiredLeaves: set
    foundLeaves: set
    data: dict

def dumpDebugData(debugDataList: Union[list[ScrapeJsonTreeDebugData], None], testDataDumpPath:str):
    if debugDataList is None:
        return

    with open(testDataDumpPath, 'w') as f:
        for i,debugData in enumerate(debugDataList):
            data = debugData.data
            
            f.write(f"\nData Number {i}:\n==================================================\n")
            json.dump(data, f, indent=2)

            if len(debugData.missingLeaves) > 0:
                f.write('\n'+ f'Missing Leaves: {debugData.missingLeaves}')

            f.write('\n'+ f'Required Leaves: {debugData.requiredLeaves}')
            f.write('\n'+ f'Found Leaves: {debugData.foundLeaves}')




ScrapeElement = Union['_ScrapeNode', 'ScrapeUnion', 'ScrapeAllUnion']

def _scrapeElementStrIndent(className: str, numIndent:int, **kwargs):
    indent = numIndent*'  '
    indentp1 = indent + '  '
    children = None
    s = f"{indent}{className}(\n"

    for key, value in kwargs.items():
        if not value:
            continue
        if key == "children":
            children = value
            continue
        s += f"{indentp1}{key}: {value}\n"

    if children is None:
        return s
    if len(children) == 0:
        return s

    s += \
        f"{indentp1}children: [\n" + \
             "\n".join([child.__repr__(numIndent = numIndent+2) for child in children]) + \
        f"\n{indentp1}]\n"
    f"{indent})"

    return s
    

def _getMissingLeavesFromList(scrapeElements: list[ScrapeElement], foundLeaves:set[str], missingLeaves:set[str], requiredLeaves:set[str]):
    for child in scrapeElements:
        child.getMissingLeaves(foundLeaves, missingLeaves, requiredLeaves)
    return 


@dataclass
class ScrapeUnion:
    children: list[ScrapeElement]

    def __post_init__(self):
        if len(self.children) == 0:
            raise Exception("ScrapeUnion Cannot be Leaf Node")
        self.isLeaf = False

    def __repr__(self, numIndent:int = 0):
        return _scrapeElementStrIndent(self.__class__.__name__, numIndent, isLeaf = self.isLeaf, children = self.children)

    def __str__(self):
        return self.__repr__()

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


        missingLeaves.update(mainMissingLeaves)
        requiredLeaves.update(mainRequiredLeaves)




@dataclass
class ScrapeAllUnionNode:
    key: str
    children: list[ScrapeElement]
    dataCondition:Union[ Callable[[Any],bool], None ] = None
    collapse = False
    rename:str = ""

    def __post_init__(self):
        self.isLeaf = len(self.children) == 0

    def __repr__(self, numIndent:int = 0):
        return _scrapeElementStrIndent(self.__class__.__name__, numIndent, 
            key = self.key, leaf = self.isLeaf, collapse = self.collapse, dataCondition = self.dataCondition, children = self.children
        )

    def __str__(self):
        return self.__repr__()


@dataclass
class ScrapeAllUnion:
    collapse:bool
    keys: list[str] # each one corrisponds to a childrenGroup
    children: list[ScrapeAllUnionNode]

    key:str         # only serves as the name of the data (irrelevent if collapsed)
    dataCondition:Union[ Callable[[Any],bool], None ]
    isLeaf:bool 
    rename:str = "" # for polymorphism with other ScrapeElements

    def __init__(self, name: str, children: list[ScrapeAllUnionNode], collapse:bool = False, dataCondition = None):
        self.key = name
        self.collapse = collapse
        self.dataCondition = dataCondition
        self.children = children

        if len(self.children) == 0:
            raise Exception("ScrapeAllUnion Cannot be Leaf Node")

        self.isLeaf:bool = False

    def __repr__(self, numIndent:int = 0):
        return _scrapeElementStrIndent(self.__class__.__name__, numIndent, 
            name = self.key, isLeaf = self.isLeaf, collapse = self.collapse, dataCondition = self.dataCondition, children = self.children
        )

    def __str__(self):
        return self.__repr__()

    def getVal(self, j):
        res = []
        scrapeJsonMultiKey(j,res, *self.keys)

        if len(res) == 0:
            return None

        if self.dataCondition is None:
            return res
        if self.dataCondition(res):
            return res
        return None

    def getMissingLeaves(self, foundLeaves:set[str], missingLeaves:set[str], requiredLeaves:set[str]):
        child = self.children[0]
        mainMissingLeaves  = set()
        mainRequiredLeaves = set()
        _getMissingLeavesFromList(child.children, foundLeaves, mainMissingLeaves, mainRequiredLeaves)

        for i in range(1, len(self.children)):
            child = self.children[i]
            m:set[str] = set()
            r:set[str] = set()
            _getMissingLeavesFromList(child.children, foundLeaves, m, r)
            if mainMissingLeaves is None or len(m) < len(mainMissingLeaves):
                mainMissingLeaves = m
                mainRequiredLeaves = r

        missingLeaves.update(mainMissingLeaves)
        requiredLeaves.update(mainRequiredLeaves)



@dataclass
class _ScrapeNode:
    key: str
    children: list[ScrapeElement]
    rename: str
    collapse: bool
    optional: bool
    iterOverVal:bool
    dataCondition:Union[ Callable[[Any],bool], None ]

    def __post_init__(self):
        self.isLeaf = len(self.children) == 0

    def __repr__(self, numIndent:int = 0, **kwargs):
        return _scrapeElementStrIndent(self.__class__.__name__, numIndent, 
            key = self.key, rename = self.rename, isLeaf = self.isLeaf, collapse = self.collapse, optional = self.optional, dataCondition = self.dataCondition, children = self.children,
            **kwargs
        )

    def __str__(self, **kwargs):
        return self.__repr__(0, **kwargs)


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



@dataclass
class ScrapeAll(_ScrapeNode):
    def __init__(self, key:str, children:list[ScrapeElement], collapse:bool = False, 
                       rename:str = "", optional:bool = False, dataCondition: Callable[[Any],bool]= None):
        super().__init__(key, children, rename, collapse, optional, True, dataCondition)
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
                       rename:str = "", optional:bool = False, dataCondition: Callable[[Any],bool]= None, n:int = 0):
        super().__init__(key, children, rename, collapse, optional, False, dataCondition)
        self.n = n

    def __repr__(self):
        return super().__repr__(0, n = self.n)

    def __str__(self):
        return super().__str__(n = self.n)

    def getVal(self, j):
        if self.n == 0:
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
        super().__init__(key, children, rename, collapse, optional, False, dataCondition)

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





def _ScrapeNodeHelper(currentVal, children: list[ScrapeElement], leavesFoundInBranch: set[str], truncateThreashold:float, iterOverVal:bool):
    res = []

    if not iterOverVal:
        currentVal = [currentVal]

    for val in currentVal:
        container = {}
        for child in children:
            childVal =_scrapeJsonTree(val, child, leavesFoundInBranch, truncateThreashold)
            if childVal is None:
                continue
            if isinstance(child, ScrapeUnion) or child.collapse:
                if len(children) == 1:
                    container = childVal
                    continue
                _update(childVal, container)
                continue
            childKey = child.rename if child.rename else child.key
            _put(childVal, container, childKey)
        if len(container) != 0:
            res.append(container)
    
    if len(res) == 0:
        return None

    if not iterOverVal:
        res = res[0]

    return res


def _UnionHelper(j, children: list[ScrapeElement], leavesFoundInBranch: set[str], truncateThreashold:float):
    chosenChild = None
    childVal = None
    for child in children:
        l = set()
        c = _scrapeJsonTree(j, child, l, truncateThreashold)
        if c is not None:
            if len(l) > len(leavesFoundInBranch):
                leavesFoundInBranch.clear()
                leavesFoundInBranch.update(l)
                childVal = c
                chosenChild = child

    
    if childVal is None:
        return None

    if isinstance(chosenChild, ScrapeUnion) or chosenChild.collapse:
        res = childVal

    else:
        childKey = chosenChild.rename if chosenChild.rename else chosenChild.key
        res = {childKey: childVal}

    return res

def _AllUnionHelper(j:list, children: list[ScrapeAllUnionNode], leavesFoundInBranch: set[str], truncateThreashold:float):
    res = []

    for val in j:
        chosenChild = None
        childVal = None
        elementLeaves = set()
        for child in children:
            l = set()
            c = _ScrapeNodeHelper(val, child.children, l, truncateThreashold, False)
            if c is not None:
                if len(l) > len(elementLeaves):
                    elementLeaves  = l
                    childVal = c
                    chosenChild = child

            if childVal is None:
                continue
        leavesFoundInBranch.update(elementLeaves)

        if isinstance(chosenChild, ScrapeUnion) or chosenChild.collapse:
            res.append(childVal)

        else:
            childKey = chosenChild.rename if chosenChild.rename else chosenChild.key
            res.append({childKey: childVal})

    if len(res) == 0:
        return None

    return res




def _scrapeJsonTree(j, base: ScrapeElement, leavesFound: set[str], truncateThreashold:float) -> Union[dict, list, None]:
    leavesFoundInBranch = set()

    if isinstance(base, ScrapeAllUnion):
        if base.isLeaf:
            raise ScrapeError("ScrapeAllUnion Cannot be Leaf Node")

        currentVal = base.getVal(j) 
        if currentVal is None:
            return None

        res = _AllUnionHelper(currentVal, base.children, leavesFoundInBranch, truncateThreashold)

    elif isinstance(base,ScrapeUnion):
        if base.isLeaf:
            raise ScrapeError("ScrapeUnion Cannot be Leaf Node")
        res = _UnionHelper(j, base.children, leavesFoundInBranch, truncateThreashold)


    else:
        currentVal = base.getVal(j) 
        if currentVal is None:
            return None

        if base.isLeaf:
            leavesFound.add(base.key)
            return currentVal

        res = _ScrapeNodeHelper(currentVal, base.children, leavesFoundInBranch, truncateThreashold, base.iterOverVal)


    if res is None:
        return None

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

    res = []
    if isinstance(fmt, list):
        bases = fmt
    else:
        bases = [fmt]

    leavesFound = set()
    missingLeaves = set()
    requiredLeaves = set()
    
    for base in bases:
        val = _scrapeJsonTree(j, base, leavesFound, truncateThreashold)
        if val is None:
            continue
        if isinstance(base, ScrapeUnion) or base.collapse:
            res.append(val)
            continue
        key = base.rename if base.rename else base.key
        res.append({key:val})

    missingLeaves = set()
    requiredLeaves = set()
    _getMissingLeavesFromList(bases, leavesFound, missingLeaves, requiredLeaves)
    if 1 - len(missingLeaves) / len(requiredLeaves) < truncateThreashold:
        if debugDataList is not None:
            debugDataList.append(ScrapeJsonTreeDebugData(missingLeaves, requiredLeaves, leavesFound, j))
        raise ScrapeError(f"Too Many Leaves Missing \nmissingLeaves: {missingLeaves} \nrequiredLeaves: {requiredLeaves}")

    if isinstance(fmt, list) :
        return res

    if len(res)==0:
        return None

    return res[0]
