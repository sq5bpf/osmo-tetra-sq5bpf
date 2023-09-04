#!/usr/bin/env python

import sys
import math
from gnuradio import blocks, filter, gr
from gnuradio import usrp2
from gnuradio.eng_option import eng_option
from optparse import OptionParser

# Load it locally or from the module
try:
    import cqpsk
except:
    from tetra_demod import cqpsk

# accepts an input file in complex format 
# applies frequency translation, resampling (interpolation/decimation)

class my_top_block(gr.top_block):
    def __init__(self, options):
        gr.top_block.__init__(self)

        # Create a USRP2 source and set decimation rate
        self._u = usrp2.source_32fc(options.interface, options.mac_addr)
        self._u.set_decim(512)

        # Set receive daughterboard gain
        if options.gain is None:
            g = self._u.gain_range()
            options.gain = float(g[0]+g[1])/2
            print "Using mid-point gain of", options.gain, "(", g[0], "-", g[1], ")"
        self._u.set_gain(options.gain)
 
        # Set receive frequency
        if options.lo_offset is not None:
            self._u.set_lo_offset(options.lo_offset)

        tr = self._u.set_center_freq(options.freq)
        if tr == None:
            sys.stderr.write('Failed to set center frequency\n')
            raise SystemExit, 1

        sample_rate = 100e6/512
        symbol_rate = 18000
        sps = 2
        # output rate will be 36,000
        ntaps = 11 * sps
        new_sample_rate = symbol_rate * sps

        channel_taps = filter.firdes.low_pass(1.0, sample_rate, options.low_pass, options.low_pass * 0.1, filter.firdes.WIN_HANN)

        FILTER = filter.freq_xlating_fir_filter_ccf(1, channel_taps, options.calibration, sample_rate)

        sys.stderr.write("sample rate: %d\n" %(sample_rate))

        DEMOD = cqpsk.cqpsk_demod( samples_per_symbol = sps,
                                 excess_bw=0.35,
                                 costas_alpha=0.03,
                                 gain_mu=0.05,
                                 mu=0.05,
                                 omega_relative_limit=0.05,
                                 log=options.log,
                                 verbose=options.verbose)

        OUT = blocks.file_sink(gr.sizeof_float, options.output_file)

        r = float(sample_rate) / float(new_sample_rate)

        INTERPOLATOR = filter.fractional_resampler_cc(0, r)

        self.connect(self._u, FILTER, INTERPOLATOR, DEMOD, OUT)

def get_options():
    parser = OptionParser(option_class=eng_option)
    # usrp related settings
    parser.add_option("-e", "--interface", type="string", default="eth0",
                      help="use specified Ethernet interface [default=%default]")
    parser.add_option("-m", "--mac-addr", type="string", default="",
                      help="use USRP2 at specified MAC address [default=None]")  
    parser.add_option("-f", "--freq", type="eng_float", default=None,
                      help="set frequency to FREQ", metavar="FREQ")
    parser.add_option("-g", "--gain", type="eng_float", default=None,
                      help="set gain in dB (default is midpoint)")
    parser.add_option("", "--lo-offset", type="eng_float", default=None,
                      help="set daughterboard LO offset to OFFSET [default=hw default]")

    # demodulator related settings
    parser.add_option("-c", "--calibration", type="int", default=0, help="freq offset")
    parser.add_option("-l", "--log", action="store_true", default=False, help="dump debug .dat files")
    parser.add_option("-L", "--low-pass", type="eng_float", default=25e3, help="low pass cut-off", metavar="Hz")
    parser.add_option("-o", "--output-file", type="string", default="out.float", help="specify the bit output file")
    parser.add_option("-v", "--verbose", action="store_true", default=False, help="dump demodulation data")

    (options, args) = parser.parse_args()
    if len(args) != 0:
        parser.print_help()
        raise SystemExit, 1
    
    if options.freq is None:
        parser.print_help()
        sys.stderr.write('You must specify the frequency with -f FREQ\n');
        raise SystemExit, 1
    
    return (options)

if __name__ == "__main__":
    (options) = get_options()
    tb = my_top_block(options)
    try:
        tb.run()
    except KeyboardInterrupt:
        tb.stop()
