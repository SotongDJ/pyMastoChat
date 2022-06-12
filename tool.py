import json, pathlib, re, time
def contentPurifier(raw_html):
    cleanr = re.compile('<.*?>')
    entertxt = raw_html.replace("<br />"," ")
    singletxt = entertxt.replace("\n"," ")
    tagtext = re.sub(cleanr, '', singletxt)
    removeSpace = tagtext.replace("\u200b"," ")
    cleantext = " ".join([ n for n in removeSpace.split(" ") if "@" not in n and n != "" ])
    return cleantext

def datetime(outputStr="yyyymmddhhnn"):
    yyyy,mm,dd,hh,nn,ss,wday,yday,isdst = time.localtime(time.time())
    dateDict = {
        "yyyy" : yyyy, "Y" : yyyy,
        "mm" : mm, "M" : mm,
        "dd" : dd, "D" : dd,
        "hh" : hh, "H" : hh,
        "nn" : nn, "N" : nn,
        "ss" : ss, "S" : ss,
        "wday" : wday,
        "yday" : yday,
        "isdst" : isdst
    }
    targetList = [ keyStr for keyStr in dateDict.keys() if keyStr in outputStr]
    resultStr = outputStr
    for keyStr in targetList:
        valueStr = str(dateDict[keyStr])
        diffInt = len(keyStr) - len(valueStr)
        if diffInt > 0:
            valueStr = "0"*diffInt + valueStr
        resultStr = resultStr.replace(keyStr,valueStr)
    return resultStr

def countdown(timeInt,msg=""):
    i = 1
    while i <= timeInt:
        print("{} | Now waiting: {}s/{}s".format(msg,i,timeInt),end="\r")
        time.sleep(1)
        i = i + 1


class database:
    def __init__(self):
        self.data = dict()
        self.targetPath = str()

    def load(self):
        if pathlib.Path(self.targetPath).exists():
            sourceDict = json.load(open(self.targetPath))
            self.data = dict()
            for key,value in sourceDict.items():
                if key[-3:] == "Set":
                    self.data[key] = set(value)
                else:
                    self.data[key] = value
        else:
            with open(self.targetPath,'w') as target:
                json.dump(dict(),target,indent=1)
            self.data = dict()

    def save(self):
        with open(self.targetPath,'w') as target:
            json.dump(self.data,target,indent=2,sort_keys=True)

    def setIt(self,targetKey,targetObject):
        dictionary = self.data.get(targetKey,dict())
        dictionary.update(targetObject)
        self.data.update({ targetKey : dictionary })
        self.save()

    def updateSet(self,targetKey,targetObject):
        targetSet = set(self.data.get(targetKey,list()))
        targetSet.update(targetObject)
        self.data.update({ targetKey : list(targetSet) })
        self.save()

class logging:
    def __init__(self):
        self.targetPath = str()
    def record(self,msg):
        logStr = "[{}] {}".format(datetime(outputStr="yyyy-mm-dd hh:mm:ss"),msg)
        with open(self.targetPath,'a') as target:
            target.write(logStr+"\n")
        print(logStr)
