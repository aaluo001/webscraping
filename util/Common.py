#!python
# coding: gbk
#----------------------------------------
# Common.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import os, re
from datetime import datetime

from Setting import LOG_FILE, LOG_LEVEL, DIR_OUTPUT
from util.Log import Log


# ��־
__vLog = Log(LOG_FILE, LOG_LEVEL)

def msgDeg(vMsg):
    global __vLog
    __vLog.debug(vMsg)

def msgInf(vMsg):
    global __vLog
    print(vMsg)
    __vLog.info(vMsg)

def msgWrn(vMsg):
    global __vLog
    print(vMsg)
    __vLog.warning(vMsg)

def msgErr(vMsg):
    global __vLog
    print(vMsg)
    __vLog.error(vMsg)

def msgExp(e, vTraceback=False):
    msgErr(str(e))
    if (vTraceback): __vLog.exception(e)


def getLogs():
    ''' ȡ�õ�ǰAction����־����
    '''
    global __vLog
    return __vLog.getLogs()

def getLogContent():
    ''' ȡ����־ȫ������(������)
    '''
    with open(LOG_FILE) as f: return f.read()

def clearLogContent():
    ''' �����־ȫ������(������)
    '''
    with open(LOG_FILE, 'w') as f: f.write('')


def toCsv(vFileName, vData, vSep=','):
    ''' ��������CSV����ʽ������ļ���
        vFileName: ֻ��ָ���ļ������ļ��ᱣ�浽outputĿ¼��
        vData: ��ά����
        vSep: �ָ�����Ĭ���Ƕ���(',')
    '''
    # ��vData�е���Ŀת�����ַ�����
    # ��vSep��������Ŀ��������
    # ��'\n'��ÿ��������������
    vText = '\n'.join([ vSep.join([ str(vItem) for vItem in vRecord ]) for vRecord in vData ]) + '\n'
    vCsvFile = os.path.join(DIR_OUTPUT, vFileName)
    with open(vCsvFile, 'w') as f:
        f.write(vText)


def timeUsed(vStartTime):
    return (datetime.now() - vStartTime).seconds

