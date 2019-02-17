#!python
# coding: gbk
#----------------------------------------
# Throttle.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import random, time
from datetime import datetime
from urllib.parse import urlparse


class Element:
    def __init__(self):
        # Timestamp of last access
        self.vLastAccess = datetime.now()
        self.vLocked = False


class Throttle:
    ''' 对同一域名而言，在两次下载之间进行延迟处理。
      支持多线程延迟处理，当元素被锁时，将触发线程等待。
    '''
    def __init__(self, vDelay):
        self.vDelay = vDelay
        self.vElementList = {}

    def wait(self, vUrl):
        k = urlparse(vUrl).netloc
        e = self.vElementList.get(k)

        if (e):
            # 等待元素解锁，让出CPU
            while(e.vLocked): time.sleep(1)
            # 元素加锁
            e.vLocked = True
            # 延迟处理
            if (e.vLastAccess and self.vDelay > 0):
                vWaitSeconds = self.vDelay - (datetime.now() - e.vLastAccess).seconds
                vWaitSeconds += round(random.random() * 2, 2)
                if (vWaitSeconds > 0): time.sleep(vWaitSeconds)

            # Set last access timestamp
            e.vLastAccess = datetime.now()
            # 元素解锁
            e.vLocked = False

        else:
            # Add new element
            self.vElementList[k] = Element()

