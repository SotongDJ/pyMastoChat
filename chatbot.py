from mastodon import Mastodon
# from pprint import pprint
import time, json, pathlib
import tool
class chatbot:
    def __init__(self):
        self.botName = ""

        self.configHost = tool.database()
        self.logHost = tool.logging()
        self.conversHost = tool.database()

        self.initiation()

    def initiation(self):
        self.configHost.targetPath = "config-{}.json".format(self.botName)
        self.configHost.load()
        secretDict = json.load(open("secret-{}.json".format(self.botName)))
        self.host = Mastodon(
            access_token = secretDict['access_token'],
            api_base_url = secretDict['hostname']
        )

        self.logHost.targetPath = "chatbot-{}.log".format(self.botName)
        pathlib.Path('userData').mkdir(parents=True,exist_ok=True)

        self.conversHost.targetPath = "userData/index.json"
        self.conversHost.load()
        
        self.sleepTimeInt = int(self.configHost.data.get("sleep_time",60))
        self.logHost.record("Finish: init()")

    def watching(self):
        self.logHost.record("Start: watch()")
        countInt = 1
        self.repliedDict = self.configHost.data.get("repliedDict",dict())
        self.rejectedDict = self.configHost.data.get("rejectedDict",dict())
        
        readSet = set()
        readSet.update(self.repliedDict.keys())
        readSet.update(self.rejectedDict.keys())
        
        self.mantainBool = True
        while self.mantainBool:
            readSet.update(self.repliedDict.keys())
            readSet.update(self.rejectedDict.keys())
            sleepInt = self.sleepTimeInt
            notif = self.host.notifications()
            notifDict = dict()
            notifDict.update({ str(n.id) : n for n in notif if str(n.id) not in readSet })
            diffInt = len([ n.id for n in notif if str(n.id) not in readSet ])
            if diffInt > 0:
                self.logHost.record("Loaded message: {} from {}".format(diffInt,len(notif)))
            while diffInt == len(notif) and diffInt != 0:
                time.sleep(1)
                if sleepInt > 1:
                    sleepInt = sleepInt - 1
                minID = notif[-1].id
                notif = self.host.notifications(max_id=minID)
                readSet.update(notifDict.keys())
                notifDict.update({ str(n.id) : n for n in notif if str(n.id) not in readSet })
                diffInt = len([ n.id for n in notif if str(n.id) not in readSet ])
                self.logHost.record("Loaded message: {} from {}".format(diffInt,len(notif)))

            if len(notifDict) > 0:
                self.logHost.record("Total {} message/s need to be process".format(len(notifDict)))
            
            print("Period start:",countInt,end="\r")
            for target in sorted([ int(n) for n in notifDict.keys()]):
                inbox = notifDict[str(target)]
                filteringDict = self.filtering(inbox)
                filteringList = list(filteringDict.keys())
                if filteringDict == dict():
                    self.logHost.record("  [Period] {}       ".format(countInt))
                    errorBool,replyMsg = self.action(inbox)

                    if errorBool:
                        self.logHost.record("  Error: Unable handle")
                        originalContent = inbox['status']['content']
                        purifiedContent = tool.contentPurifier(originalContent)
                        self.logHost.record("  Message:"+str(purifiedContent))
                        self.logHost.record("  Type: "+inbox.type)

                    replyToot = self.host.status_reply(inbox['status'],replyMsg)
                    self.logHost.record("  Reply: {}".format(replyMsg))

                    self.conversation(replyToot)

                    self.repliedDict.update({ str(inbox.id) : inbox.status.id })
                    self.configHost.setIt("repliedDict",self.repliedDict)

                elif filteringList == ["haventReview"]:
                    replyMsg = "Sorry, this chatbot are not available to you."
                    replyToot = self.host.status_reply(inbox['status'],replyMsg)
                    self.logHost.record("  filteringList: \n{}".format(filteringDict))
                    self.logHost.record("  Reply: {}".format(replyMsg))

                    self.conversation(replyToot)

                    self.repliedDict.update({ str(inbox.id) : inbox.status.id })
                    self.configHost.setIt("repliedDict",self.repliedDict)

                else:
                    self.logHost.record("  filteringList: \n{}".format(filteringDict))
                    self.logHost.record("  Rejected: <{}-{}>{}".format(inbox.account.id,inbox.id,inbox.type))
                    self.rejectedDict.update({ str(inbox.id) : inbox.type })
                    self.configHost.setIt("rejectedDict",self.rejectedDict)

                time.sleep(1)
                if sleepInt > 1:
                    sleepInt = sleepInt - 1

            tool.countdown(sleepInt,"Period done:  {}".format(countInt))
            countInt = countInt + 1

    def filtering(self,toot):
        returnDict = dict()
        if toot.type != 'mention':
            returnDict.update({'noMention':toot.type})
        userID = str(toot.account.id)
        userList = self.configHost.data.get("userList",list())
        blackList = self.configHost.data.get("blackList",list())
        botList = self.configHost.data.get("botList",list())
        if userID not in userList and userID not in blackList:
            returnDict.update({'haventReview':userID})
        if userID in botList or userID in blackList:
            returnDict.update({'blocked':userID})

        return returnDict

    def conversation(self,toot):
        conversDict = dict()
        conversDict.update(self.conversHost.data.get(self.botName,dict()))

        if toot.in_reply_to_id == None:
            parentID = toot.id
        elif str(toot.in_reply_to_id) in conversDict.keys():
            parentID = conversDict[str(toot.in_reply_to_id)]
        else:
            parentID = toot.in_reply_to_id

        conversDict.update({ str(toot.id) : parentID })
        self.conversHost.setIt(self.botName,conversDict)

    def action(self,toot):
        errorBool = False
        msgStr = ""
        return errorBool, msgStr

if __name__ == "__main__":
    Bot = chatbot()
    Bot.watching()