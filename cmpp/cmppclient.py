#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import struct
import logging
from cmppresp import response as cmppresp
from cmppthread import sendthread, recvthread
from cmppdefines import *
from cmppsend import messageheader
from cmppsend import cmppconnect
from cmppsend import cmppsubmit
from cmppsend import cmppdeliverresp
from cmppsend import cmppactiveresp
# from binascii import hexlify


class cmppclient:

    def __init__(self, send_queue, recv_queue,
                 gateway='0.0.0.0', port=0,
                 sp_id='000000', sp_passwd='000000',
                 src_id='0000000000', com_id='000000',
                 service_id='0000000000', max_window=30):
        self.__gateway = gateway
        self.__service_id = service_id
        self.__port = port
        self.__sp_id = sp_id
        self.__src_id = src_id
        self.__com_id = com_id
        self.__sp_passwd = sp_passwd
        self.__src_id = src_id
        self.__sequence_id = 2001
        self.__active_sequence_id = 1
        self.__sp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__resp = cmppresp()
        self.__send_queue = send_queue
        self.__recv_queue = recv_queue
        self.__sendthread = sendthread(self.send, self.__send_queue,
                                       rate=max_window)
        self.__recvthread = recvthread(self.recv, self.deliverresp,
                                       self.activeresp, self.__recv_queue,
                                       self.timeout)
        self.logger = logging.getLogger('cmppclient')

    def __del__(self):
        if self.__recvthread.is_alive():
            self.__recvthread.stop()
        if self.__sendthread.is_alive():
            self.__sendthread.stop()
        self.disconnectgateway()

    def is_alive(self):
        return self.__recvthread.is_alive() and self.__sendthread.is_alive()

    def __internal_id(self, seq_type=1):
        if seq_type == 0:
            if self.__active_sequence_id >= 100:
                self.__avtive_sequence_id = 1
            s = self.__active_sequence_id
            self.__active_sequence_id += 1
        elif seq_type == 1:
            s = self.__sequence_id
            self.__sequence_id += 1
        else:
            s = 0
        return s

    def start(self):
        if self.connect():
            self.__sendthread.start()
            self.__recvthread.start()
        return self

    def stop(self):
        self.terminate()
        self.__sendthread.stop()
        self.__recvthread.stop()
        self.disconnectgateway()

    def connectgateway(self):
        try:
            cmppaddr = (self.__gateway, self.__port)
            self.__sp.settimeout(15)
            self.__sp.connect(cmppaddr)
        except socket.error as arg:
            self.logger.error(arg)
            # sys.exit(100)

    def disconnectgateway(self):
        try:
            self.__sp.close()
        except socket.error as arg:
            self.logger.error(arg)

    def send(self, message):
        # print('sending: ')
        # print(hexlify(message))
        self.__sp.send(message)

    def connect(self):
        mb = cmppconnect(self.__sp_id, self.__sp_passwd)
        mh = messageheader(mb.length(), CMPP_CONNECT,
                           self.__internal_id(seq_type=0))
        msg = mh.header() + mb.body()
        try:
            self.connectgateway()
            # print(msg, len(msg))
            self.send(msg)
            h, b = self.recv()
            # print(h, b)
            status = b.get('Status', -1)
            if status != 0:
                self.logger.error(
                    'connect failed, status: %d.' % status)
                # self.__sp.close()
                # sys.exit(201)
            else:
                self.logger.info('connect successfully')
                return True
            # self.__send_queue.put(msg_seq)
        except socket.error as arg:
            self.logger.error(arg)
            # self.disconnectgateway()
            # return False
            # sys.exit(100)
        # self.logger.error('connect failed')
        return False

    def normalmessage(self, dest, content, isdelivery=0):
        mb = cmppsubmit(Src_Id=self.__src_id,
                        Service_Id=self.__service_id,
                        Msg_src=self.__com_id,
                        Registered_Delivery=isdelivery,
                        Msg_Content=content,
                        DestUsr_tl=len(dest),
                        Dest_terminal_Id=dest)
        seq = self.__internal_id()
        mh = messageheader(mb.length(), CMPP_SUBMIT, seq)
        msg = mh.header() + mb.body()
        # self.__sp.send(msg)
        # self.__sp.send(msg)
        self.__send_queue.put((msg, seq))

    def longmessage(self, dest, content, isdelivery=0):
        tp_udhi = '\x05\x00\x03\x37'
        remain_len = len(content) * 2
        times = remain_len // 134
        if remain_len % 134 > 0:
            times += 1
        msg = []
        seq = self.__internal_id()
        for count in range(0, times):

            if remain_len >= 134:
                current_len = 134
            else:
                current_len = remain_len
            remain_len -= 134

            content_header = tp_udhi
            content_header += struct.pack('B', times).decode('utf-8')
            content_header += struct.pack('B', count + 1).decode('utf-8')
            content_slice = content[(0 + count * 67):
                                    (current_len // 2 + count * 67)]

            mb = cmppsubmit(Src_Id=self.__src_id,
                            Registered_Delivery=isdelivery,
                            Msg_Header=content_header,
                            Service_Id=self.__service_id,
                            Msg_Content=content_slice,
                            Msg_src=self.__com_id,
                            Msg_Length=current_len + 6,
                            DestUsr_tl=len(dest),
                            Dest_terminal_Id=dest,
                            TP_pId=1, TP_udhi=1)
            mh = messageheader(mb.length(), CMPP_SUBMIT, seq)
            msg.append(mh.header() + mb.body())

        self.__sp.send(msg[count])
        self.__send_queue.put((msg, seq))

    def sendmessage(self, dest, content, isdelivery=0):
        if len(content) <= 70:
            self.normalmessage(dest, content, isdelivery)
        else:
            self.longmessage(dest, content, isdelivery)

    def terminate(self):
        seq = self.__internal_id(seq_type=0)
        mh = messageheader(0, CMPP_TERMINATE, seq)
        msg = mh.header()
        try:
            self.__sp.send(msg)
        except Exception:
            pass
        # self.__send_queue.put((msg, seq))

    def active(self):
        seq = self.__internal_id(seq_type=0)
        mh = messageheader(0, CMPP_ACTIVE_TEST, seq)
        msg = mh.header()
        # self.__sp.send(msg)
        self.__send_queue.put((msg, seq))

    def activeresp(self, sequence_id):
        mb = cmppactiveresp()
        mh = messageheader(mb.length(), CMPP_ACTIVE_TEST_RESP, sequence_id)
        msg = mh.header() + mb.body()

        # self.__sp.send(msg)
        self.__send_queue.put((msg, sequence_id))
        # self.active()

    def deliverresp(self, Msg_Id, Result, sequence_id):
        mb = cmppdeliverresp(Msg_Id, Result)
        mh = messageheader(mb.length(), CMPP_DELIVER_RESP, sequence_id)
        msg = mh.header() + mb.body()

        # self.__sp.send(msg)
        self.__send_queue.put((msg, sequence_id))

    def recv(self):
        try:
            length = self.__sp.recv(4)
            maxlen, = struct.unpack('!I', length)
            rec = length + self.__sp.recv(maxlen - 4)
            # print('receive:')
            # print(hexlify(rec))
            self.__resp.parse(rec)
            mh = self.__resp.parseheader()
            mb = self.__resp.parsebody()
        except struct.error:
            mh = {}
            mb = {}
        return mh, mb

    def timeout(self, doubletimeout=False):
        if not doubletimeout:
            self.logger.info('long connection timeout, send active test')
            self.active()
        else:
            self.logger.info('socket timeout, disconnecting...')
            self.stop()

