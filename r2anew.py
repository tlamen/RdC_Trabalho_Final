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


class R2ANew(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        self.send_up(msg)

    def getQuality():
        return 0

    def getOscilation():
        return 0

    def getBuffering():
        return 0

    def getBufferChange():
        return 0

    def handle_segment_size_request(self, msg):
        # Constants for reward function
        C1 = 2
        C2 = 1 
        C3 = 4  
        C4 = 3

        # Getting reward components
        R_quality = self.getQuality()
        R_oscilation  = self.getOscilation()
        R_bufferChange = self.getBufferChange()
        R_buffering = self.getBuffering()

        # Reward Function
        R = C1 * R_quality + C2 * R_oscilation + C3 * R_buffering + C4 * R_bufferChange # reward function        

        # Constants for Q function
        alpha = 0.3 # learning rate
        gama = 0.5 # discount factor
        max_Qi_id = max(self.qi)
        
        # Q function
        qi_id = qi_id + alpha + [R + gama * max_Qi_id - qi_id]
        
        msg.add_quality_id(self.qi[qi_id])

        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
