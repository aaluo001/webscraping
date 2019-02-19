#!python
# coding: gbk
#----------------------------------------
# TestDownloadQueue.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import unittest
import time

from util.DownloadQueue import DownloadQueue as DQ
from util.DownloadQueue import OUTSTANDING
from util.DownloadQueue import PROCESSING
from util.DownloadQueue import COMPLETE

from util.db.MysqlDBApi import MysqlDBApi as DBApi
from util.db.MysqlDBApi import DBApiError


URL1 = 'http://www.pytest01.com/{}'
URL2 = 'http://www.pytest02.com/{}'
URL3 = 'http://www.pytest03.com/{}'

DOMAIN1 = 'www.pytest01.com'
DOMAIN2 = 'www.pytest02.com'
DOMAIN3 = 'www.pytest03.com'

MAX_RECORD = 5

MYSQL_CONF = {
    'host':    'localhost',
    'port':    3306,
    'user':    'Pywork',
    'passwd':  'Pywork2019+',
    'db':      'pywork',
    'charset': 'UTF8',
}


class TestDownloadQueue(unittest.TestCase):

    def setUp(self):
        self.vDB = DBApi(MYSQL_CONF)
        self.vQueue = DQ(MYSQL_CONF)
        self.vQueue.push([ (URL1.format(i), DOMAIN1, 1, None, None) for i in range(MAX_RECORD) ])
        self.vQueue.push([ (URL2.format(i), DOMAIN2, 2, 'http://test.com', '/this') for i in range(MAX_RECORD) ])
        self.vQueue.push([ (URL3.format(i), DOMAIN3, 3, None, None) for i in range(MAX_RECORD) ])

    def tearDown(self):
        self.vQueue.delete()

    def getRecordList(self, vDomain=None):
        vSQL = 'SELECT * FROM dlqueue '
        vQuery = []
        
        if (vDomain):
            vSQL += 'WHERE domain=%s'
            vQuery.append(vDomain)

        self.vDB.connect()
        try:
            self.vDB.execute(vSQL, *vQuery)
            return self.vDB.fetchall()
        finally:
            self.vDB.close()


    def test_FunctionPush(self):
        vRecordList = self.getRecordList()
        self.assertEqual(len(vRecordList), MAX_RECORD * 3)

        vRecordList = self.getRecordList(DOMAIN1)
        self.assertEqual(len(vRecordList), MAX_RECORD)
        vUrlList = [ vRecord[0] for vRecord in vRecordList ]
        for i, vRecord in enumerate(vRecordList):
            self.assertIn(URL1.format(i), vUrlList)
            self.assertEqual(vRecord[1], DOMAIN1)
            self.assertEqual(vRecord[2], 1)
            self.assertIsNone(vRecord[3])
            self.assertIsNone(vRecord[4])
            self.assertEqual(vRecord[5], OUTSTANDING)

        vRecordList = self.getRecordList(DOMAIN2)
        self.assertEqual(len(vRecordList), MAX_RECORD)
        vUrlList = [ vRecord[0] for vRecord in vRecordList ]
        for i, vRecord in enumerate(vRecordList):
            self.assertIn(URL2.format(i), vUrlList)
            self.assertEqual(vRecord[1], DOMAIN2)
            self.assertEqual(vRecord[2], 2)
            self.assertEqual(vRecord[3], 'http://test.com')
            self.assertEqual(vRecord[4], '/this')
            self.assertEqual(vRecord[5], OUTSTANDING)


    def test_FunctionPop(self):
        pass
        
        
    def test_FunctionComplete(self):
        pass
        

    def test_FunctionReset(self):
        pass
        
        
    def test_FunctionDeleteByDomain(self):
        self.vQueue.delete(DOMAIN3)
        vRecordList = self.getRecordList(DOMAIN3)
        self.assertEqual(len(vRecordList), 0)
        vRecordList = self.getRecordList(DOMAIN1)
        self.assertEqual(len(vRecordList), MAX_RECORD)
        
        self.vQueue.delete(DOMAIN1)
        vRecordList = self.getRecordList(DOMAIN1)
        self.assertEqual(len(vRecordList), 0)
        vRecordList = self.getRecordList(DOMAIN2)
        self.assertEqual(len(vRecordList), MAX_RECORD)

        self.vQueue.delete(DOMAIN2)
        vRecordList = self.getRecordList(DOMAIN2)
        self.assertEqual(len(vRecordList), 0)


    def test_FunctionDeleteAll(self):
        self.vQueue.delete()
        vRecordList = self.getRecordList()
        self.assertEqual(len(vRecordList), 0)


# 执行
if (__name__ == '__main__'):
    unittest.main()
