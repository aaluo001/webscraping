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
    ''' ��ͬһ�������ԣ�����������֮������ӳٴ���
      ֧�ֶ��߳��ӳٴ�����Ԫ�ر���ʱ���������̵߳ȴ���
    '''
    def __init__(self, vDelay):
        self.vDelay = vDelay
        self.vElementList = {}

    def wait(self, vUrl):
        k = urlparse(vUrl).netloc
        e = self.vElementList.get(k)

        if (e):
            # �ȴ�Ԫ�ؽ������ó�CPU
            while(e.vLocked): time.sleep(1)
            # Ԫ�ؼ���
            e.vLocked = True
            # �ӳٴ���
            if (e.vLastAccess and self.vDelay > 0):
                vWaitSeconds = self.vDelay - (datetime.now() - e.vLastAccess).seconds
                vWaitSeconds += round(random.random() * 2, 2)
                if (vWaitSeconds > 0): time.sleep(vWaitSeconds)

            # Set last access timestamp
            e.vLastAccess = datetime.now()
            # Ԫ�ؽ���
            e.vLocked = False

        else:
            # Add new element
            self.vElementList[k] = Element()

