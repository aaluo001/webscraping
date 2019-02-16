#!python
# coding: gbk
#----------------------------------------
# MysqlDBApi.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import pymysql
from util.db.BaseDBApi import BaseDBApi


DBApiError = pymysql.err.DatabaseError

class MysqlDBApi(BaseDBApi):
    def __init__(self, vMysqlConf):
        ''' 链接数据库(MySQL)
            使用方法：
                # 导入MysqlDBApi
                from util.db.MysqlDBApi import MysqlDBApi as DBApi
                from util.db.MysqlDBApi import DBApiError

                # 初始化MysqlDBApi
                vMysqlConf = {
                    'host':    'localhost',
                    'port':    3306,
                    'user':    'Pywork',
                    'passwd':  'Pywork2019+',
                    'db':      'pywork',
                    'charset': 'UTF8',
                }
                db = DBApi(vMysqlConf)

                # 使用MysqlDBApi
                db.connect()
                try:
                    db.lock('pytest')
                    db.execute('SELECT * FROM pytest WHERE id=%s AND update_ts=%s', '00001', '2019-01-12 10:10:30')
                    db.execute('UPDATE pytest SET update_ts=%s WHERE id=%s', datetime.now(), '00001')
                    db.commit()
                    db.unlock()
                finally:
                    db.close()
        '''
        super().__init__()
        self.vMysqlConf = vMysqlConf


    def connect(self):
        self.vConn = pymysql.connect(**self.vMysqlConf)
        self.vCurs = self.vConn.cursor()
        self.setAutoCommit(False)


    def setAutoCommit(self, vAutoCommit=True):
        self.vConn.autocommit(vAutoCommit)

    def lock(self, vTable, vType=1):
        ''' 锁表
            vTable: 表名
            vType: 0=READ, 1=WRITE
        '''
        vLockType = 'WRITE' if vType==1 else 'READ'
        self.execute('LOCK TABLES {} {}'.format(vTable, vLockType))

    def unlock(self):
        self.execute('UNLOCK TABLES')

