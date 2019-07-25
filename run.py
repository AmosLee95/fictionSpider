import requests
from bs4 import BeautifulSoup
import re
import _thread
import json
import sys
def save(line, fileName, mode):
    file = open("%s/%s"%(sys.path[0],fileName), mode,   encoding='utf-8')
    file.write(line)
    file.close()
def readJson(fileName):
    try:
        file = open("%s/%s"%(sys.path[0],fileName), 'r')
        configs = json.load(file)
        file.close()
    except :
        configs = {
            "sourceLink": "https://www.biquge.info/57_57727/",
            "dajiadu8":{
                "sourceLink": "https://www.dajiadu8.com/files/article/html/40/40250/index.html",
                "catalogueEncoding": "gb2312",
                "chapterEncoding": "gbk",
                "threadDapth": 100,
                "jumpNum": 0,
                "fitter":{
                    "fictionTitle":"#left h1",
                    "chapterList":"#booktext li a",
                    "r_src":".+/",
                    "chapterContent":"#content1"
                }
                
            },
            "aixiashu":{
                "sourceLink": "http://www.aixiashu.com/8/8615/",
                "catalogueEncoding": "utf-8",
                "chapterEncoding": "utf-8",
                "threadDapth": 100,
                "jumpNum": 9,
                "fitter":{
                    "fictionTitle":"#info h1",
                    "chapterList":"#list dd a",
                    "r_src": ".+com",
                    "chapterContent":"#content"
                }
            },
            "biquge":{
                "sourceLink": "https://www.biquge.info/57_57727/",
                "catalogueEncoding": "utf-8",
                "chapterEncoding": "utf-8",
                "threadDapth": 100,
                "jumpNum": 0,
                "fitter":{
                    "fictionTitle":"#info h1",
                    "chapterList":"#list dd a",
                    "r_src": ".+/",
                    "chapterContent":"#content"
                }
            }
        }
        content = json.dumps(configs)
        content = re.sub(r'(?<=[\{,]) *', "\n",content)
        content = re.sub(r'(?=\})', "\n",content)
        content = re.sub(r'\n"', '\n\t"',content)
        save(content, fileName, "w")
    sourceLink = configs['sourceLink']
    matchObj = re.search( r'(?<=www\.).+(?=\.)', sourceLink)
    if matchObj:
        key = matchObj.group()
    config = configs[key]
    if not config:
        print("config error!")
    config['sourceLink'] =sourceLink 
    print("============================\nget config")
    print(config)
    print("\n\n\n")
    return config

class FictionSpider():
    def __init__(self, catalogueEncoding, chapterEncoding):
        self.catalogueEncoding = catalogueEncoding
        self.chapterEncoding = chapterEncoding
        self.chapter = []
        self.chapterNum = 0
        self.completeNum = 0
        self.runThread = 0
        self.unComplete = 0
        self.unCompleteSrc=[]

    def run(self, sourceLink, queueDepth, fitter, jumpNum = 0):
        self.sourceLink = sourceLink
        self.fitter = fitter
        r = requests.get(sourceLink)
        r.encoding = self.catalogueEncoding
        soup = BeautifulSoup(r.text)
        # 写入文章的开头
        self.fictionTitle  = soup.select(self.fitter['fictionTitle'])[0].text

        chapterList = soup.select(self.fitter['chapterList'])
        # 删除多余的信息（九章）
        for x in range(jumpNum):
            if x < jumpNum:#强行消除警告，233
                chapterList.remove(chapterList[0])

        for entry in chapterList:
            title = re.sub(r'[\.、]', "章", entry.text)
            title = re.sub(r'^第?', "第", title)+"\n\n"
            # title =  entry.text
            src = "%s%s"%(re.search(self.fitter['r_src'],self.sourceLink).group(0), entry.attrs['href'])
            # 记录起来
            self.chapter.append({'title':title,'content':'','src':src,'state':'static'})
            
        print('get chapterList complete')
        self.chapterNum = len(chapterList)
        print('============================================================\n')
        print("ChapterNum: %d"%self.chapterNum)
        queueDepth = queueDepth if queueDepth < self.chapterNum else self.chapterNum
        print("QueueDepth: %d\n"%queueDepth)
        print('============================================================')
        for x in range(queueDepth):
            _thread.start_new_thread( self.tryGetAChapterConternt , ())
            self.runThread += 1
        # 检查是否都结束了
        while self.runThread:
            pass
        # 所有进程都结束了
        print('NO thread!')
        # 再次检查是否都完成了
        for entry in self.chapter:
            if entry['state'] != 'complete':
                # 只要有一个没停止，就return
                # todo：没停止可以跳到上面去，继续执行
                self.unComplete += 1
                self.unCompleteSrc.append(entry['src'])

        # 经过检查，都complete，即可以进行保存了
        print('开始写入： %s.txt'%self.fictionTitle)
        
        save(self.fictionTitle + "\n\n", self.fictionTitle+".txt", "w")
            
        text = ""
        for index in range(len(self.chapter)):
            title = self.chapter[index]['title']
            content = self.chapter[index]['content']
            text = "%s%s\n\n%s\n\n\n\n"%(text, title, content)
            # print('%s'%title)
            if index % 30 == 0 or index == self.chapterNum - 1:
                save(text, self.fictionTitle+".txt", "a")
                text = ""
        print('完成了！')
        if self.unComplete:
            print('警告，有未完成！\n unComplete:%d'%self.unComplete)

    def tryGetAChapterConternt(self):
        # 尝试看看谁没被用，就用起来
        # print('tryGetAChapterConternt\n')
            
        for index in range(len(self.chapter)):
            if self.chapter[index]['state'] == 'static':
                flag = True
                while flag:
                    # print('[tryGetAChapterConternt] index : %d'%index)
                    self.chapter[index]['state'] = 'running'
                    src = self.chapter[index]['src']
                    
                    content = self.getChapterContent(src)
                    if content == 'error':
                        self.chapter[index]['state'] = 'static'
                        # flag = True #不用修改
                    else:
                        self.chapter[index]['content'] = content
                        self.chapter[index]['state'] = 'complete'
                        self.completeNum += 1
                        flag = False

                    # show something
                    if self.completeNum == 1 :
                        print("ChapterNum: %d"%self.chapterNum)
                    if self.completeNum % (self.chapterNum / 100) < 1 % (self.chapterNum / 100):
                        print('%d%%'%(self.completeNum // (self.chapterNum / 100)))
                    else:
                        if self.completeNum == self.chapterNum :
                            print('100%%')
        self.runThread -= 1
        # print('kill a thread, left:%d\n'%self.runThread)

    def getChapterContent(self, src):
        try:
            # print(src)
            r = requests.get(src)
            r.encoding = self.chapterEncoding
            soup = BeautifulSoup(r.text)
            content  = soup.select(self.fitter['chapterContent'])[0].text
            content = re.sub(r'\xa0', "\n", content)
            content = re.sub(r'\ufeff', "\n", content)
            content = re.sub(r'\n\n', "\n", content)
            content = re.sub(r'\n\n', "\n", content)
            content = re.sub(r'\n\n', "\n", content)
            content = "\n\n"+re.sub(r'\n', "\n\n", content)
        except:
            print('异常！')
            content = 'error'
        return content



config = readJson('config.json')
fictionSpider = FictionSpider(config["catalogueEncoding"], config["chapterEncoding"])
fictionSpider.run(config["sourceLink"], config["threadDapth"], config["fitter"], config["jumpNum"])


