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
        self.vDB = DBApi(MYSQL_CONF)

        try:
            self.vDB.connect()
        except DBApiError as e:
            msgExp(e)
            self.vDB = None
            return

        try:
            self.vDB.execute('''
                CREATE TABLE pytest(id CHAR(3), update_ts DATETIME, PRIMARY KEY(id))
            ''')
        except DBApiError:
            msgInf('Table pytest has aleady exist.')
        else:
            msgInf('Created table pytest.')
        finally:
            self.vDB.close()


    def tearDown(self):
        pass


    def test_main(self):
        # 确保数据库连接成功
        self.assertIsNotNone(self.vDB)
        
        self.vDB.connect()
        try:
            # Lock Table
            self.vDB.lock('pytest')
            msgInf('Table pytest is locked.')
            
            vDeleteSQL = 'DELETE FROM pytest'
            vSelectSQL = 'SELECT * FROM pytest'
            
            # --- Delete Data ---
            self.vDB.execute(vDeleteSQL)
            self.vDB.commit()
            time.sleep(2)
            
            # --- Select Data ---
            self.vDB.execute(vSelectSQL)
            # 确保取得数据的件数是对的
            self.assertEqual(len(self.vDB.fetchall()), 0)


            # --- Insert Data ---
            for i in range(5):
                self.vDB.execute( \
                    'INSERT INTO pytest VALUES(%s,%s)', \
                    '{:03d}'.format(i+1), \
                    datetime.now() \
                )
                time.sleep(2)
            self.vDB.commit()


            # --- Select Data ---
            self.vDB.execute(vSelectSQL)
            vRecordList = self.vDB.fetchall()
            
            # 确保取得数据的件数是对的
            self.assertEqual(len(vRecordList), 5)
            
            # 表示数据
            for vRecord in vRecordList:
                msgInf(str(vRecord))
                time.sleep(2)


            # --- Delete Data ---
            self.vDB.execute(vDeleteSQL)
            self.vDB.commit()
            time.sleep(2)

            # --- Select Data ---
            self.vDB.execute(vSelectSQL)
            # 确保取得数据的件数是对的
            self.assertEqual(len(self.vDB.fetchall()), 0)

            # Unlock Table
            self.vDB.unlock()
            msgInf('Table pytest is unlocked.')

        finally:
            self.vDB.close()


# 执行
if (__name__ == '__main__'):
    unittest.main()
