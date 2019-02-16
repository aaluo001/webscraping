#!python
# coding: gbk
#----------------------------------------
# TestCommon.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import os, logging
import unittest
import time
from datetime import datetime

from Setting import LOG_LEVEL, DIR_OUTPUT
from util.Common import msgDeg, msgInf, msgWrn, msgErr, getLogs
from util.Common import toCsv, timeUsed
from util.Common import clearLogContent, getLogContent
from util.Common import msgExp


class TestCommon(unittest.TestCase):

    def test_MsgFuncs(self):
        # 确保Setting.py中的LOG_LEVEL=logging.INFO
        self.assertEqual(LOG_LEVEL, logging.INFO)

        # 设置
        for i in range(2): msgDeg('Debug Message Test {}'.format(i))
        for i in range(7): msgInf('Info Message Test {}'.format(i))
        for i in range(1): msgWrn('Warning Message Test {}'.format(i))
        for i in range(3): msgErr('Error Message Test {}'.format(i))

        # 使用
        vLogContent = getLogs()
        vDebugs   = vLogContent['debugs']
        vInfos    = vLogContent['infos']
        vWarnings = vLogContent['warnings']
        vErrors   = vLogContent['errors']

        # 断言
        for i in range(2): self.assertNotIn('Debug Message Test {}'.format(i), [ vVal['message'] for vVal in vDebugs ])
        for i in range(7): self.assertIn('Info Message Test {}'.format(i), [ vVal['message'] for vVal in vInfos ])
        for i in range(1): self.assertIn('Warning Message Test {}'.format(i), [ vVal['message'] for vVal in vWarnings ])
        for i in range(3): self.assertIn('Error Message Test {}'.format(i), [ vVal['message'] for vVal in vErrors ])


    def test_ToCsv(self):
        # 设置
        vData = []
        vData.append(['编号', '姓名', '性别', '年龄', ])
        vData.append(['0001', '张三', '男', 22, ])
        vData.append(['0002', '李四', '女', 21, ])
        vData.append(['0003', '小明', '女', 24, ])
        
        # 使用
        vCsvFN = 'TestToCsvFunc.dat'
        vSep = ' '
        toCsv(vCsvFN, vData, vSep)
        
        # 断言
        vCsvFile = os.path.join(DIR_OUTPUT, vCsvFN)
        self.assertTrue(os.path.exists(vCsvFile))
        
        vText = '\n'.join([ vSep.join([ str(vItem) for vItem in vRecord ]) for vRecord in vData ]) + '\n'
        with open(vCsvFile) as f:
            self.assertEqual(vText, f.read())


    def test_TimeUsed(self):
        # 设置
        vWait = 2
        vStartTime = datetime.now()

        time.sleep(vWait)
        vUsed = timeUsed(vStartTime)

        self.assertEqual(vUsed, vWait)


    def test_SystemError(self):
        clearLogContent()
        try:
            [][1]
        except IndexError as e:
            msgExp(e)
            vText = getLogContent()
            self.assertIn(str(e), vText)
            self.assertNotIn('Traceback (most recent call last):', vText)

        clearLogContent()
        try:
            '' + 1
        except TypeError as e:
            msgExp(e, vTraceback=True)
            vText = getLogContent()
            self.assertIn(str(e), vText)
            self.assertIn('Traceback (most recent call last):', vText)


# 执行
if (__name__ == '__main__'):
    unittest.main()
