#!python
# coding: gbk
#----------------------------------------
# DownloadQueue.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
from datetime import datetime
from datetime import timedelta

from util.db.MysqlDBApi import MysqlDBApi as DBApi
from util.db.MysqlDBApi import DBApiError


OUTSTANDING = 0
PROCESSING  = 1
COMPLETE    = 2

PROCESS_TIMEOUT = 60

SQL_CREATE_TABLE = '''
    CREATE TABLE dlqueue(
        url         VARCHAR(256) NOT NULL,
        domain      VARCHAR(128) NOT NULL,
        depth       INT NOT NULL,
        old_url     VARCHAR(256),
        old_link    VARCHAR(256),
        status      INT NOT NULL,
        update_ts   DATETIME,
        PRIMARY KEY(url)
    )
'''

class DownloadQueue:
    ''' ���ض��У�
        ���ƶ������ͬʱ���صĶ��С�
        �ʺ϶��̴߳���
    '''
    def __init__(self, vMysqlConf):
        # ���ݿ�
        self.vDB = DBApi(vMysqlConf)

        # �½���
        self.vDB.connect()
        try: self.vDB.execute(SQL_CREATE_TABLE)
        # ���Ѿ�����ʱ����������
        except DBApiError: pass
        finally: self.vDB.close()


    def push(self, vQueryList):
        ''' ���µ�URL������У�
            �����URL�Ѿ����ڣ���������
            ����Ͳ����µļ�¼��
            vQuery: vUrl, vDomain, vDepth, vOldUrl, vOldList
        '''
        self.vDB.connect()
        try:
            self.vDB.lock('dlqueue')
            
            # ��������
            vUpdateTS = datetime.now()
            for vQuery in vQueryList:
                try:
                    self.vDB.execute(\
                        'INSERT INTO dlqueue VALUES(%s, %s, %s, %s, %s, %s, %s)', \
                        *vQuery, OUTSTANDING, vUpdateTS \
                    )
                # �����Ѿ�����ʱ����������
                except DBApiError: pass
            
            self.vDB.commit()
            self.vDB.unlock()

        finally:
            self.vDB.close()


    def pop(self, vMaxDepth=None, vDomain=None):
        ''' ȡ�ò�����δ����(OUTSTANDING)��URL��¼��������״̬��Ϊ������(PROCESSING)��
            �ü�¼����Ȳ��ܳ���������(С��������)
            ���û�з���δ����ļ�¼���ͼ�鴦���е������Ƿ�ʱ��
            �����ʱ���ͱ�Ϊδ�����״̬��
        '''
        self.vDB.connect()
        try:
            self.vDB.lock('dlqueue')
            
            # ȡ��һ��δ���������
            vSQL = 'SELECT url, depth FROM dlqueue WHERE status=%s '
            vQuery = [OUTSTANDING, ]

            if (vMaxDepth):
                vSQL += 'and depth<%s '
                vQuery.append(vMaxDepth)

            if (vDomain):
                vSQL += 'and domain=%s '
                vQuery.append(vDomain)

            self.vDB.execute(vSQL, *vQuery)
            vRecord = self.vDB.fetchone()
            if (vRecord):
                vUrl, vDepth = vRecord
                # �������ݵ�״̬��Ϊ������
                self.vDB.execute(\
                    'UPDATE dlqueue SET status=%s, update_ts=%s WHERE url=%s', \
                    PROCESSING, datetime.now(), vUrl \
                )
                self.vDB.commit()
                self.vDB.unlock()
                return (vUrl, vDepth)
    
            else:
                # ����Ƿ��г�ʱ������(ֱ�Ӹ���)
                self.vDB.execute(\
                    'UPDATE dlqueue SET status=%s WHERE status=%s AND update_ts<%s', \
                    OUTSTANDING, PROCESSING, datetime.now()-timedelta(seconds=PROCESS_TIMEOUT) \
                )
                self.vDB.commit()
                self.vDB.unlock()
                raise IndexError('Empty DownloadQueue.')

        finally:
            self.vDB.close()


    def complete(self, vUrl):
        ''' ������أ�����״̬��Ϊ�������(COMPLETE)
        '''
        self.vDB.connect()
        try:
            self.vDB.lock('dlqueue')
            self.vDB.execute(\
                'UPDATE dlqueue SET status=%s WHERE url=%s', \
                COMPLETE, vUrl \
            )
            self.vDB.commit()
            self.vDB.unlock()
        finally:
            self.vDB.close()


    def reset(self, vUrl=None, vDomain=None):
        ''' ��������
            ע�⣺�ڶ������ͬʱץȡʱ��������øù��ܡ�
        '''
        self.vDB.connect()
        try:
            vSQL = 'UPDATE dlqueue SET status=%s WHERE '
            vQuery = [OUTSTANDING, ]

            if (vUrl):
                vSQL += 'url=%s'
                vQuery.append(vUrl)
            elif (vDomain):
                vSQL += 'domain=%s'
                vQuery.append(vDomain)
            else:
                raise TypeError('����vUrl��vDomain������ֻ��ָ������һ����')

            self.vDB.execute(vSQL, *vQuery)
            self.vDB.commit()

        finally:
            self.vDB.close()


    def delete(self, vDomain=None):
        ''' ������ض���
            �����ؿ�ʼǰ��Ҫ��ִ����ն��в������磺
                from util.crawl.DownloadQueue import DownloadQueue as DQ
                DQ().delete()
                DQ().delete(vDomain)
        '''
        self.vDB.connect()
        try:
            self.vDB.lock('dlqueue')

            vSQL = 'DELETE FROM dlqueue '
            vQuery = []
            if (vDomain):
                vSQL += 'where domain=%s'
                vQuery.append(vDomain)
            self.vDB.execute(vSQL, *vQuery)

            self.vDB.commit()
            self.vDB.unlock()

        finally:
            self.vDB.close()

