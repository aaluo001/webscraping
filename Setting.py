#!python
# coding: gbk
#----------------------------------------
# Setting.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import os
import logging


VERSION     = '0.1.01'
PROJECT     = 'webscraping'

DIR_BASE    = os.path.dirname(os.path.abspath(__file__))
DIR_OUTPUT  = os.path.join(DIR_BASE, 'output')

LOG_FILE    = os.path.join(DIR_OUTPUT, '{}.log'.format(PROJECT))
LOG_LEVEL   = logging.INFO


MYSQL_CONF = {
    'host':    'localhost',
    'port':    3306,
    'user':    'Pywork',
    'passwd':  'Pywork2019+',
    'db':      PROJECT,
    'charset': 'UTF8',
}

MONGO_CONF = {
    'host': 'localhost',
    'port': 27017,
    'db':   PROJECT,
}
