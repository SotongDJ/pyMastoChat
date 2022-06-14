from mastodon import Mastodon
import time, json, pathlib, re
from pyTimeTag import libCommand

def datetime(output_str="yyyymmddhhnn"):
    yyyy,mm,dd,hh,nn,ss,wday,yday,isdst = time.localtime(time.time())
    date_dict = {
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
    target_list = [ key_str for key_str in date_dict.keys() if key_str in output_str]
    result_str = output_str
    for key_str in target_list:
        value_str = str(date_dict[key_str])
        diffInt = len(key_str) - len(value_str)
        if diffInt > 0:
            value_str = "0"*diffInt + value_str
        result_str = result_str.replace(key_str,value_str)
    return result_str

class database:
    def __init__(self):
        self.data = dict()
        self.target_path = str()
    def load(self):
        if pathlib.Path(self.target_path).exists():
            source_dict = json.load(open(self.target_path))
            self.data = dict()
            for key,value in source_dict.items():
                if key[-3:] == "Set":
                    self.data[key] = set(value)
                else:
                    self.data[key] = value
        else:
            with open(self.target_path,'w') as target:
                json.dump(dict(),target,indent=1)
            self.data = dict()
    def save(self):
        with open(self.target_path,'w') as target:
            json.dump(self.data,target,indent=2,sort_keys=True)
    def setIt(self,target_key,target_object):
        dictionary = self.data.get(target_key,dict())
        dictionary.update(target_object)
        self.data.update({ target_key : dictionary })
        self.save()
    def updateSet(self,target_key,target_object):
        target_set = set(self.data.get(target_key,list()))
        target_set.update(target_object)
        self.data.update({ target_key : list(target_set) })
        self.save()

class chatbot:
    def __init__(self):
        self.bot_name = ""
        self.log_name = "" # whithout extension
        self.config_host = database()
        self.convers_host = database()
        self.initiation()
    def initiation(self):
        secret_dict = json.load(open("secret-{}.json".format(self.bot_name)))
        self.host = Mastodon(
            access_token = secret_dict['access_token'],
            api_base_url = secret_dict['hostname']
        )
        self.log_host = libCommand.tag()
        self.log_host.log.name = self.log_name + "-log.txt"
        self.log_host.error.name = self.log_name + "-error.txt"
        self.log_host.start()
        self.log_host.timeStamp("Start: init()")
        self.config_host.target_path = "config-{}.json".format(self.bot_name)
        self.config_host.load()
        self.sleep_time_int = int(self.config_host.data.get("sleep_time",60))
        pathlib.Path('userData').mkdir(parents=True,exist_ok=True)
        self.convers_host.target_path = "userData/index.json"
        self.convers_host.load()
        self.log_host.timeStamp("Finish: init()")
    def watching(self):
        self.log_host.timeStamp("Start: watch()")
        count_int = 1
        self.replied_dict = self.config_host.data.get("replied_dict",dict())
        self.rejected_dict = self.config_host.data.get("rejected_dict",dict())
        read_set = set()
        read_set.update(self.replied_dict.keys())
        read_set.update(self.rejected_dict.keys())
        self.mantain_bool = True
        while self.mantain_bool:
            read_set.update(self.replied_dict.keys())
            read_set.update(self.rejected_dict.keys())
            sleep_int = self.sleep_time_int
            notif = self.host.notifications()
            notif_dict = dict()
            notif_dict.update({ str(n.id) : n for n in notif if str(n.id) not in read_set })
            diff_int = len([ n.id for n in notif if str(n.id) not in read_set ])
            if diff_int > 0:
                self.log_host.timeStamp("Loaded message: {} from {}".format(diff_int,len(notif)))
            while diff_int == len(notif) and diff_int != 0:
                time.sleep(1)
                if sleep_int > 1:
                    sleep_int = sleep_int - 1
                min_id = notif[-1].id
                notif = self.host.notifications(max_id=min_id)
                read_set.update(notif_dict.keys())
                notif_dict.update({ str(n.id) : n for n in notif if str(n.id) not in read_set })
                diff_int = len([ n.id for n in notif if str(n.id) not in read_set ])
                self.log_host.timeStamp("Loaded message: {} from {}".format(diff_int,len(notif)))
            if len(notif_dict) > 0:
                self.log_host.timeStamp("Total {} message/s need to be process".format(len(notif_dict)))
            print("Period start:",count_int,end="\r")
            for target in sorted([ int(n) for n in notif_dict.keys()]):
                inbox = notif_dict[str(target)]
                filtering_dict = self.filtering(inbox)
                filtering_list = list(filtering_dict.keys())
                if filtering_dict == dict():
                    self.log_host.timeStamp("  [Period] {}       ".format(count_int))
                    error_bool,reply_msg = self.action(inbox)
                    if errorBool:
                        self.log_host.timeStamp("  Error: Unable handle")
                        original_content = inbox['status']['content']
                        purified_Content = self.contentPurifier(original_content)
                        self.log_host.timeStamp("  Message:"+str(purified_content))
                        self.log_host.timeStamp("  Type: "+inbox.type)
                    reply_toot = self.host.status_reply(inbox['status'],reply_msg)
                    self.log_host.timeStamp("  Reply: {}".format(reply_msg))
                    self.conversation(reply_toot)
                    self.replied_dict.update({ str(inbox.id) : inbox.status.id })
                    self.config_host.setIt("replied_dict",self.replied_dict)
                elif filtering_list == ["haventReview"]:
                    reply_msg = "Sorry, this chatbot are not available to you."
                    reply_toot = self.host.status_reply(inbox['status'],reply_msg)
                    self.log_host.timeStamp("  filteringList: \n{}".format(filtering_dict))
                    self.log_host.timeStamp("  Reply: {}".format(reply_msg))
                    self.conversation(reply_toot)
                    self.replied_dict.update({ str(inbox.id) : inbox.status.id })
                    self.config_host.setIt("replied_dict",self.replied_dict)
                else:
                    self.log_host.timeStamp("  filteringList: \n{}".format(filtering_dict))
                    self.log_host.timeStamp("  Rejected: <{}-{}>{}".format(inbox.account.id,inbox.id,inbox.type))
                    self.rejected_dict.update({ str(inbox.id) : inbox.type })
                    self.config_host.setIt("rejected_dict",self.rejected_dict)
                time.sleep(1)
                if sleep_int > 1:
                    sleep_int = sleep_int - 1
            self.countdown(sleep_int,"Period done:  {}".format(count_int))
            count_int = count_int + 1
    def filtering(self,toot):
        return_dict = dict()
        if toot.type != 'mention':
            return_dict.update({'no_mention':toot.type})
        user_id = str(toot.account.id)
        user_list = self.config_host.data.get("user_list",list())
        black_list = self.config_host.data.get("black_list",list())
        bot_list = self.config_host.data.get("bot_list",list())
        if user_id not in user_list and user_id not in black_list:
            return_dict.update({'havent_review':user_id})
        if user_id in bot_list or user_id in black_list:
            return_dict.update({'blocked':user_id})
        return return_dict
    def conversation(self,toot):
        convers_dict = dict()
        convers_dict.update(self.convers_host.data.get(self.bot_name,dict()))
        if toot.in_reply_to_id == None:
            parent_id = toot.id
        elif str(toot.in_reply_to_id) in convers_dict.keys():
            parent_id = convers_dict[str(toot.in_reply_to_id)]
        else:
            parent_id = toot.in_reply_to_id
        convers_dict.update({ str(toot.id) : parent_id })
        self.convers_host.setIt(self.bot_name,convers_dict)
    def action(self,toot):
        error_bool = False
        msg_str = ""
        return error_bool, msg_str
    def contentPurifier(self,raw_html):
        cleanr = re.compile('<.*?>')
        entertxt = raw_html.replace("<br />"," ")
        singletxt = entertxt.replace("\n"," ")
        tagtext = re.sub(cleanr, '', singletxt)
        removeSpace = tagtext.replace("\u200b"," ")
        cleantext = " ".join([ n for n in removeSpace.split(" ") if "@" not in n and n != "" ])
        return cleantext
    def countdown(self,timeInt,msg=""):
        i = 1
        while i <= timeInt:
            print("{} | Now waiting: {}s/{}s".format(msg,i,timeInt),end="\r")
            time.sleep(1)
            i = i + 1

if __name__ == "__main__":
    Bot = chatbot()
    Bot.watching()