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
    def __init__(self, vDBApiConf):
        self.vDBApiConf = vDBApiConf
        self.initTable()

    def getDBApi(self):
        return DBApi(self.vDBApiConf)

    def initTable(self):
        # �½���
        db = self.getDBApi()
        try: db.execute(SQL_CREATE_TABLE)
        # ���Ѿ�����ʱ����������
        except DBApiError: pass
        finally: db.close()


    def push(self, vQueryList):
        ''' ���µ�URL������У�
            �����URL�Ѿ����ڣ���������
            ����Ͳ����µļ�¼��
            vQuery: vUrl, vDomain, vDepth, vOldUrl, vOldList
        '''
        db = self.getDBApi()
        try:
            db.lock('dlqueue')
            # ��������
            vUpdateTS = datetime.now()
            for vQuery in vQueryList:
                try:
                    db.execute(\
                        'INSERT INTO dlqueue VALUES(%s, %s, %s, %s, %s, %s, %s)', \
                        *vQuery, OUTSTANDING, vUpdateTS \
                    )
                # �����Ѿ�����ʱ����������
                except DBApiError: pass
            db.commit()
            db.unlock()
        finally:
            db.close()


    def pop(self, vMaxDepth=None, vDomain=None):
        ''' ȡ�ò�����δ����(OUTSTANDING)��URL��¼��������״̬��Ϊ������(PROCESSING)��
            �ü�¼����Ȳ��ܳ���������(С��������)
            ���û�з���δ����ļ�¼���ͼ�鴦���е������Ƿ�ʱ��
            �����ʱ���ͱ�Ϊδ�����״̬��
        '''
        db = self.getDBApi()
        try:
            db.lock('dlqueue')
            
            # ȡ��һ��δ���������
            vSQL = 'SELECT url, depth FROM dlqueue WHERE status=%s '
            vQuery = [OUTSTANDING, ]

            if (vMaxDepth):
                vSQL += 'and depth<%s '
                vQuery.append(vMaxDepth)

            if (vDomain):
                vSQL += 'and domain=%s '
                vQuery.append(vDomain)

            db.execute(vSQL, *vQuery)
            vRecord = db.fetchone()
            if (vRecord):
                vUrl, vDepth = vRecord
                # �������ݵ�״̬��Ϊ������
                db.execute(\
                    'UPDATE dlqueue SET status=%s, update_ts=%s WHERE url=%s', \
                    PROCESSING, datetime.now(), vUrl \
                )
                db.commit()
                db.unlock()
                return (vUrl, vDepth)
    
            else:
                # ����Ƿ��г�ʱ������(ֱ�Ӹ���)
                db.execute(\
                    'UPDATE dlqueue SET status=%s WHERE status=%s AND update_ts<%s', \
                    OUTSTANDING, PROCESSING, datetime.now()-timedelta(seconds=PROCESS_TIMEOUT) \
                )
                db.commit()
                db.unlock()
                raise IndexError('Empty Queue.')

        finally:
            db.close()


    def complete(self, vUrl):
        ''' ������أ�����״̬��Ϊ�������(COMPLETE)
        '''
        db = self.getDBApi()
        try:
            db.lock('dlqueue')
            db.execute(\
                'UPDATE dlqueue SET status=%s WHERE url=%s', \
                COMPLETE, vUrl \
            )
            db.commit()
            db.unlock()
        finally:
            db.close()


    def reset(self, vUrl=None, vDomain=None):
        ''' ��������
            ע�⣺�ڶ������ͬʱץȡʱ��������øù��ܡ�
        '''
        db = self.getDBApi()
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

            db.execute(vSQL, *vQuery)
            db.commit()

        finally:
            db.close()


    def delete(self, vDomain=None):
        ''' ������ض���
            �����ؿ�ʼǰ��Ҫ��ִ����ն��в������磺
                from util.crawl.DownloadQueue import DownloadQueue as DQ
                DQ().delete()
                DQ().delete(vDomain)
        '''
        db = self.getDBApi()
        try:
            db.lock('dlqueue')
            vSQL = 'DELETE FROM dlqueue '
            vQuery = []
            if (vDomain):
                vSQL += 'where domain=%s'
                vQuery.append(vDomain)
            db.execute(vSQL, *vQuery)
            db.commit()
            db.unlock()
        finally:
            db.close()

