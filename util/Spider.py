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
    ''' ���������ռ�����
        �������������ɸѡ���ӽ���ץȡ������ҳ�滺�浽ָ��������
        ͬʱ����ָ��Callback�ص�������ȡ��ҳ����д���
        ���ö��̴߳���
        ***ע��***
        ��ץȡ��ҳʱ����������ֱ��룬��'UTF-8'��'ISO-8859-1'��
        ͨ��response.encoding�������鿴�ǲ������ֱ��롣
        �����'ISO-8859-1'���룬�ͱ��������趨response.encoding��
    '''

    def __init__(self, vUrl=None, vDomain=None, \
        vDelay=2, vMaxDepth=10, vMaxDownload=None, \
        vHeaders=REQUEST_HEADERS, vProxies=None, vCache=None, \
        vAllowRules=None, vDisallowRules=None, \
        mCallbackSaveSource=None, mCallbackAnalyzeHtml=None, \
        vReset=False, vReport=True \
    ):
        ''' vUrl: ��վ��ַ
            vDomain: ��վ����(���ָ������վ��ַ��ָ����������Ч)
            
            vDelay: �ȴ�ʱ��(��)
            vMaxDepth: ����������(Ĭ����10, None��ʾ������)
            vMaxDownload: ������ش���(None��ʾ������)
            
            vHeaders = {'User-Agent': 'MyApp/0.0.1',}
            vProxies = {
                'http':    'http://10.0.0.1:81',
                'https': 'https://10.0.0.1:82',
            }
            vCache: ָ����������
            
            vAllowRules: ƥ����Ҫץȡ������
            vDisallowRules: ƥ��ܾ�ץȡ������
            
            mCallbackSaveSource:
                �ص���������Response�����ݱ��浽�ļ�(ContentType����text�Ķ���)
                def mCallbackSaveSource(vUrl, vResponse)
            mCallbackAnalyzeHtml:
                �ص�����������Response������(ContentType��text�Ķ���)
                def mCallbackAnalyzeHtml(vUrl, vHtml)
            
            vReset: �Ƿ�Ҫ��������(True: �������أ�False: ���������أ������ϴεļ�¼)
                ע�⣺�ڶ������ͬʱ����ʱ��������øù��ܣ���vReset=False��
                ��vReset=Trueʱ��
                    ���ָ����vUrl����ô���������ظ���վ��ַ��
                    ���ָ����vDomain����ô���������ظ��������е����ӡ�
                    �������������û��ָ�������ͬ��vReset=False��
            vReport: ��ӡ�������

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


        # ���̴߳���
        vThreadQueue = []
        while (not self.vFinished or vThreadQueue):
            # �Ƴ�ֹͣ���߳�
            for vThread in vThreadQueue:
                if (not vThread.isAlive()):
                    vThreadQueue.remove(vThread)

            # �������߳�ֱ��װ���̶߳���
            while (not self.vFinished and len(vThreadQueue) < MAX_THREAD):
                vThread = threading.Thread(target=self.__linkCrawler)
                vThread.setDaemon(True)
                vThread.start()
                vThreadQueue.append(vThread)

            # �����̶߳��ڴ����У�ִ�еȴ����ó�CPU
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
                # ȡ���һ��Ԫ�ؾ��������������
                # ȡ��һ��Ԫ�����ǹ����������
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
                    # ��ʱ��ҳ��δ�ҵ�ʱ����ִ�к���Ĵ���
                    if (vResponse is None): continue

                    if (checkContentType(vResponse, 'text')):
                        # ȡ��ҳ������
                        vHtml = self.__getText(vResponse)
                        # ����ҳ������
                        if (self.vCache):
                            try:
                                self.vCache[vUrl] = vHtml
                            except CacheError as e:
                                # ���̿ռ�����
                                self.vFinished = True
                                break

                    # ִ�лص�����(����Response���ݵ��ļ�)
                    if (self.mCallbackSaveSource): self.mCallbackSaveSource(vUrl, vResponse)

                # Process stoped when html is none
                if (vHtml is None): continue


                # Get html links
                vQueryList = []
                for vLink in getLinks(vHtml):
                    # Filter for links matching our regular expression
                    vLink = vLink.strip()
                    # ɸѡ����
                    if (not self.__linkFilter(vLink, self.vAllowRules, self.vDisallowRules)): continue
                    vNewLink = normalizeLink(vUrl, vLink)
                    vQueryList.append([vNewLink, urlparse(vNewLink).netloc, vDepth+1, vUrl, vLink])

                # ִ�лص�����(����ҳ������)
                # �ص��������ص����ӱ����ǿ���ֱ��ʹ�õľ�������
                # ��Щ���ӽ����ٽ����ر�ת��normalizeLink()����
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


    # ȡ��ҳ������
    def __getText(self, vResponse):
        ''' ȡ��ҳ������
            ע�⣺ҳ�����response.encoding��
            ���ContentType��ָ��CharSet���ԣ���ôresponse.encoding����CharSet��ֵ��
            ����response.encoding�Ͳ���Ĭ��ISO-8859-1��
            �������ҳ�����ISO-8859-1����ʱ�ͻ�������롣
            ��ˣ�response.encoding��ISO-8859-1ʱ�������һ������
        '''
        if (vResponse.encoding == 'ISO-8859-1'):
            vEncodingList = requests.utils.get_encodings_from_content(vResponse.text)
            if (vEncodingList): vResponse.encoding = vEncodingList[0]
            else: vResponse.encoding = vResponse.apparent_encoding
        #msgDeg('Encoding: ' + vResponse.encoding)
        return vResponse.text


    def __linkFilter(self, vLink, vAllowRules=None, vDisallowRules=None):
        ''' ���ӹ�����
            vAllowRules: ƥ����Ҫץȡ������
            vDisallowRules: ƥ��ܾ�ץȡ������
        '''
        if (re.match('http[s]?:', vLink, re.I)):
            # ������Ǳ�վ���������ӣ�����������
            return False
        else:
            # ����Э�飬����������
            if (re.match('#|[a-z]+:', vLink, re.I)):
                return False
        
        # �ܾ�ץȡ������
        if (vDisallowRules):
            for vRule in vDisallowRules:
                if (re.search(vRule, vLink, re.I)):
                    return False
        
        # ��Ҫץȡ������
        if (vAllowRules):
            for vRule in vAllowRules:
                if (re.search(vRule, vLink, re.I)):
                    return True
            return False

        # Ĭ����ץȡ���� 
        return True

