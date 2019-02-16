#!python
# coding: gbk
#----------------------------------------
# ToutiaoCrawls.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import os, time, re
from datetime import datetime, timedelta
from urllib.parse import urlsplit, urljoin

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup

from Setting import DIR_OUTPUT
from Setting import MYSQL_CONF
from util.Common import msgInf, msgDeg
from util.project.BaseProject import BaseProject

from util.db.MysqlDBApi import MysqlDBApi as DBApi
from util.db.MysqlDBApi import DBApiError


SQL_CREATE_TABLE = '''
  CREATE TABLE toutiao_news(
    id         VARCHAR(64) NOT NULL,
    title      VARCHAR(256) NOT NULL,
    url        VARCHAR(256) NOT NULL,
    kind       VARCHAR(16) NOT NULL,
    comment    INT NOT NULL,
    uptime     VARCHAR(16) NOT NULL,
    source     VARCHAR(16) NOT NULL,
    update_ts  DATETIME,
    PRIMARY KEY(id)
  )
'''

URL = 'http://www.toutiao.com'

EXPIRE_DAYS         = 180
CRAWL_DELAY         = 2
MOVE_SCROLL_NUM     = 10
MOVE_SCROLL_SIZE    = 1200
REFRESH_NUM         = 3
REFRESH_DELAY       = 60

FIREFOX_PROFILE     = r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\m7u028lc.default'
#CHROME_USERDATA     = r'C:\Users\Administrator\AppData\Local\Google\Chrome\User Data'

CS_REFRESH          = 'div.refresh-mode'
CS_LOADING          = 'div.loading.ball-pulse'
CS_RECORD_GROUP     = 'div.feed-infinite-wrapper ul > li > div.bui-box.single-mode > div.single-mode-rbox > div.single-mode-rbox-inner'
CS_RECORD_TITLE     = 'div.title-box > a.link'
CS_RECORD_ATTRS     = 'div.bui-box.footer-bar > div.bui-left.footer-bar-left'
CS_RECORD_ATTRS_1   = 'a'
CS_RECORD_ATTRS_2   = 'span.footer-bar-action'

MSG_LOAD_FAILED     = '页面加载失败，请检查网络是否正常！'


class ToutiaoCrawls(BaseProject):
    def __init__(self):
        super().__init__()

        self.vRefreshNum = 0        # 页面刷新次数
        self.vMoveScrollNum = 0     # 滚动条移动次数
        self.vRecordNum = 0         # 加载新闻条数
        self.vInsertNum = 0         # 插入新闻条数

        # 数据库
        self.vDB = DBApi(MYSQL_CONF)
        # 浏览器
        self.vBrowser = None


    def setUp(self):
        ''' 初始化处理
            新建表,然后清除过期的数据.
            启动浏览器.
        '''
        msgInf('正在启动程序...')

        # 链接数据库
        self.vDB.connect()
        # 新建表
        try: self.vDB.execute(SQL_CREATE_TABLE)
        except DBApiError: pass
        
        # 清除过期的数据
        vSQL = 'DELETE FROM toutiao_news WHERE update_ts<%s'
        vPastDate = datetime.now() - timedelta(days=EXPIRE_DAYS)
        try:
            self.vDB.execute(vSQL, (vPastDate, ))
            self.vDB.commit()
        finally:
            self.vDB.close()

        # 启动浏览器
        self.vBrowser = webdriver.Firefox( \
            firefox_profile=webdriver.FirefoxProfile(FIREFOX_PROFILE), \
            log_path=os.path.join(DIR_OUTPUT, 'geckodriver.log') \
        )


    def tearDown(self):
        ''' 关闭浏览器
        '''
        msgInf('正在关闭程序...')
        try: self.vBrowser.close()
        except: pass



    def getRefreshElement(self):
        ''' 取得刷新元素
            在该元素上使用click()方法即可执行刷新页面操作。
        '''
        vWaitTime = 10
        vStartTime = time.time()
        while(True):
            try:
                # 取得显示刷新的元素
                return self.vBrowser.find_element_by_css_selector(CS_REFRESH)

            except WebDriverException as e:
                # 延迟处理
                if (time.time() - vStartTime > vWaitTime): raise e
                else: time.sleep(1)


    def waitForRefreshFinished(self):
        ''' 等待页面刷新完成
            点击刷新元素后，会显示"加载中..."的信息(style="")，
            当"加载中..."的信息消失时(style="display: none")，即可判定刷新处理已经完成。
        '''
        vWaitTime = 10
        vStartTime = time.time()
        while(True):
            try:
                # 取得显示"加载中..."的元素
                e = self.vBrowser.find_element_by_css_selector(CS_LOADING)
                vStyle = e.get_attribute('style').strip()
                vRegex = re.compile('display.+none', re.I)
                # 加载完成
                if (vRegex.match(vStyle)): return

            except WebDriverException as e:
                if (time.time() - vStartTime > vWaitTime): raise e
                else: time.sleep(1)


    def waitForLoadMoreRecords(self):
        ''' 等待页面新闻记录加载完成
            无论是刷新页面，还是移动滚动条导致页面加载时，都会增加新闻条数。
            由于加载一条两条新闻记录也会被认为是加载完成，
            所以在此之前要先判断页面的刷新处理是否完成。
        '''
        # 等待页面刷新完成
        self.waitForRefreshFinished()

        vWaitTime = 10
        vStartTime = time.time()
        vRecordNum = 0
        while(True):
            # 取得新闻条数
            vRecordNum = len(self.vBrowser.find_elements_by_css_selector(CS_RECORD_GROUP))
            # 更新完成
            if (vRecordNum > self.vRecordNum):
              self.vRecordNum = vRecordNum
              return True

            if (time.time() - vStartTime > vWaitTime): return False
            else: time.sleep(1)


    def getUrl(self):
        ''' 初次加载页面
        '''
        # INIT
        self.vRefreshNum = 0
        self.vMoveScrollNum = 0
        self.vRecordNum = 0

        # 加载页面
        msgInf('Getting: {}'.format(URL))
        self.vBrowser.get(URL)

        # 等待页面加载完成
        self.waitForLoadMoreRecords()


    def loadPageByMoveScroll(self):
        ''' 通过移动滚动条来加载页面
        '''
        vScrollPos = 0
        vFailedNum = 0
        while(True):
            # 移动滚动条
            msgInf('MoveScroll: {:0>2d}'.format(self.vMoveScrollNum + 1))
            vScrollPos += MOVE_SCROLL_SIZE
            self.vBrowser.execute_script('window.scrollTo(0, {});'.format(vScrollPos))

            # 等待页面加载完成
            # 移动滚动条距离不足以造成页面刷新时，可能导致页面加载失败
            if (not self.waitForLoadMoreRecords()):
                vFailedNum += 1
                if (vFailedNum < 3): continue
                else: raise WebDriverException(MSG_LOAD_FAILED)

            # 解析页面
            self.parsePage()

            # 延迟处理
            time.sleep(CRAWL_DELAY)

            # 页面加载完成
            self.vMoveScrollNum += 1
            msgDeg('Record Number: {}'.format(self.vRecordNum))
            if (self.vMoveScrollNum >= MOVE_SCROLL_NUM): break


    def loadPageByClickRefreshElement(self):
        ''' 通过点击刷新元素来加载页面
        '''
        vFailedNum = 0
        while(True):
            # 点击刷新
            e = self.getRefreshElement()
            msgInf('ClickRefreshElement: {:0>2d}'.format(self.vRefreshNum + 1))
            e.click()
            
            # 等待页面加载完成
            if (not self.waitForLoadMoreRecords()):
                vFailedNum += 1
                if (vFailedNum < 3): continue
                else: raise WebDriverException(MSG_LOAD_FAILED)

            # 解析页面
            self.parsePage()

            # 页面加载完成
            self.vRefreshNum += 1
            msgDeg('Record Number: {}'.format(self.vRecordNum))
            if (self.vRefreshNum >= REFRESH_NUM): break

            # 延迟处理
            time.sleep(REFRESH_DELAY)


    def savePage(self, vPageSource):
        vOutputFile = os.path.join( \
            DIR_OUTPUT, \
            '{}_CacheFile.html'.format(self.vAppName) \
        )
        with open(vOutputFile, 'w', encoding='UTF-8') as f:
            f.write(vPageSource)


    def parsePage(self):
        # 取得域名
        vDomain = urlsplit(URL).netloc

        # 取得页面
        # 2018-12-31 替换掉&nbsp;
        # 网页源代码中&nbsp;的utf-8编码是：\xc2\xa0，
        # 转换为Unicode字符为：\xa0，当显示到DOS窗口上的时候，转换为GBK编码的字符串，
        # 但是\xa0这个Unicode字符没有对应的GBK编码的字符串，所以出现错误。
        vHtml = self.vBrowser.page_source.replace('&nbsp;', ' ')
        self.savePage(vHtml)
        
        # 解析页面
        vSoup = BeautifulSoup(vHtml, 'lxml')
        
        # 保存结果序列
        vResultList = []

        # 取得所有新闻序列，并解析每条新闻数据
        for vRecord in vSoup.select(CS_RECORD_GROUP):
            # 新闻标题节点(列表)
            vNodeTitle = vRecord.select(CS_RECORD_TITLE)
            
            # 判断新闻是否链接到外网
            # 如果是外网，则不处理
            vHref = vNodeTitle[0].get('href').strip()
            if (vHref.startswith('http') and vDomain != urlsplit(vHref).netloc):
                continue
            
            vGroupId = vHref.split('/')[2]
            vTitle = vNodeTitle[0].get_text().strip()
    
            # 新闻属性节点(列表)
            vNodeAttrs = vRecord.select(CS_RECORD_ATTRS)
            # 新闻属性节点(列表)长度
            #msgDeg('vNodeAttrs size: {}'.format(len(vNodeAttrs)))
            
            # 新闻属性(类型，来源，评论)
            vNodeAttrs1 = vNodeAttrs[0].select(CS_RECORD_ATTRS_1)
            vSizeAttrs1 = len(vNodeAttrs1)
            
            
            # 类型
            vKind = None
            if   (vSizeAttrs1 <= 2): continue
            elif (vSizeAttrs1 == 3):
                # 原创
                vKind = '原创'
                # 在列表开头插入一个空元素，以填充类型的位置
                vNodeAttrs1.insert(0, None)
            else:
                # 非原创
                vKind = vNodeAttrs1[0].get_text().strip()


            # 来源(去掉末尾无法识别的字符)
            vSource = vNodeAttrs1[2].get_text()[:-1].strip()
            
            # 评论(去掉末尾无法识别的字符，以及‘评论’二字)
            vComment = 0
            vCommentText = vNodeAttrs1[3].get_text()[:-1].strip()[:-2]

            # 处理以‘万’结尾的评论
            if (vCommentText.endswith('万')):
                vCommentText = vCommentText.rstrip('万')
                vCommentText = float(vCommentText) * 10000
              
            # 取得评论处理
            if (vCommentText):
                try: vComment = int(vCommentText)
                except: continue

            # 新闻属性(发布时间)
            vNodeAttrs2 = vNodeAttrs[0].select(CS_RECORD_ATTRS_2)
            vUptime = vNodeAttrs2[0].get_text().strip()

            # 打印日志
            #msgDeg('类型:{}'.format(vKind))
            #msgDeg('来源:{}'.format(vSource))
            #msgDeg('评论:{}'.format(vComment))
            #msgDeg('发布:{}'.format(vUptime))
            
            # 收集信息
            vFields = []
            vFields.append(vGroupId)
            vFields.append(vTitle)
            vFields.append(urljoin(URL, vHref))
            vFields.append(vKind)
            vFields.append(vComment)
            vFields.append(vUptime)
            vFields.append(vSource)
            vResultList.append(vFields)

        # 更新数据
        self.updateData(vResultList)


    def updateData(self, vResultList):
        ''' 将数据更新到数据库
            先将数据插入表中，如果该数据已存在，就更新评论。
        '''
        vInsertSQL = 'INSERT INTO toutiao_news VALUES(%s,%s,%s,%s,%s,%s,%s,%s)'
        vUpdateSQL = 'UPDATE toutiao_news SET comment=%s WHERE id=%s'

        self.vDB.connect()
        try:
            self.vDB.lock('toutiao_news')
            for vItems in vResultList:
                # 插入新记录到数据库
                try:
                    self.vDB.execute(vInsertSQL, *vItems, datetime.now())
                    self.vInsertNum += 1
                # 该记录已存在，更新评论
                except DBApiError:
                    self.vDB.execute(vUpdateSQL, vItems[4], vItems[0])
            self.vDB.commit()
            self.vDB.unlock()

        finally:
            self.vDB.close()


    # 参数处理
    def procArgv(self): return True

    # 主处理
    def main(self):
        self.getUrl()
        self.loadPageByMoveScroll()
        self.loadPageByClickRefreshElement()

    # 处理结果报告
    def report(self):
        msgInf('Records: {}'.format(self.vRecordNum))
        msgInf('Inserts: {}'.format(self.vInsertNum))


# 执行
if (__name__ == '__main__'):
    ToutiaoCrawls().run()
