#!python
# coding: gbk
#----------------------------------------
# TestDownloadQueue.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import unittest
import time, threading

from util.DownloadQueue import DownloadQueue as DQ
from util.db.MysqlDBApi import MysqlDBApi as DBApi
from util.db.MysqlDBApi import DBApiError


URL = 'http://www.pytest.com/{}'
DOMAIN = 'www.pytest.com'
MAX_THREAD = 5
MAX_RECORD = 20

MYSQL_CONF = {
    'host':    'localhost',
    'port':    3306,
    'user':    'Pywork',
    'passwd':  'Pywork2019+',
    'db':      'pywork',
    'charset': 'UTF8',
}

SQL_COUNT = 'SELECT COUNT(*) FROM dlqueue;'


class TestDownloadQueue(unittest.TestCase):

    def setUp(self):
        self.vDB = DBApi(MYSQL_CONF)
        self.vQueue = DQ(MYSQL_CONF)
        self.vQueue.delete()

    def tearDown(self):
        self.vQueue.delete()


    def test_Main(self):
        self.vQueue.push([ (URL.format(i), DOMAIN, 0, None, None) for i in range(MAX_RECORD) ])
        self.vDB.connect()
        try:
            self.vDB.execute(SQL_COUNT)
            vCount = self.vDB.fetchone()[0]
            self.assertEqual(vCount, MAX_RECORD)
        finally:
            self.vDB.close()

        self.vQueue.delete()
        self.vDB.connect()
        try:
            self.vDB.execute(SQL_COUNT)
            vCount = self.vDB.fetchone()[0]
            self.assertEqual(vCount, 0)
        finally:
            self.vDB.close()


# 执行
if (__name__ == '__main__'):
    unittest.main()
