#!python
# coding: gbk
#----------------------------------------
# Log.py
#----------------------------------------
import re, time
import logging
from logging.handlers import RotatingFileHandler


class Log:     
    def __init__(self, vLogFile, vLogLevel):
        self.vLogFile = vLogFile
        self.vActionID = '{:.3f}'.format(time.time()).replace('.', '@')
        self.vActionInfo = '<{}>'.format(self.vActionID)
        
        self.vLogger = logging.getLogger(self.vActionID)
        self.vLogger.setLevel(vLogLevel)
        
        vLog1 = RotatingFileHandler(self.vLogFile, maxBytes=512*1024, backupCount=3)
        vLog1.setFormatter(logging.Formatter('<%(asctime)s><%(levelname)s>%(message)s'))
        vLog1.setLevel(logging.DEBUG)
        
        self.vLogger.addHandler(vLog1)


    def debug(self, vMsg=''):
        self.vLogger.debug(self.vActionInfo + vMsg)

    def info(self, vMsg=''):
        self.vLogger.info(self.vActionInfo + vMsg)

    def warning(self, vMsg=''):
        self.vLogger.warning(self.vActionInfo + vMsg)

    def error(self, vMsg=''):
        self.vLogger.error(self.vActionInfo + vMsg)

    def exception(self, e):
        self.vLogger.exception(e)


    def getLogs(self):
        ''' ȡ�õ�ǰActionID����־����
            ���ֵ����ʽ���أ����£�
            {'action_id': ��ǰ��־��ActionID,
             'debugs': [
                {'timestamp': ��־ʱ��, 'message': ��־����},
                {'timestamp': ��־ʱ��, 'message': ��־����},
                ...(�����Ƕ�������)
                ],
             'infos': [...(ͬdebugs)...]
             'warnings': [...(ͬdebugs)...]
             'errors: [...(ͬdebugs)...]
            }
        '''
        # ȡ�õ�ǰActionID����־����
        with open(self.vLogFile) as f:
            vLogLines = re.findall('.+<{}>.+'.format(self.vActionID), f.read())
        
        vDebugs   = []
        vInfos    = []
        vWarnings = []
        vErrors   = []
        for vLine in vLogLines:
            vItems = vLine.split('>')
            vLevel = vItems[1].strip('<')
            vValue = { \
                'timestamp': vItems[0].strip('<'), \
                'message': vItems[3], \
            }
            if (vLevel == 'DEBUG'): vDebugs.append(vValue)
            elif (vLevel == 'INFO'): vInfos.append(vValue)
            elif (vLevel == 'WARNING'): vWarnings.append(vValue)
            elif (vLevel == 'ERROR'): vErrors.append(vValue)
        
        return { \
            'action_id': self.vActionID, \
            'debugs': vDebugs, \
            'infos': vInfos, \
            'warnings': vWarnings, \
            'errors': vErrors, \
        }

