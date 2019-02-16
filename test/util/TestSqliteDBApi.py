#!python
# coding: gbk
#----------------------------------------
# TestSqliteDBApi.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import os
import unittest
from datetime import datetime

from util.Common import msgInf

from util.db.SqliteDBApi import SqliteDBApi as DBApi
from util.db.SqliteDBApi import DBApiError


class TestSqliteDBApi(unittest.TestCase):

    def setUp(self):
        self.vDBFile = os.path.join( \
            os.path.dirname(os.path.abspath(__file__)), \
            'pywork.db' \
        )
        vSqliteConf = {
            'database': self.vDBFile,
        }
        self.vDB = DBApi(vSqliteConf)

        self.vDB.connect()
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
        os.remove(self.vDBFile)


    def test_main(self):
        # 确保数据库连接成功
        self.assertTrue( \
            os.path.exists(self.vDBFile), \
            'No such file: {}'.format(self.vDBFile) \
        )
        
        self.vDB.connect()
        try:
            vDeleteSQL = 'DELETE FROM pytest'
            vSelectSQL = 'SELECT * FROM pytest'
            
            # --- Delete Data ---
            self.vDB.execute(vDeleteSQL)
            self.vDB.commit()
            
            # --- Select Data ---
            self.vDB.execute(vSelectSQL)
            # 确保取得数据的件数是对的
            self.assertEqual(len(self.vDB.fetchall()), 0)


            # --- Insert Data ---
            for i in range(5):
                self.vDB.execute( \
                    'INSERT INTO pytest VALUES(?, ?)', \
                    '{:03d}'.format(i+1), \
                    datetime.now() \
                )
            self.vDB.commit()


            # --- Select Data ---
            self.vDB.execute(vSelectSQL)
            vRecordList = self.vDB.fetchall()
            
            # 确保取得数据的件数是对的
            self.assertEqual(len(vRecordList), 5)
            
            # 表示数据
            for vRecord in vRecordList:
                msgInf(str(vRecord))


            # --- Delete Data ---
            self.vDB.execute(vDeleteSQL)
            self.vDB.commit()

            # --- Select Data ---
            self.vDB.execute(vSelectSQL)
            # 确保取得数据的件数是对的
            self.assertEqual(len(self.vDB.fetchall()), 0)

        finally:
            self.vDB.close()


# 执行
if (__name__ == '__main__'):
    unittest.main()
