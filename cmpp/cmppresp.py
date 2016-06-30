#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
from cmppdefines import *


class response:

    def __init__(self):
        self.__header = b''
        self.__body = b''
        self.__length = 12
        self.__bodylen = 0
        self.__command_id = 0
        self.__sequence_id = 0
        self.__resp_obj = {
            CMPP_CONNECT_RESP: connectresp,
            CMPP_SUBMIT_RESP: submitresp,
            CMPP_DELIVER: deliver,
            CMPP_ACTIVE_TEST: activetest,
            CMPP_ACTIVE_TEST_RESP: nothingresp,
            CMPP_TERMINATE_RESP: nothingresp
        }

    def parse(self, info):
        self.__length, = struct.unpack('!L', info[0:4])
        self.__header = info[0:12]
        self.__body = info[12:self.__length]
        self.__command_id, = struct.unpack('!L', info[4:8])
        self.__sequence_id, = struct.unpack('!L', info[8:12])

    def parseheader(self):
        return {'length': self.__length,
                'command_id': self.__command_id,
                'sequence_id': self.__sequence_id}

    def parsebody(self):
        resp = self.__resp_obj[self.__command_id]()
        return resp.parse(self.__body)


class connectresp:

    def __init__(self):
        self.__Status = 5
        self.__AuthenticatorISMG = b''
        self.__Version = 0

    def parse(self, body):
        self.__Status, = struct.unpack('!I', body[0:4])
        self.__AuthenticatorISMG = body[4:20]
        self.__Version, = struct.unpack('!B', body[20:21])
        return {'Status': self.__Status,
                'AuthenticatorISMG': self.__AuthenticatorISMG,
                'Version': self.__Version
                }


class submitresp:

    def __init__(self):
        self.__Msg_Id = b''
        self.__Result = 0

    def parse(self, body):
        self.__Msg_Id = struct.unpack('!Q', body[0:8])
        self.__Result, = struct.unpack('!I', body[8:12])
        return {'Msg_Id': self.__Msg_Id,
                'Result': self.__Result
                }


class msgcontent:

    def __init__(self):
        self.__Msg_Id = 0
        self.__Stat = ''
        self.__Submit_time = ''
        self.__Done_time = ''
        self.__Dest_terminal_Id = ''
        self.__SMSC_sequence = 0
        self.__myself = {}

    def parse(self, body):
        # self.__Msg_Id = struct.unpack('!Q',body[0:8])
        self.__Msg_Id = body[0:8]
        self.__Stat = body[8:15]
        self.__Submit_time = body[15:25]
        self.__Done_time = body[25:35]
        self.__Dest_terminal_Id = body[35:67]
        self.__SMSC_sequence = struct.unpack('!L', body[67:71])
        self.__myself = {'Msg_Id': self.__Msg_Id,
                         'Stat': self.__Stat,
                         'Submit_time': self.__Submit_time,
                         'Done_time': self.__Done_time,
                         'Dest_terminal_Id': self.__Dest_terminal_Id,
                         'SMSC_sequence': self.__SMSC_sequence
                         }

    def value(self):
        return self.__myself


class deliver:

    def __init__(self):
        self.__Msg_Id = 0
        self.__Dest_Id = b''
        self.__Service_Id = b''
        self.__TP_pid = 0
        self.__TP_udhi = 0
        self.__Msg_Fmt = 0
        self.__Src_terminal_Id = b''
        self.__Src_terminal_type = b''
        self.__Registered_Delivery = 0
        self.__Msg_Length = 0
        self.__Msg_Content = ''
        self.__LinkID = ''

    def parse(self, body):
        self.__Msg_Id, = struct.unpack('!I', body[0:8])
        self.__Dest_Id = body[8:29]
        self.__Service_Id = body[29:39]
        self.__TP_pid, = struct.unpack('!B', body[39:40])
        self.__TP_udhi, = struct.unpack('!B', body[40:41])
        self.__Msg_Fmt, = struct.unpack('!B', body[41:42])
        self.__Src_terminal_Id = body[42:74]
        self.__Src_terminal_type = body[74:75]
        self.__Registered_Delivery = struct.unpack('!B', body[75:76])
        self.__Msg_Length, = struct.unpack('!B', body[76:77])
        if self.__Registered_Delivery == 1:
            submitstate = msgcontent()
            submitstate.parse(body[77:self.__Msg_Length + 77])
            self.__Msg_Content = submitstate.value()
        else:
            self.__Msg_Content = body[77:self.__Msg_Length + 77]
            #msg_fmt = {0:'utf-8', 8:'utf-16-be', 15:'gbk'}
            #self.__Msg_Content = body[65:self.__Msg_Length+65].decode(msg_fmt[self.__Msg_Fmt])
        self.__LinkID = body[self.__Msg_Length + 77:]
        return {'Msg_Id': self.__Msg_Id,
                'Dest_Id': self.__Dest_Id,
                'Service_Id': self.__Service_Id,
                'TP_pid': self.__TP_pid,
                'TP_udhi': self.__TP_udhi,
                'Msg_Fmt': self.__Msg_Fmt,
                'Src_terminal_Id': self.__Src_terminal_Id,
                'Src_terminal_type': self.__Src_terminal_type,
                'Registered_Delivery': self.__Registered_Delivery,
                'Msg_Length': self.__Msg_Length,
                'Msg_Content': self.__Msg_Content,
                'LinkID': self.__LinkID
                }


class activetest:

    def __init__(self):
        self.__Reserved = 0

    def parse(self, body):
        return {}


class nothingresp:

    def parse(self, body):
        return {}
