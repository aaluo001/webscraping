#!python
# coding: gbk
#----------------------------------------
# SqliteDBApi.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import sqlite3
from util.db.BaseDBApi import BaseDBApi


DBApiError = sqlite3.DatabaseError

class SqliteDBApi(BaseDBApi):
    def __init__(self, vSqliteConf):
        ''' �������ݿ�(SQLite)
            ע�⣺Ĭ�����ֶ�Commit
            ʹ�÷�����
                # ����SqliteDBApi
                from util.db.SqliteDBApi import SqliteDBApi as DBApi
                from util.db.SqliteDBApi import DBApiError
                
                
                # ��ʼ��SqliteDBApi
                vSqliteConf = {
                    'database': os.path.join(DIR_OUTPUT, 'pywork.db')
                }
                db = SqliteDBApi(vSqliteConf)
                
                # ʹ��SqliteDBApi
                db.connect()
                try:
                    db.execute('SELECT * FROM pytest WHERE id=%s AND update_ts=%s', '00001', '2019-01-12 10:10:30')
                    db.execute('UPDATE pytest SET update_ts=%s WHERE id=%s', datetime.now(), '00001')
                    db.commit()
                finally:
                    db.close()
        '''
        super().__init__()
        self.vSqliteConf = vSqliteConf
    
    def connect(self):
        self.vConn = sqlite3.connect(**self.vSqliteConf)
        self.vCurs = self.vConn.cursor()

