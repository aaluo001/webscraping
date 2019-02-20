#!python
# coding: gbk
#----------------------------------------
# Spider.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import re, threading, time

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError
from urllib.parse import urlparse

from Setting import MYSQL_CONF
from util.Common import msgInf, msgExp
from util.CrawlTool import getLinks, normalizeLink, checkContentType
from util.Throttle import Throttle
from util.DownloadQueue import DownloadQueue


REQUEST_TIMEOUT = 12
REQUEST_HEADERS = {'User-Agent': 'WebScraping-Spider/0.0.1'}
MAX_THREAD = 5


class Spider:
    ''' 网络数据收集器：
        利用网络爬虫对筛选链接进行抓取，并将页面缓存到指定容器。
        同时可以指定Callback回调函数对取得页面进行处理。
        采用多线程处理。
        ***注意***
        在抓取网页时，会出现两种编码，即'UTF-8'和'ISO-8859-1'。
        通过response.encoding属性来查看是采用哪种编码。
        如果是'ISO-8859-1'编码，就必须重新设定response.encoding。
    '''

    def __init__(self, vUrl=None, vDomain=None, \
        vDelay=2, vMaxDepth=10, vMaxDownload=None, \
        vHeaders=REQUEST_HEADERS, vProxies=None, vCache=None, \
        vAllowRules=None, vDisallowRules=None, \
        mCallbackSaveSource=None, mCallbackAnalyzeHtml=None, \
        vReset=False, vReport=True \
    ):
        ''' vUrl: 网站地址
            vDomain: 网站域名(如果指定了网站地址，指定域名将无效)
            
            vDelay: 等待时间(秒)
            vMaxDepth: 最大链接深度(默认是10, None表示无限制)
            vMaxDownload: 最大下载次数(None表示无限制)
            
            vHeaders = {'User-Agent': 'MyApp/0.0.1',}
            vProxies = {
                'http':    'http://10.0.0.1:81',
                'https': 'https://10.0.0.1:82',
            }
            vCache: 指定缓存容器
            
            vAllowRules: 匹配需要抓取得链接
            vDisallowRules: 匹配拒绝抓取得链接
            
            mCallbackSaveSource:
                回调函数，将Response的内容保存到文件(ContentType不是text的对象)
                def mCallbackSaveSource(vUrl, vResponse)
            mCallbackAnalyzeHtml:
                回调函数，分析Response的内容(ContentType是text的对象)
                def mCallbackAnalyzeHtml(vUrl, vHtml)
            
            vReset: 是否要重新下载(True: 重新下载，False: 不重新下载，继续上次的记录)
                注意：在多个进程同时下载时，必须禁用该功能，即vReset=False。
                当vReset=True时，
                    如果指定了vUrl，那么将重新下载该网站地址；
                    如果指定了vDomain，那么将重新下载该域名所有的链接。
                    如果上面两个都没有指定，则等同于vReset=False。
            vReport: 打印结果报告

        '''
        self.vUrl = vUrl
        self.vDomain = vDomain
        self.vThrottle = Throttle(vDelay)
        self.vMaxDepth = vMaxDepth
        self.vMaxDownload = vMaxDownload

        self.vHeaders = vHeaders
        self.vProxies = vProxies
        self.vCache = vCache

        self.vAllowRules = vAllowRules
        self.vDisallowRules = vDisallowRules

        self.mCallbackSaveSource = mCallbackSaveSource
        self.mCallbackAnalyzeHtml = mCallbackAnalyzeHtml

        self.vReset = vReset
        self.vReport = vReport

        # Download Finished
        self.vFinished = False
        # Download Queue
        self.vDQueue = DownloadQueue(MYSQL_CONF)

        # Download Counter
        self.vDCUrl         = 0
        self.vDCTotal       = 0
        self.vDCSuccessed   = 0
        self.vDCRetried     = 0
        self.vDCFailed      = 0

        self.vDCErrConnection = 0
        self.vDCErrTimeout = 0
        self.vDCErrHttp = 0


    def run(self):
        # Download Counter
        self.vDCUrl         = 0
        self.vDCTotal       = 0
        self.vDCSuccessed   = 0
        self.vDCRetried     = 0
        self.vDCFailed      = 0

        self.vDCErrConnection = 0
        self.vDCErrTimeout = 0
        self.vDCErrHttp = 0

        # Download Finished
        self.vFinished = False

        # Reset DownloadQueue
        if (self.vReset):
            if (self.vUrl): self.vDQueue.reset(vUrl=self.vUrl)
            elif (self.vDomain): self.vDQueue.reset(vDomain=self.vDomain)

        # Push Url into the DownloadQueue
        if (self.vUrl):
            self.vDomain = urlparse(self.vUrl).netloc
            self.vDQueue.push([[self.vUrl, self.vDomain, 0, None, None], ])


        # 多线程处理
        vThreadQueue = []
        while (not self.vFinished or vThreadQueue):
            # 移除停止的线程
            for vThread in vThreadQueue:
                if (not vThread.isAlive()):
                    vThreadQueue.remove(vThread)

            # 增加新线程直到装满线程队列
            while (not self.vFinished and len(vThreadQueue) < MAX_THREAD):
                vThread = threading.Thread(target=self.__linkCrawler)
                vThread.setDaemon(True)
                vThread.start()
                vThreadQueue.append(vThread)

            # 所有线程都在处理中，执行等待以让出CPU
            time.sleep(1)


        if (self.vReport):
            msgInf('Download Finished.')

            msgInf('Download Url: {}'.format(self.vDCUrl))
            msgInf('Download Total: {}'.format(self.vDCTotal))
            msgInf('Download Successed: {}'.format(self.vDCSuccessed))
            msgInf('Download Retried: {}'.format(self.vDCRetried))
            msgInf('Download Failed: {}'.format(self.vDCFailed))

            if (self.vDCFailed > 0):
                msgInf('Download ConnectionError: {}'.format(self.vDCErrConnection))
                msgInf('Download TimeoutError: {}'.format(self.vDCErrTimeout))
                msgInf('Download HttpError: {}'.format(self.vDCErrHttp))


    def __linkCrawler(self):
        ''' Crawl from the given ListQueue
            following links matched by LinkRegex
        '''
        while(True):
            try:
                # Get URL
                # 取最后一个元素就是深度优先搜索
                # 取第一个元素则是广度优先搜索
                vUrl, vDepth = self.vDQueue.pop( \
                    vMaxDepth=self.vMaxDepth, vDomain=self.vDomain)

            except IndexError as e:
                # The download queue is empty
                self.vFinished = True
                break

            else:
                vHtml = None
                if (self.vCache):
                    # Get cache file
                    try:
                        vHtml = self.vCache[vUrl]
                    except CacheError as e:
                        # The cache file dose not exist,
                        # Or has expired
                        pass

                if (vHtml is None):
                    # Check max download
                    if (self.vMaxDownload and self.vDCUrl >= self.vMaxDownload):
                        self.vFinished = True
                        break

                    # Download
                    self.vDCUrl += 1
                    vResponse = self.__download(vUrl)
                    # 超时或页面未找到时，不执行后面的处理
                    if (vResponse is None): continue

                    if (checkContentType(vResponse, 'text')):
                        # 取得页面内容
                        vHtml = self.__getText(vResponse)
                        # 缓存页面内容
                        if (self.vCache):
                            try:
                                self.vCache[vUrl] = vHtml
                            except CacheError as e:
                                # 磁盘空间已满
                                self.vFinished = True
                                break

                    # 执行回调函数(保存Response内容到文件)
                    if (self.mCallbackSaveSource): self.mCallbackSaveSource(vUrl, vResponse)

                # Process stoped when html is none
                if (vHtml is None): continue


                # Get html links
                vQueryList = []
                for vLink in getLinks(vHtml):
                    # Filter for links matching our regular expression
                    vLink = vLink.strip()
                    # 筛选链接
                    if (not self.__linkFilter(vLink, self.vAllowRules, self.vDisallowRules)): continue
                    vNewLink = normalizeLink(vUrl, vLink)
                    vQueryList.append([vNewLink, urlparse(vNewLink).netloc, vDepth+1, vUrl, vLink])

                # 执行回调函数(分析页面内容)
                # 回调函数返回的链接必须是可以直接使用的绝对链接
                # 这些链接将不再进行特别转换normalizeLink()处理
                if (self.mCallbackAnalyzeHtml):
                    for vLink in (self.mCallbackAnalyzeHtml(vUrl, vHtml) or []):
                        vQueryList.append([vLink, urlparse(vLink).netloc, vDepth+1, vUrl, 'mCallback'])

                # Push and Complete crawl queue
                if (vQueryList): self.vDQueue.push(vQueryList)
                self.vDQueue.complete(vUrl)


    def __download(self, vUrl, vRetries=2):
        self.vThrottle.wait(vUrl)
        self.vDCTotal += 1
        vCouldRetry = False

        try:
            vResponse = requests.get(vUrl, \
                headers=self.vHeaders, \
                proxies=self.vProxies, \
                timeout=REQUEST_TIMEOUT \
            )
            vResponse.raise_for_status()

        except ConnectionError as e:
            if (vRetries > 0):
                vCouldRetry = True
            else:
                msgExp(e)
                self.vDCErrConnection += 1

        except Timeout as e:
            if (vRetries > 0):
                vCouldRetry = True
            else:
                msgExp(e)
                self.vDCErrTimeout += 1

        except HTTPError as e:
            vCode = vResponse.status_code
            if (vRetries > 0 and 500 <= vCode < 600):
                vCouldRetry = True
            else:
                msgExp(e)
                self.vDCErrHttp += 1

        else:
            # Download Sucessed
            msgInf('Downloaded: {}'.format(vUrl))
            self.vDCSuccessed += 1
            return vResponse


        # Download Retry
        if (vCouldRetry):
            return self.__download(vUrl, vRetries - 1)

        # Download Failed
        else:
            self.vDCFailed += 1
            return None


    # 取得页面内容
    def __getText(self, vResponse):
        ''' 取得页面内容
            注意：页面编码response.encoding，
            如果ContentType中指定CharSet属性，那么response.encoding就是CharSet的值；
            否则，response.encoding就采用默认ISO-8859-1。
            如果中文页面采用ISO-8859-1编码时就会出现乱码。
            因此，response.encoding是ISO-8859-1时，还需进一步处理。
        '''
        if (vResponse.encoding == 'ISO-8859-1'):
            vEncodingList = requests.utils.get_encodings_from_content(vResponse.text)
            if (vEncodingList): vResponse.encoding = vEncodingList[0]
            else: vResponse.encoding = vResponse.apparent_encoding
        #msgDeg('Encoding: ' + vResponse.encoding)
        return vResponse.text


    def __linkFilter(self, vLink, vAllowRules=None, vDisallowRules=None):
        ''' 链接过滤器
            vAllowRules: 匹配需要抓取的链接
            vDisallowRules: 匹配拒绝抓取的链接
        '''
        if (re.match('http[s]?:', vLink, re.I)):
            # 如果不是本站域名的链接，将不作处理
            return False
        else:
            # 其他协议，将不作处理
            if (re.match('#|[a-z]+:', vLink, re.I)):
                return False
        
        # 拒绝抓取的链接
        if (vDisallowRules):
            for vRule in vDisallowRules:
                if (re.search(vRule, vLink, re.I)):
                    return False
        
        # 需要抓取的链接
        if (vAllowRules):
            for vRule in vAllowRules:
                if (re.search(vRule, vLink, re.I)):
                    return True
            return False

        # 默认是抓取对象 
        return True

