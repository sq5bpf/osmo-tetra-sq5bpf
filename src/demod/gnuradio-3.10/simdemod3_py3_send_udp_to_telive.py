"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import socket

class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block - periodically send UDP packet to telive"""

    def __init__(self, ntimes=10, rxid=0, port=7379, ip="127.0.0.1",scaling=10):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Send UDP messages to telive',   # will show up in GRC
            in_sig=[np.float32],
            out_sig=None
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.counter=0
        self.ntimes=ntimes
        self.tetra_hack_rxid=int(rxid)
        self.tetra_hack_ip=str(ip)
        self.tetra_hack_port=int(port)
        self.tetra_hack_scaling=scaling
        
        

    def work(self, input_items, output_items):
        """example: multiply with constant"""
        self.counter=(self.counter+1)%self.ntimes
        if self.counter==0:
            mmm="TETMON_begin FUNC:AFCVAL AFC:%i RX:%i TETMON_end" % ( int (input_items[0][0] * self.tetra_hack_scaling * - 1.0), self.tetra_hack_rxid)
            message=bytes(mmm, "utf-8")
            self.sock.sendto(message, (self.tetra_hack_ip, self.tetra_hack_port))
        return len(input_items [0])
