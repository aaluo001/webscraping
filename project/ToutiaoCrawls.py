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

MSG_LOAD_FAILED     = 'ҳ�����ʧ�ܣ����������Ƿ�������'


class ToutiaoCrawls(BaseProject):
    def __init__(self):
        super().__init__()

        self.vRefreshNum = 0        # ҳ��ˢ�´���
        self.vMoveScrollNum = 0     # �������ƶ�����
        self.vRecordNum = 0         # ������������
        self.vInsertNum = 0         # ������������

        # ���ݿ�
        self.vDB = DBApi(MYSQL_CONF)
        # �����
        self.vBrowser = None


    def setUp(self):
        ''' ��ʼ������
            �½���,Ȼ��������ڵ�����.
            ���������.
        '''
        msgInf('������������...')

        # �������ݿ�
        self.vDB.connect()
        # �½���
        try: self.vDB.execute(SQL_CREATE_TABLE)
        except DBApiError: pass
        
        # ������ڵ�����
        vSQL = 'DELETE FROM toutiao_news WHERE update_ts<%s'
        vPastDate = datetime.now() - timedelta(days=EXPIRE_DAYS)
        try:
            self.vDB.execute(vSQL, (vPastDate, ))
            self.vDB.commit()
        finally:
            self.vDB.close()

        # ���������
        self.vBrowser = webdriver.Firefox( \
            firefox_profile=webdriver.FirefoxProfile(FIREFOX_PROFILE), \
            log_path=os.path.join(DIR_OUTPUT, 'geckodriver.log') \
        )


    def tearDown(self):
        ''' �ر������
        '''
        msgInf('���ڹرճ���...')
        try: self.vBrowser.close()
        except: pass



    def getRefreshElement(self):
        ''' ȡ��ˢ��Ԫ��
            �ڸ�Ԫ����ʹ��click()��������ִ��ˢ��ҳ�������
        '''
        vWaitTime = 10
        vStartTime = time.time()
        while(True):
            try:
                # ȡ����ʾˢ�µ�Ԫ��
                return self.vBrowser.find_element_by_css_selector(CS_REFRESH)

            except WebDriverException as e:
                # �ӳٴ���
                if (time.time() - vStartTime > vWaitTime): raise e
                else: time.sleep(1)


    def waitForRefreshFinished(self):
        ''' �ȴ�ҳ��ˢ�����
            ���ˢ��Ԫ�غ󣬻���ʾ"������..."����Ϣ(style="")��
            ��"������..."����Ϣ��ʧʱ(style="display: none")�������ж�ˢ�´����Ѿ���ɡ�
        '''
        vWaitTime = 10
        vStartTime = time.time()
        while(True):
            try:
                # ȡ����ʾ"������..."��Ԫ��
                e = self.vBrowser.find_element_by_css_selector(CS_LOADING)
                vStyle = e.get_attribute('style').strip()
                vRegex = re.compile('display.+none', re.I)
                # �������
                if (vRegex.match(vStyle)): return

            except WebDriverException as e:
                if (time.time() - vStartTime > vWaitTime): raise e
                else: time.sleep(1)


    def waitForLoadMoreRecords(self):
        ''' �ȴ�ҳ�����ż�¼�������
            ������ˢ��ҳ�棬�����ƶ�����������ҳ�����ʱ��������������������
            ���ڼ���һ���������ż�¼Ҳ�ᱻ��Ϊ�Ǽ�����ɣ�
            �����ڴ�֮ǰҪ���ж�ҳ���ˢ�´����Ƿ���ɡ�
        '''
        # �ȴ�ҳ��ˢ�����
        self.waitForRefreshFinished()

        vWaitTime = 10
        vStartTime = time.time()
        vRecordNum = 0
        while(True):
            # ȡ����������
            vRecordNum = len(self.vBrowser.find_elements_by_css_selector(CS_RECORD_GROUP))
            # �������
            if (vRecordNum > self.vRecordNum):
              self.vRecordNum = vRecordNum
              return True

            if (time.time() - vStartTime > vWaitTime): return False
            else: time.sleep(1)


    def getUrl(self):
        ''' ���μ���ҳ��
        '''
        # INIT
        self.vRefreshNum = 0
        self.vMoveScrollNum = 0
        self.vRecordNum = 0

        # ����ҳ��
        msgInf('Getting: {}'.format(URL))
        self.vBrowser.get(URL)

        # �ȴ�ҳ��������
        self.waitForLoadMoreRecords()


    def loadPageByMoveScroll(self):
        ''' ͨ���ƶ�������������ҳ��
        '''
        vScrollPos = 0
        vFailedNum = 0
        while(True):
            # �ƶ�������
            msgInf('MoveScroll: {:0>2d}'.format(self.vMoveScrollNum + 1))
            vScrollPos += MOVE_SCROLL_SIZE
            self.vBrowser.execute_script('window.scrollTo(0, {});'.format(vScrollPos))

            # �ȴ�ҳ��������
            # �ƶ����������벻�������ҳ��ˢ��ʱ�����ܵ���ҳ�����ʧ��
            if (not self.waitForLoadMoreRecords()):
                vFailedNum += 1
                if (vFailedNum < 3): continue
                else: raise WebDriverException(MSG_LOAD_FAILED)

            # ����ҳ��
            self.parsePage()

            # �ӳٴ���
            time.sleep(CRAWL_DELAY)

            # ҳ��������
            self.vMoveScrollNum += 1
            msgDeg('Record Number: {}'.format(self.vRecordNum))
            if (self.vMoveScrollNum >= MOVE_SCROLL_NUM): break


    def loadPageByClickRefreshElement(self):
        ''' ͨ�����ˢ��Ԫ��������ҳ��
        '''
        vFailedNum = 0
        while(True):
            # ���ˢ��
            e = self.getRefreshElement()
            msgInf('ClickRefreshElement: {:0>2d}'.format(self.vRefreshNum + 1))
            e.click()
            
            # �ȴ�ҳ��������
            if (not self.waitForLoadMoreRecords()):
                vFailedNum += 1
                if (vFailedNum < 3): continue
                else: raise WebDriverException(MSG_LOAD_FAILED)

            # ����ҳ��
            self.parsePage()

            # ҳ��������
            self.vRefreshNum += 1
            msgDeg('Record Number: {}'.format(self.vRecordNum))
            if (self.vRefreshNum >= REFRESH_NUM): break

            # �ӳٴ���
            time.sleep(REFRESH_DELAY)


    def savePage(self, vPageSource):
        vOutputFile = os.path.join( \
            DIR_OUTPUT, \
            '{}_CacheFile.html'.format(self.vAppName) \
        )
        with open(vOutputFile, 'w', encoding='UTF-8') as f:
            f.write(vPageSource)


    def parsePage(self):
        # ȡ������
        vDomain = urlsplit(URL).netloc

        # ȡ��ҳ��
        # 2018-12-31 �滻��&nbsp;
        # ��ҳԴ������&nbsp;��utf-8�����ǣ�\xc2\xa0��
        # ת��ΪUnicode�ַ�Ϊ��\xa0������ʾ��DOS�����ϵ�ʱ��ת��ΪGBK������ַ�����
        # ����\xa0���Unicode�ַ�û�ж�Ӧ��GBK������ַ��������Գ��ִ���
        vHtml = self.vBrowser.page_source.replace('&nbsp;', ' ')
        self.savePage(vHtml)
        
        # ����ҳ��
        vSoup = BeautifulSoup(vHtml, 'lxml')
        
        # ����������
        vResultList = []

        # ȡ�������������У�������ÿ����������
        for vRecord in vSoup.select(CS_RECORD_GROUP):
            # ���ű���ڵ�(�б�)
            vNodeTitle = vRecord.select(CS_RECORD_TITLE)
            
            # �ж������Ƿ����ӵ�����
            # ������������򲻴���
            vHref = vNodeTitle[0].get('href').strip()
            if (vHref.startswith('http') and vDomain != urlsplit(vHref).netloc):
                continue
            
            vGroupId = vHref.split('/')[2]
            vTitle = vNodeTitle[0].get_text().strip()
    
            # �������Խڵ�(�б�)
            vNodeAttrs = vRecord.select(CS_RECORD_ATTRS)
            # �������Խڵ�(�б�)����
            #msgDeg('vNodeAttrs size: {}'.format(len(vNodeAttrs)))
            
            # ��������(���ͣ���Դ������)
            vNodeAttrs1 = vNodeAttrs[0].select(CS_RECORD_ATTRS_1)
            vSizeAttrs1 = len(vNodeAttrs1)
            
            
            # ����
            vKind = None
            if   (vSizeAttrs1 <= 2): continue
            elif (vSizeAttrs1 == 3):
                # ԭ��
                vKind = 'ԭ��'
                # ���б�ͷ����һ����Ԫ�أ���������͵�λ��
                vNodeAttrs1.insert(0, None)
            else:
                # ��ԭ��
                vKind = vNodeAttrs1[0].get_text().strip()


            # ��Դ(ȥ��ĩβ�޷�ʶ����ַ�)
            vSource = vNodeAttrs1[2].get_text()[:-1].strip()
            
            # ����(ȥ��ĩβ�޷�ʶ����ַ����Լ������ۡ�����)
            vComment = 0
            vCommentText = vNodeAttrs1[3].get_text()[:-1].strip()[:-2]

            # �����ԡ��򡯽�β������
            if (vCommentText.endswith('��')):
                vCommentText = vCommentText.rstrip('��')
                vCommentText = float(vCommentText) * 10000
              
            # ȡ�����۴���
            if (vCommentText):
                try: vComment = int(vCommentText)
                except: continue

            # ��������(����ʱ��)
            vNodeAttrs2 = vNodeAttrs[0].select(CS_RECORD_ATTRS_2)
            vUptime = vNodeAttrs2[0].get_text().strip()

            # ��ӡ��־
            #msgDeg('����:{}'.format(vKind))
            #msgDeg('��Դ:{}'.format(vSource))
            #msgDeg('����:{}'.format(vComment))
            #msgDeg('����:{}'.format(vUptime))
            
            # �ռ���Ϣ
            vFields = []
            vFields.append(vGroupId)
            vFields.append(vTitle)
            vFields.append(urljoin(URL, vHref))
            vFields.append(vKind)
            vFields.append(vComment)
            vFields.append(vUptime)
            vFields.append(vSource)
            vResultList.append(vFields)

        # ��������
        self.updateData(vResultList)


    def updateData(self, vResultList):
        ''' �����ݸ��µ����ݿ�
            �Ƚ����ݲ�����У�����������Ѵ��ڣ��͸������ۡ�
        '''
        vInsertSQL = 'INSERT INTO toutiao_news VALUES(%s,%s,%s,%s,%s,%s,%s,%s)'
        vUpdateSQL = 'UPDATE toutiao_news SET comment=%s WHERE id=%s'

        self.vDB.connect()
        try:
            self.vDB.lock('toutiao_news')
            for vItems in vResultList:
                # �����¼�¼�����ݿ�
                try:
                    self.vDB.execute(vInsertSQL, *vItems, datetime.now())
                    self.vInsertNum += 1
                # �ü�¼�Ѵ��ڣ���������
                except DBApiError:
                    self.vDB.execute(vUpdateSQL, vItems[4], vItems[0])
            self.vDB.commit()
            self.vDB.unlock()

        finally:
            self.vDB.close()


    # ��������
    def procArgv(self): return True

    # ������
    def main(self):
        self.getUrl()
        self.loadPageByMoveScroll()
        self.loadPageByClickRefreshElement()

    # ����������
    def report(self):
        msgInf('Records: {}'.format(self.vRecordNum))
        msgInf('Inserts: {}'.format(self.vInsertNum))


# ִ��
if (__name__ == '__main__'):
    ToutiaoCrawls().run()
