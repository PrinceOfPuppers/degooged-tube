from typing import List

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

def scrapeJsonMultiKey(j, results:list, *args: str):
    if isinstance(j,List):
        for value in j:
            if isinstance(value,List) or isinstance(value,dict):
                scrapeJsonMultiKey(value, results, *args)
        return

    if isinstance(j, dict):
        for key,value in j.items():
            if key in args:
                results.append({key: value})
            elif isinstance(value, dict) or isinstance(value, List):
                scrapeJsonMultiKey(value, results, *args)
        return
