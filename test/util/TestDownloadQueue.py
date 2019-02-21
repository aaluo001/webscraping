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

from util.DownloadQueue import DownloadQueue
from util.DownloadQueue import OUTSTANDING
from util.DownloadQueue import PROCESSING
from util.DownloadQueue import COMPLETE


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
        self.vDQueue = DownloadQueue(MYSQL_CONF)
        self.vDQueue.push([ (URL1.format(i), DOMAIN1, 1, None, None) for i in range(MAX_RECORD) ])
        self.vDQueue.push([ (URL2.format(i), DOMAIN2, 2, 'http://test.com', '/this') for i in range(MAX_RECORD) ])
        self.vDQueue.push([ (URL3.format(i), DOMAIN3, 3, None, None) for i in range(MAX_RECORD) ])

    def tearDown(self):
        self.vDQueue.delete()

    def getRecordList(self, vDomain=None):
        vSQL = 'SELECT * FROM dlqueue '
        vQuery = []
        
        if (vDomain):
            vSQL += 'WHERE domain=%s'
            vQuery.append(vDomain)

        db = self.vDQueue.getDBApi()
        try:
            db.execute(vSQL, *vQuery)
            return db.fetchall()
        finally:
            db.close()


    def test_Push(self):
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


    def test_Pop(self):
        pass


    def test_Complete(self):
        vRecordList = self.getRecordList()
        vTestUrls = [ vRecord[0] for vRecord in vRecordList[5:11] ]
        for vUrl in vTestUrls:
            self.vDQueue.complete(vUrl)

        vRecordList = self.getRecordList()
        for vRecord in vRecordList:
            if (vRecord[0] in vTestUrls):
                self.assertEqual(vRecord[5], COMPLETE)
            else:
                self.assertEqual(vRecord[5], OUTSTANDING)


    def test_ResetByUrl(self):
        pass

    def test_ResetByDomain(self):
        pass

    def test_ResetAll(self):
        try:
            self.vDQueue.reset()
        except TypeError as e:
            self.assertEqual(str(e), '参数vUrl和vDomain必须且只能指定其中一个！')


    def test_DeleteByDomain(self):
        self.vDQueue.delete(DOMAIN3)
        vRecordList = self.getRecordList(DOMAIN1)
        self.assertEqual(len(vRecordList), MAX_RECORD)
        vRecordList = self.getRecordList(DOMAIN3)
        self.assertEqual(len(vRecordList), 0)

        self.vDQueue.delete(DOMAIN1)
        vRecordList = self.getRecordList(DOMAIN1)
        self.assertEqual(len(vRecordList), 0)
        vRecordList = self.getRecordList(DOMAIN2)
        self.assertEqual(len(vRecordList), MAX_RECORD)

        self.vDQueue.delete(DOMAIN2)
        vRecordList = self.getRecordList(DOMAIN2)
        self.assertEqual(len(vRecordList), 0)


    def test_DeleteAll(self):
        self.vDQueue.delete()
        vRecordList = self.getRecordList()
        self.assertEqual(len(vRecordList), 0)


# 执行
if (__name__ == '__main__'):
    unittest.main()
