#!python
# coding: gbk
#----------------------------------------
# TestLog.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import os, logging
import unittest

from Setting import LOG_FILE
from util.Log import Log
from util.Common import clearLogContent, getLogContent


class TestLog(unittest.TestCase):

    def test_LogFile(self):
        self.assertTrue( \
            LOG_FILE.endswith(r'webscraping\output\webscraping.log'), \
            'LogFile: {}'.format(LOG_FILE) \
        )


    def test_DebugMode(self):
        # 设置
        vLog = Log(vLogFile=LOG_FILE, vLogLevel=logging.DEBUG)
        for i in range(2): vLog.debug('Debug Test {}'.format(i))
        for i in range(5): vLog.info('Info Test {}'.format(i))
        for i in range(3): vLog.warning('Warning Test {}'.format(i))
        for i in range(1): vLog.error('Error Test {}'.format(i))

        # 使用
        vLogContent = vLog.getLogs()
        vActionID = vLogContent['action_id']
        vDebugs   = vLogContent['debugs']
        vInfos    = vLogContent['infos']
        vWarnings = vLogContent['warnings']
        vErrors   = vLogContent['errors']

        # 断言
        self.assertEqual(vActionID, vLog.vActionID)
        for i in range(2): self.assertIn('Debug Test {}'.format(i), [ vVal['message'] for vVal in vDebugs ])
        for i in range(5): self.assertIn('Info Test {}'.format(i), [ vVal['message'] for vVal in vInfos ])
        for i in range(3): self.assertIn('Warning Test {}'.format(i), [ vVal['message'] for vVal in vWarnings ])
        for i in range(1): self.assertIn('Error Test {}'.format(i), [ vVal['message'] for vVal in vErrors ])


    def test_Exception(self):
        clearLogContent()
        vLog = Log(vLogFile=LOG_FILE, vLogLevel=logging.DEBUG)
        try:
            [][1]
        except IndexError as e:
            vLog.exception(e)
            vText = getLogContent()
            self.assertIn('Traceback (most recent call last):', vText)
            self.assertIn(str(e), vText)


# 执行
if (__name__ == '__main__'):
    unittest.main()

