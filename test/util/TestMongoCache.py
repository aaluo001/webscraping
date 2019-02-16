#!python
# coding: gbk
#----------------------------------------
# TestMongoCache.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import unittest, time
from datetime import timedelta
from urllib.parse import urlparse

from util.cache.MongoCache import MongoCache


URL = 'http://www.pytest.com/'
DOMAIN = urlparse(URL).netloc
MAX_NUM = 11


class TestMongoCache(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_SetItemAndGetItem(self):
        mc = MongoCache()
        mc.delete(DOMAIN)

        vUrl = URL + '{}'
        for i in range(MAX_NUM):
            mc[vUrl.format(i)] = 'TestContent: {:02d}'.format(i)

        for i in range(MAX_NUM):
            vHtml = mc[vUrl.format(i)]
            self.assertEqual(vHtml, 'TestContent: {:02d}'.format(i))


    def test_DoseNotExists(self):
        mc = MongoCache()
        mc.delete(DOMAIN)

        try:
            mc[URL]
        except IndexError as e:
            self.assertEqual(str(e), URL + ': Dose not exist.')


    def test_HasExpired(self):
        mc = MongoCache(timedelta(seconds=1))
        mc.delete(DOMAIN)

        mc[URL] = 'TestContent'
        time.sleep(2)

        try:
            mc[URL]
        except IndexError as e:
            self.assertEqual(str(e), URL + ': Has expired.')



# 执行
if (__name__ == '__main__'):
  unittest.main()
