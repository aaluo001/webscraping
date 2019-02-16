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


# 日志
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
    ''' 取得当前Action的日志内容
    '''
    global __vLog
    return __vLog.getLogs()

def getLogContent():
    ''' 取得日志全部内容(测试用)
    '''
    with open(LOG_FILE) as f: return f.read()

def clearLogContent():
    ''' 清空日志全部内容(测试用)
    '''
    with open(LOG_FILE, 'w') as f: f.write('')


def toCsv(vFileName, vData, vSep=','):
    ''' 将数据以CSV的形式输出到文件中
        vFileName: 只需指定文件名，文件会保存到output目录下
        vData: 二维数组
        vSep: 分隔符，默认是逗号(',')
    '''
    # 将vData中的项目转换成字符串型
    # 用vSep将各个项目链接起来
    # 用'\n'将每行数据链接起来
    vText = '\n'.join([ vSep.join([ str(vItem) for vItem in vRecord ]) for vRecord in vData ]) + '\n'
    vCsvFile = os.path.join(DIR_OUTPUT, vFileName)
    with open(vCsvFile, 'w') as f:
        f.write(vText)


def timeUsed(vStartTime):
    return (datetime.now() - vStartTime).seconds

