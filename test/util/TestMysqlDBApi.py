#!python
# coding: gbk
#----------------------------------------
# TestMysqlDBApi.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import time
import unittest
from datetime import datetime

from util.Common import msgInf, msgExp

from util.db.MysqlDBApi import MysqlDBApi as DBApi
from util.db.MysqlDBApi import DBApiError


MYSQL_CONF = {
    'host':    'localhost',
    'port':    3306,
    'user':    'Pywork',
    'passwd':  'Pywork2019+',
    'db':      'pywork',
    'charset': 'UTF8',
}


class TestMysqlDBApi(unittest.TestCase):

    def setUp(self):
        db = DBApi(MYSQL_CONF)
        try:
            db.execute('''
                CREATE TABLE pytest(id CHAR(3), update_ts DATETIME, PRIMARY KEY(id))
            ''')
        except DBApiError: pass
        finally: db.close()

    def tearDown(self):
        pass


    def test_Main(self):
        db = DBApi(MYSQL_CONF)
        try:
            # Lock Table
            db.lock('pytest')
            msgInf('Table pytest is locked.')
            
            vDeleteSQL = 'DELETE FROM pytest'
            vSelectSQL = 'SELECT * FROM pytest'
            
            # --- Delete Data ---
            db.execute(vDeleteSQL)
            db.commit()
            time.sleep(2)
            
            # --- Select Data ---
            db.execute(vSelectSQL)
            # 确保取得数据的件数是对的
            self.assertEqual(len(db.fetchall()), 0)


            # --- Insert Data ---
            for i in range(5):
                db.execute( \
                    'INSERT INTO pytest VALUES(%s,%s)', \
                    '{:03d}'.format(i+1), \
                    datetime.now() \
                )
                time.sleep(2)
            db.commit()


            # --- Select Data ---
            db.execute(vSelectSQL)
            vRecordList = db.fetchall()
            
            # 确保取得数据的件数是对的
            self.assertEqual(len(vRecordList), 5)
            
            # 表示数据
            for vRecord in vRecordList:
                msgInf(str(vRecord))
                time.sleep(2)


            # --- Delete Data ---
            db.execute(vDeleteSQL)
            db.commit()
            time.sleep(2)

            # --- Select Data ---
            db.execute(vSelectSQL)
            # 确保取得数据的件数是对的
            self.assertEqual(len(db.fetchall()), 0)

            # Unlock Table
            db.unlock()
            msgInf('Table pytest is unlocked.')

        finally:
            db.close()


# 执行
if (__name__ == '__main__'):
    unittest.main()
