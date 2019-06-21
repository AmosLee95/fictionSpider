# http://www.aixiashu.com/30/30908/
# webEncoding = 'UTF-8'
# /https://www.booktxt.net/1_1482/
# webEncoding = 'gbk'


sourceLink = 'http://www.aixiashu.com/36/36732/'
webEncoding = 'UTF-8'
threadDapth = 30
jumpNum = 0


import requests
from bs4 import BeautifulSoup
import re
import _thread
def save(line, fileName, mode):
    file = open(fileName, mode,   encoding='utf-8')
    file.write(line)
    file.close()


class FictionSpider():
    def __init__(self):
        self.webEncoding = webEncoding
        self.chapter = []
        self.chapterNum = 0
        self.completeNum = 0
        self.runThread = 0
        self.unComplete = 0
    def run(self, sourceLink, queueDepth, jumpNum = 0):
        r = requests.get(sourceLink)
        r.encoding = 'UTF-8'
        soup = BeautifulSoup(r.text)
        # 写入文章的开头
        self.fictionTitle  = soup.select("#info h1")[0].text
        save(self.fictionTitle + "\n\n", self.fictionTitle+".txt", "w")

        chapterList = soup.select("#list dd")
        # 删除多余的信息（九章）
        for x in range(9 + jumpNum):
            chapterList.remove(chapterList[0])

        for entry in chapterList:
            entry = entry.contents[0]
            title = re.sub(r'[\.、]', "章", entry.text)
            title = re.sub(r'^第{0，1}', "第", title)+"\n\n"
            # title =  entry.text
            src = "http://www.aixiashu.com%s"%entry.attrs['href']
            # 记录起来
            self.chapter.append({'title':title,'content':'','src':src,'state':'static'})
            
        print('get chapterList complete')
        self.chapterNum = len(chapterList)
        for x in range(queueDepth):
            _thread.start_new_thread( self.tryGetAChapterConternt )
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
        # 经过检查，都complete，即可以进行保存了
        print('开始写入')
        for entry in self.chapter:
            title = entry['title']
            content = entry['content']
            text = "%s\n\n%s\n\n\n\n"%(title,content)
            # print('%s'%title)
            save(text, self.fictionTitle+".txt", "a")
        print('完成了！')
        if self.unComplete:
            print('警告，有未完成！\n unComplete:%d'%self.unComplete)

    def tryGetAChapterConternt(self):
        # 尝试看看谁没被用，就用起来
        # print('tryGetAChapterConternt\n')
        for index in range(len(self.chapter)):
            if self.chapter[index]['state'] == 'static':
                # print('[tryGetAChapterConternt] index : %d'%index)
                self.chapter[index]['state'] = 'running'
                src = self.chapter[index]['src']
                content = self.getChapterContent(src)
                self.chapter[index]['content'] = content
                self.chapter[index]['state'] = 'complete'
                self.completeNum += 1
                if index % 10 == 0 :
                    print('%d / %d\n'%(self.completeNum, self.chapterNum))

        self.runThread -= 1
        print('kill a thread, left:%d\n'%self.runThread)

    def getChapterContent(self, src):
        # print(src)
        r = requests.get(src)
        r.encoding = 'UTF-8'
        soup = BeautifulSoup(r.text)
        content  = soup.select("#content")[0].text
        content = re.sub(r'\xa0', "\n", content)
        content = re.sub(r'\ufeff', "\n", content)
        content = re.sub(r'\n\n', "\n", content)
        content = re.sub(r'\n\n', "\n", content)
        content = re.sub(r'\n\n', "\n", content)
        content = "\n\n"+re.sub(r'\n', "\n\n", content)
        return content



fictionSpider = FictionSpider()
fictionSpider.run(sourceLink, threadDapth, jumpNum)
