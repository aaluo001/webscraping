#!python
# coding: gbk
#----------------------------------------
# BaseProject.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import sys, os
from datetime import datetime

from Setting import DIR_OUTPUT
from util.Common import timeUsed
from util.Common import msgInf, msgExp


class BaseProject:
    def __init__(self):
        self.vStartTime = datetime.now()
        self.vTSDate  = self.vStartTime.strftime('%Y%m%d')
        self.vTSTime  = self.vStartTime.strftime('%H%M%S')
        
        self.vSysArgv = sys.argv
        self.vAppName = os.path.basename(self.vSysArgv[0])[:-3]
        self.vAppDir  = os.path.dirname(self.vSysArgv[0])


    def __procStart(self):
        msgInf('<START - {}>'.format(self.vAppName))
        msgInf(self.vStartTime.strftime('%Y-%m-%d %H:%M:%S'))

    def __procEnd(self, vCode):
        vStatus = 'Successed'
        if (vCode != 0): vStatus = 'Failed'
        msgInf('TimeUsed: {:.3f}s'.format(timeUsed(self.vStartTime)))
        msgInf('<END - {}>'.format(vStatus))
        sys.exit(vCode)


    # ��������
    def procArgv(self): return True
    # �������ô���
    def setUp(self): pass
    # �����������
    def tearDown(self): pass
    # ������
    def main(self): pass
    # ����������
    def report(self): pass    


    # ִ��
    def run(self):
        if (not self.procArgv()): sys.exit(1)
        vCode = 0
        self.__procStart()
        
        try:
            self.setUp()
            self.main()
            self.report()
        except Exception as e:
            msgExp(e, vTraceback=True)
            vCode = 1
        finally:
            self.tearDown()

        self.__procEnd(vCode)
