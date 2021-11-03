import requests
import re
import json
from typing import Union
from dataclasses import dataclass
import degooged_tube.config as cfg

apiKeyRe = re.compile(r'[\'\"]INNERTUBE_API_KEY[\'\"]:[\'\"](.*?)[\'\"]')
continuationTokenRe = re.compile(r'[\'\"]token[\'\"]\s?:\s?[\'\"](.*?)[\'\"]')
clientVersionRe = re.compile(r'[\'\"]cver[\'\"]: [\'|\"](.*?)[\'\"]')
ytInitalDataRe = re.compile(r"ytInitialData = (\{.*?\});</script>")


@dataclass()
class YtContIter:
    url: str
    continuationUrlFragment: str
    key: str
    continuationToken: str
    clientVersion: str
    endOfData:bool

    initalData: Union[dict, None] = None # used to store elements provided on first page load, set to none after first getNext


    @classmethod
    def fromUrl(cls, url:str, continuationUrlFragment: str, getDataInScript = True) -> Union['YtContIter', None]:
        r=requests.get(url)

        x,y,z = apiKeyRe.search(r.text), continuationTokenRe.search(r.text), clientVersionRe.search(r.text)

        if not x:
            cfg.logger.error("Unable to Find INNERTUBE_API_KEY")
            return None

        if not y:
            cfg.logger.error("Unable to Find Continuation Token")
            return None

        if not z:
            cfg.logger.error("Unable to Find Youtube Client Version")
            return None

        key = x.group(1)
        continuationToken = y.group(1)
        clientVersion = z.group(1)

        if getDataInScript:
            a = ytInitalDataRe.search(r.text)
            if not a:
                cfg.logger.error("Unable to Find ScriptData")
                return None
            b = a.group(1)
            initalData = json.loads(b)
            return cls(url, continuationUrlFragment, key, continuationToken, clientVersion,False, initalData)

        return cls(url, continuationUrlFragment, key, continuationToken, clientVersion,False)


    def getNext(self) -> Union[dict, None]:
        # gets element that was sent on page load
        if self.initalData:
            data = self.initalData
            self.initalData = None
            return data

        if self.endOfData:
            return None
        requestData = '''{
            "context": {
                "adSignalsInfo": {
                },
                "clickTracking": {
                },
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "'''+self.clientVersion+'''",
                },
                "request": {
                },
                "user": {
                }
            },
            "continuation": "'''+self.continuationToken+'''"
        }'''
        
        reqUrl = f'https://www.youtube.com/youtubei/v1/{self.continuationUrlFragment}?key={self.key}'
        b = requests.post(reqUrl, data=requestData)
        cfg.logger.debug(f"Sent Post Request to: {reqUrl} \nStatus {b.status_code} {b.reason}")

        if b.status_code != 200:
            cfg.logger.error(f"Error Sending Post Request to: {reqUrl} \nStatus {b.status_code} {b.reason}")
            return None
        
        x = continuationTokenRe.search(b.text)

        if not x:
            self.endOfData = True
            cfg.logger.debug(f"Reached End of Continuation Chain, Yeilding Last Result")
        else:
            self.continuationToken = x.group(1)


        data:dict = json.loads(b.text)
        return data
