# -*- coding: utf-8 -*-
"""
@authors: Bernardo M. Lobo, Luiz Henrique

@description: PyDash Project

An implementation example of a Random R2A Algorithm.

The quality list is obtained with the parameter of handle_xml_response()
method and the choice is made inside of handle_segment_size_request(),
before sending the message down.

In this algorithm the quality choice is made randomly.
"""

from player.parser import *
from r2a.ir2a import IR2A
import time

class R2ANew(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = []
        self.parsed_mpd = ''
        self.qi = []
        self.qualities_used = []

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        t = time.perf_counter() - self.request_time
        self.throughputs.append(msg.get_bit_length() / t)

        self.send_up(msg)

    def getQuality(self, msg):
        # getting qi list
        QLi = msg.get_bit_length()
        N = len(self.qi)
        # print(QLi)
        # print(N)
        # print((QLi - 1) / (N - 1) * 2 - 1)
        return (QLi - 1) / (N - 1) * 2 - 1

    def getOscilation(self, msg):
        return 1

    def getBuffering(self, msg):
        return 1

    def getBufferChange(self, msg):
        return 1

    def handle_segment_size_request(self, msg):
        # Constants for reward function
        C1 = 2
        C2 = 1 
        C3 = 4  
        C4 = 3

        # Getting reward components
        if self.qualities_used:
            R_quality = self.qualities_used[-1]
        else:
            R_quality = 1
        R_oscilation  = self.getOscilation(msg)
        R_bufferChange = self.getBufferChange(msg)
        R_buffering = self.getBuffering(msg)

        print(R_quality)
        # Reward Function
        R = C1 * 1 + C2 * R_oscilation + C3 * R_buffering + C4 * R_bufferChange      

        # Constants for Q function
        alpha = 0.3 # learning rate
        gama = 0.5 # discount factor
        max_Qi_id = max(self.qi)
        
        # Q function
        qi_id = msg.get_bit_length()
        qi_id = int(qi_id + alpha + (R + gama * max_Qi_id - qi_id))

        if qi_id > max_Qi_id:
            qi_id = max_Qi_id - 1
        
        msg.add_quality_id(self.qi[1])

        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.qualities_used.append(self.getQuality(msg))
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
