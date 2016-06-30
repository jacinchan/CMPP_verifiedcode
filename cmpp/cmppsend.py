#!/usr/bin/env python
# -*- coding: utf-8 -*-


import struct
import hashlib
import time

__all__ = ['messageheader', 'cmppconnect', 'cmppsubmit',
           'cmppdeliverresp', 'cmppactiveresp']


class messageheader:
    """
    the common message header
    """

    def __init__(self, messagebodylength=0, command_id=b'', seq=0):
        self.__total_length = struct.pack('!I', 12 + messagebodylength)
        self.__command_id = struct.pack('!I', command_id)
        self.__sequence_id = struct.pack('!I', seq)
        self.__sid = seq

    def header(self):
        return self.__total_length + self.__command_id + self.__sequence_id

    def total_length(self):
        return self.__total_length

    def command_id(self):
        return self.__command_id

    def sequence_id(self):
        return self.__sid


def get_strtime():
    """
    get the currenttime with a string style
    """
    return time.strftime('%m%d%H%M%S', time.localtime(time.time()))


def get_strdate():
    return time.strftime('%Y%m%d', time.localtime(time.time()))


class cmppconnect:
    """
    create a connection to ISMG on application layer
    """

    def __init__(self, sp_id='000000', sp_passwd='000000'):
        # if len(sp_id) != 6 or len(sp_passwd) != 6:
        #     raise ValueError("sp_id and sp_passwd are both 6 bits")
        self.__sourceaddr = sp_id.encode('utf-8').ljust(6, b'\x00')
        self.__password = sp_passwd.encode('utf-8')
        self.__version = struct.pack('!B', 0x30)
        self.__timestamp = get_strtime()
        authenticatorsource = self.__sourceaddr + 9 * b'\x00' + \
            self.__password + self.__timestamp.encode('utf-8')
        self.__md5 = hashlib.md5(authenticatorsource).digest()
        self.__length = 27
        self.__body = self.__sourceaddr + \
            self.__md5 + \
            self.__version + \
            int(self.__timestamp).to_bytes(4, 'big')

    def body(self):
        return self.__body

    def length(self):
        return self.__length


class cmppsubmit:
    """
    submit short message to ISMG
    """

    def __init__(self,
                 Pk_total=1,
                 Pk_number=1,
                 Registered_Delivery=0,
                 Msg_level=9,
                 Service_Id='0000000000',
                 Fee_UserType=0,
                 Fee_terminal_Id='',
                 Fee_terminal_type=0,
                 TP_pId=0,
                 TP_udhi=0,
                 Msg_Fmt=8,
                 Msg_src='000000',
                 FeeType='',
                 FeeCode='0',
                 ValId_Time='',
                 At_Time='',
                 Src_Id='000000000000',
                 DestUsr_tl=1,
                 Dest_terminal_Id=['8613900000000', ],
                 Dest_terminal_type=0,
                 Msg_Header='',
                 Msg_Content='test'):
        if len(Msg_Content) >= 70:
            raise ValueError("msg_content more than 70 words")
        if len(Dest_terminal_Id) > 100:
            raise ValueError("single submit more than 100 phone numbers")
        self.__Msg_Id = 8 * b'\x00'
        self.__Pk_total = struct.pack('!B', Pk_total)
        self.__Pk_number = struct.pack('!B', Pk_number)
        self.__Registered_Delivery = struct.pack('!B', Registered_Delivery)
        self.__Msg_level = struct.pack('!B', Msg_level)
        self.__Service_Id = Service_Id.encode('utf-8').ljust(10, b'\x00')
        self.__Fee_UserType = struct.pack('!B', Fee_UserType)
        self.__Fee_terminal_Id = Fee_terminal_Id.encode().ljust(32, b'\x00')
        self.__Fee_terminal_type = struct.pack('!B', Fee_terminal_type)
        self.__TP_pId = struct.pack('!B', TP_pId)
        self.__TP_udhi = struct.pack('!B', TP_udhi)
        self.__Msg_Fmt = struct.pack('!B', Msg_Fmt)
        self.__Msg_src = Msg_src.encode('utf-8').ljust(6, b'\x00')
        self.__FeeType = FeeType.encode('utf-8').ljust(2, b'\x00')
        self.__FeeCode = FeeCode.encode('utf-8').ljust(6, b'\x00')
        self.__ValId_Time = ValId_Time.encode('utf-8').ljust(17, b'\x00')
        self.__At_Time = At_Time.encode('utf-8').ljust(17, b'\x00')
        self.__Src_Id = Src_Id.encode('utf-8').ljust(21, b'\x00')
        self.__DestUsr_tl = struct.pack('!B', DestUsr_tl)
        self.__Dest_terminal_Id = b""
        for msisdn in Dest_terminal_Id:
            self.__Dest_terminal_Id += msisdn.encode().ljust(32, b'\x00')
        self.__Dest_terminal_type = struct.pack('!B', Dest_terminal_type)
        self.__Msg_Content = Msg_Content.encode('utf-16-BE')
        Msg_Length = len(self.__Msg_Content)
        self.__Msg_Length = struct.pack('!B', Msg_Length)
        self.__Msg_Header = Msg_Header.encode('utf-8')
        self.__LinkID = 20 * b'\x00'
        self.__length = 151 + 32 * DestUsr_tl + Msg_Length
        self.__body = self.__Msg_Id + \
            self.__Pk_total + self.__Pk_number + \
            self.__Registered_Delivery + \
            self.__Msg_level + \
            self.__Service_Id + \
            self.__Fee_UserType + self.__Fee_terminal_Id + \
            self.__Fee_terminal_type + \
            self.__TP_pId + self.__TP_udhi + \
            self.__Msg_Fmt + self.__Msg_src + \
            self.__FeeType + self.__FeeCode + \
            self.__ValId_Time + self.__At_Time + \
            self.__Src_Id + self.__DestUsr_tl + \
            self.__Dest_terminal_Id + self.__Dest_terminal_type + \
            self.__Msg_Length + \
            self.__Msg_Header + \
            self.__Msg_Content + \
            self.__LinkID

    def body(self):
        return self.__body

    def length(self):
        return self.__length


class cmppdeliverresp:

    def __init__(self, Msg_Id, Result=0):
        self.__Msg_Id = struct.pack('!Q', Msg_Id)
        self.__Result = struct.pack('!I', Result)
        self.__length = 12
        self.__body = self.__Msg_Id + self.__Result

    def body(self):
        return self.__body

    def length(self):
        return self.__length


class cmppactiveresp:

    def __init__(self):
        self.__Reserved = b'\x00'
        self.__length = 1
        self.__body = self.__Reserved

    def body(self):
        return self.__body

    def length(self):
        return self.__length
