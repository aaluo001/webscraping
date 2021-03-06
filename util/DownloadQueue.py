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
    ''' 下载队列：
        控制多个进程同时下载的队列。
        适合多线程处理。
    '''
    def __init__(self, vDBApiConf):
        self.vDBApiConf = vDBApiConf
        self.initTable()

    def getDBApi(self):
        return DBApi(self.vDBApiConf)

    def initTable(self):
        # 新建表
        db = self.getDBApi()
        try: db.execute(SQL_CREATE_TABLE)
        # 表已经存在时，不作处理
        except DBApiError: pass
        finally: db.close()


    def push(self, vQueryList):
        ''' 将新的URL加入队列：
            如果该URL已经存在，则不作处理，
            否则就插入新的记录。
            vQuery: vUrl, vDomain, vDepth, vOldUrl, vOldList
        '''
        db = self.getDBApi()
        try:
            db.lock('dlqueue')
            # 插入数据
            vUpdateTS = datetime.now()
            for vQuery in vQueryList:
                try:
                    db.execute(\
                        'INSERT INTO dlqueue VALUES(%s, %s, %s, %s, %s, %s, %s)', \
                        *vQuery, OUTSTANDING, vUpdateTS \
                    )
                # 数据已经存在时，不作处理
                except DBApiError: pass
            db.commit()
            db.unlock()
        finally:
            db.close()


    def pop(self, vMaxDepth=None, vDomain=None):
        ''' 取得并锁定未处理(OUTSTANDING)的URL记录，并将其状态变为处理中(PROCESSING)。
            该记录的深度不能超过最大深度(小于最大深度)
            如果没有发现未处理的记录，就检查处理中的数据是否超时。
            如果超时，就变为未处理的状态。
        '''
        db = self.getDBApi()
        try:
            db.lock('dlqueue')
            
            # 取得一条未处理的数据
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
                # 将该数据的状态变为处理中
                db.execute(\
                    'UPDATE dlqueue SET status=%s, update_ts=%s WHERE url=%s', \
                    PROCESSING, datetime.now(), vUrl \
                )
                db.commit()
                db.unlock()
                return (vUrl, vDepth)
    
            else:
                # 检查是否有超时的数据(直接更新)
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
        ''' 完成下载，将其状态变为处理完成(COMPLETE)
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
        ''' 重新下载
            注意：在多个进程同时抓取时，必须禁用该功能。
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
                raise TypeError('参数vUrl和vDomain必须且只能指定其中一个！')

            db.execute(vSQL, *vQuery)
            db.commit()

        finally:
            db.close()


    def delete(self, vDomain=None):
        ''' 清空下载队列
            在下载开始前，要先执行清空队列操作，如：
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

