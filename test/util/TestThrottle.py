#!python
# coding: gbk
#----------------------------------------
# TestThrottle.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import unittest
import time, threading
from util.Throttle import Throttle


URL = 'http://www.pytest.com/{}'
MAX_THREAD = 5


class TestThrottle(unittest.TestCase):

    def setUp(self):
        self.vDelay = 1
        self.vThrottle = Throttle(self.vDelay)
        self.vQueue = set()

    def tearDown(self):
        pass


    def initQueue(self, vSize):
        for i in range(vSize):
            self.vQueue.add(URL.format(i))

    def waitTime(self):
        vStartTime = time.time()
        self.vThrottle.wait(self.vQueue.pop())
        return time.time() - vStartTime


    def firstWait(self):
        vWaitTime = self.waitTime()
        self.assertTrue(vWaitTime < self.vDelay, 'WaitTime: {}'.format(vWaitTime))

    def process(self):
        while(self.vQueue):
            vWaitTime = self.waitTime()
            self.assertTrue(vWaitTime >= self.vDelay, 'WaitTime: {}'.format(vWaitTime))


    def test_ThrottleBySingleThread(self):
        self.initQueue(5)
        self.firstWait()
        self.process()


    def test_ThrottleByMultipleThreads(self):
        self.initQueue(20)
        self.firstWait()
        
        vThreadList = []
        while(self.vQueue or vThreadList):
            for vThread in vThreadList:
                if (not vThread.isAlive()): vThreadList.remove(vThread)
            
            while(self.vQueue and len(vThreadList) < MAX_THREAD):
                vThread = threading.Thread(target=self.process)
                vThread.setDaemon(True)
                vThread.start()
                vThreadList.append(vThread)
            
            time.sleep(1)


# 执行
if (__name__ == '__main__'):
    unittest.main()
