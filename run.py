
try:
    import requests
    from bs4 import BeautifulSoup
except :
    import os
    os.system('pip install beautifulsoup4')
    os.system('pip install requests')
    import requests
    from bs4 import BeautifulSoup

import re
import _thread
import json
import sys
def save(line, fileName, mode):
    try:
        file = open("%s/%s"%(sys.path[0],fileName), mode,   encoding='utf-8')
    except FileNotFoundError:
        import os
        os.makedirs("%s/%s"%(sys.path[0],re.sub(r'/.+','',fileName)))
        file = open("%s/%s"%(sys.path[0],fileName), mode,   encoding='utf-8')
    file.write(line)
    file.close()
def readJson():

    # read configs
    file = open("%s/%s"%(sys.path[0],'config.json'), 'r', encoding='utf-8')
    configs = json.load(file)
    file.close()

    # read sourceLinkFile
    try:
        file = open("%s/%s"%(sys.path[0],'sourceUrl.json'), 'r', encoding='utf-8')
        sourceLinkFile = json.load(file)
        file.close()
    except:
        sourceLinkFile = {"sourceLink": "http://www.biquku.la/2/2553/","jumpNum":0,"threadDapth": 100,"replaceRegex":[]}

    # update sourceLinkFile 
    sourceLinkFile['urls'] = []
    # sourceLinkFile["replaceRegex"] = [r"^您可以在百度里搜索.+查找最新章节！\n\n",r"        .+最新章节地址.+html\n\n.+全文阅读地.+\n\n.+\n\n.+\n\n.+\n\n.+\(www\.soxs\.cc\)\n\n"]
    # print(sourceLinkFile["replaceRegex"][0])
    # print(sourceLinkFile["replaceRegex"][1])
    for index in configs:
        sourceLinkFile['urls'].append(configs[index]['sourceLink'])
    content = json.dumps(sourceLinkFile, ensure_ascii =False, indent=4)
    save(content, 'sourceUrl.json', "w")

    # get config
    sourceLink = sourceLinkFile['sourceLink']
    matchObj = re.search( r'(?<=www\.).+?(?=\.)', sourceLink)
    if matchObj:
        website = matchObj.group()

    print("current website:%s"%website)
    config = configs[website]
    if not config:
        print("config error!")
        
    # merge
    config['sourceLink'] =sourceLink 
    config["website"] = website
    try:
        config["jumpNum"] += sourceLinkFile['jumpNum']
    except:
        pass

    try:
        config["threadDapth"] = min(config["threadDapth"], sourceLinkFile['threadDapth'])
    except:
        pass

    try:
        config["replaceRegex"] += sourceLinkFile['replace']
        config["replaceRegex"] = list(set(config["replaceRegex"]))
    except:
        pass


    print("========get config====================")
    print(config)
    print("\n\n\n")
    print("========get config====================")
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

    def run(self, sourceLink, queueDepth, fitter, website, replaceRegex, jumpNum = 0):
        self.sourceLink = sourceLink
        self.fitter = fitter
        self.website = website
        self.replaceRegex = replaceRegex
        r = requests.get(sourceLink)
        r.encoding = self.catalogueEncoding
        soup = BeautifulSoup(r.text, features="html.parser")
        # 写入文章的开头
        self.fictionTitle  = soup.select(self.fitter['fictionTitle'])[0].text
        print(self.fictionTitle)
        chapterList = soup.select(self.fitter['chapterList'])
        # 删除多余的信息（九章）
        while jumpNum:
            chapterList.remove(chapterList[0])
            jumpNum -= 1

        for entry in chapterList:
            title = re.sub(r'[\.、]', "章", entry.text, 1)
            title = re.sub(r'^第?', "第", title)+"\n\n"
            # title =  entry.text
            # print(self.sourceLink)
            src = "%s%s"%(re.search(self.fitter['websiteEndRegex'],self.sourceLink).group(0), entry.attrs['href'])
            # 记录起来
            self.chapter.append({'title':title,'content':'','src':src,'state':'static'})
            
        print('get chapterList complete')
        self.chapterNum = len(chapterList)
        print('============================================================\n')
        print("ChapterNum: %d"%self.chapterNum)
        queueDepth = queueDepth if queueDepth < self.chapterNum else self.chapterNum
        print("QueueDepth: %d\n"%queueDepth)
        print('============================================================')
        while queueDepth:
            _thread.start_new_thread( self.tryGetAChapterConternt , ())
            self.runThread += 1
            queueDepth -= 1
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
        saveTo = "bookrack/"+self.fictionTitle+"_"+self.website+".txt"
        print('开始写入： %s'%(saveTo))
        save(self.fictionTitle + "\n\n", saveTo, "w")
            
        text = ""
        for index in range(len(self.chapter)):
            title = self.chapter[index]['title']
            content = self.chapter[index]['content']
            text = "%s%s\n\n%s\n\n\n\n"%(text, title, content)
            # print('%s'%title)
            if index % 30 == 0 or index == self.chapterNum - 1:
                save(text, saveTo, "a")
                text = ""
        print('完成了！')
        if self.unComplete:
            print('警告，有未完成！\n unComplete:%d'%self.unComplete)
            print(self.unCompleteSrc)

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
                    if self.completeNum % (self.chapterNum / 100) < 1 % (self.chapterNum / 100):
                        percent = round(1.0 * self.completeNum / self.chapterNum * 100,2)
                        print('爬取进度 : %.2f%%  [%d/%d]'%(percent,self.completeNum,self.chapterNum))
                    else:
                        if self.completeNum == self.chapterNum :
                            percent = 100.0
                            print('爬取进度 : %.2f%%  [%d/%d]'%(percent,self.completeNum,self.chapterNum))
        self.runThread -= 1
        # print('kill a thread, left:%d\n'%self.runThread)

    def getChapterContent(self, src):
        try:
            # print(src)
            r = requests.get(src)
            r.encoding = self.chapterEncoding
            soup = BeautifulSoup(r.text, features="html.parser")
            content  = soup.select(self.fitter['chapterContent'])[0].text
            content = re.sub(r'\xa0', "\n", content)
            content = re.sub(r'\ufeff', "\n", content)
            content = re.sub(r'\n\n', "\n", content)
            content = re.sub(r'\n\n', "\n", content)
            content = re.sub(r'\n\n', "\n", content)
            content = "\n\n"+re.sub(r'\n', "\n\n", content)

            for replaceRegex in self.replaceRegex:
                content = re.sub(replaceRegex, "", content)
        except:
            print('异常！')
            content = 'error'
        return content



config = readJson()
fictionSpider = FictionSpider(config["catalogueEncoding"], config["chapterEncoding"])
fictionSpider.run(config["sourceLink"], config["threadDapth"], config["fitter"], config["website"], config["replaceRegex"], config["jumpNum"])


