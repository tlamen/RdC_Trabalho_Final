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
from base.whiteboard import Whiteboard

class R2ANew(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = []
        self.parsed_mpd = ''
        self.qi = []
        self.qualities_responses = []
        self.qualities_used = []
        self.last_move = ""
        self.index = 10
        self.whiteboard = Whiteboard.get_instance()
        self.last_buffer_use = 0

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        self.send_up(msg)

    def getQuality(self, msg):
        # getting qi list
        QLi = msg.get_quality_id()
        N = len(self.qi)
        QLi = self.qi.index(QLi)

        return (QLi - 1) / (N - 1) * 2 - 1

    def getOscilation(self):
        oscilation_length_max = 30
        oscilation_length = -1
        if len(self.qualities_used) > 1:
            if self.last_move == "up" and self.qualities_used[-1] < self.qualities_used[-2]:
                for i in range(len(self.qualities_used)-1, -1, -1):
                    oscilation_length += 1
                    if oscilation_length > oscilation_length_max:
                        return 0
                    if i != len(self.qualities_used)-1:
                        if self.qualities_used[i] < self.qualities_used[i-1]:
                            print("entrou 2")
                            oscilation_depth = self.qualities_used[i-1] - self.qualities_used[i]
                            
                            return  (-1 / oscilation_length**(2/oscilation_depth)) + ((oscilation_length - 1) / (oscilation_length_max - 1) * oscilation_length_max**(2/oscilation_depth))
                        elif i == 0:
                            oscilation_depth = max(self.qualities_used) - self.qualities_used[i]

                            return  (-1 / oscilation_length**(2/oscilation_depth)) + ((oscilation_length - 1) / (oscilation_length_max - 1) * oscilation_length_max**(2/oscilation_depth))
                self.last_move = "down"
            else:
                if self.qualities_used[-1] < self.qualities_used[-2]:
                    self.last_move = "down"
                else:
                    self.last_move = "up"
                return 0
        else:
            return 0

    def getBuffering(self, msg):
        actual = self.whiteboard.get_amount_video_to_play()
        Bmax = self.whiteboard.get_max_buffer_size()
        Bi = actual / Bmax
        if Bi <= 0.1:
            return -1
        else:
            return ((2*Bi) / (0.9 * Bmax)) - (1.1 / 0.9)
 
    def getBufferChange(self, msg):
        actual = self.whiteboard.get_amount_video_to_play()
        Bmax = self.whiteboard.get_max_buffer_size()
        Bi = actual / Bmax
        if self.last_buffer_use > 0:
            if Bi > self.last_buffer_use:
                response = (Bi - self.last_buffer_use) / (Bi - (self.last_buffer_use / 2 ))
            else:
                response = ((Bi - self.last_buffer_use) / self.last_buffer_use)
        else:
            self.last_buffer_use = Bi
            return 0
        
        self.last_buffer_use = Bi
        return response

    def handle_segment_size_request(self, msg):
        # Constants for reward function
        C1 = 2
        C2 = 1 
        C3 = 4  
        C4 = 3

        # Getting reward components
        if self.qualities_responses:
            R_quality = self.qualities_responses[-1]
        else:
            R_quality = 1
        R_oscilation  = self.getOscilation()
        R_bufferChange = self.getBufferChange(msg)
        R_buffering = self.getBuffering(msg)

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

        # qi_id = random.randint(0, len(self.qi)-1)
        if self.index > 19:
            self.index = 10
        
        qi_id = self.index

        msg.add_quality_id(self.qi[qi_id])
        

        self.index += 1

        info = {
            "R_quality": R_quality,
            "R_oscilation": R_oscilation,
            "R_buffering": R_buffering,
            "R_bufferChange": R_bufferChange,
            "actualBufferSize": self.whiteboard.get_amount_video_to_play(),
            "lastMove": self.last_move,
            "Quality": qi_id
        }

        print(info)

        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.qualities_responses.append(self.getQuality(msg))
        self.qualities_used.append(self.qi.index(msg.get_quality_id()))
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
