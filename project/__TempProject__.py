#!python
# coding: gbk
#----------------------------------------
# TempProject.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
from Setting import *
from util.Common import *
from util.project.BaseProject import BaseProject


class TempProject(BaseProject):
    def __init__(self):
        super().__init__()

    # ��������
    def procArgv(self): return True
    # ������
    def main(self): pass


# ִ��
if (__name__ == '__main__'):
    TempProject().run()
