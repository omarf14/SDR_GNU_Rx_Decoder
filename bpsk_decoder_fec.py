
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# Author: dc04-operations
# GNU Radio version: 3.10.12.0
from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import uhd
import time
import sip
import threading
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from IPython import embed
import decoder_utils as du
import cProfile
import queue
from gnuradio import iio


############## Rx Tune for 4MSPS #############
# SAMP_RATE = 4000000
# BW = 1000000
# RF_GAIN = 50
# LOOP_BW_0 = 0.003
# LOOP_BW = 0.001
# FREQ = 2.23e9
# BWIDTH = BW
# SPS = 8
# SYMBOL_RATE = SAMP_RATE / SPS
# FILTER_CUTOFF = BW*1.2
# FILTER_TRANSITION = 200000

############## Rx Tune for 1MSPS #############
# SAMP_RATE = 1000000
# BW = 250000
# RF_GAIN = 50
# LOOP_BW_0 = 0.003
# LOOP_BW = 0.001
# FREQ = 2.23e9
# BWIDTH = BW
# SPS = 8
# SYMBOL_RATE = SAMP_RATE / SPS
# FILTER_CUTOFF = BW*1.2
# FILTER_TRANSITION = 50000


SAMP_RATE = 1000000
BW = 250000
RF_GAIN = 35
LOOP_BW_0 = 0.008 # Sym Sync Loop (very sensitive)
LOOP_BW = 0.01  # Costas Loop
FREQ = 2.23e9
BWIDTH = BW
SPS = 8
SYMBOL_RATE = SAMP_RATE / SPS
FILTER_CUTOFF = BW*1.2
FILTER_TRANSITION = 50000
ANALOG_SQUELCH = -65

# Global variables
sq_trigger = 0
decode_trigger = 0
tot_ctr = 0
fidx = 250000 # It depend in how many IDLE the transmitter send to avoid look for ASM in it 
decoder_queue = queue.Queue(maxsize=2048)

def monitor_squelch(tb):
    while tb.flowgraph_started.is_set():
        check_squelch_state(tb)
        # time.sleep(0.1)

def check_squelch_state(tb):
    global sq_trigger, fidx
    global decode_trigger, tot_ctr
    val = tb.probe.level()

    # Check squelch level to avoid processing garbage 
    if abs(val) == 0.0:

        # This block is executed when the squelch is switched off.
        if sq_trigger:
            tout = 0

            # Wait a second to ensure there is no signal (FIXME: this tout can be reduced)
            while abs(val) == 0 and tout < 500:
                val = tb.probe.level()
                tout+=1
                time.sleep(0.001)
            
            # If tout reached means that a transmission has finished
            if tout >= 500:

                ##### DEBUGGING PRINTING #####
                # print(f"INFO: 🔇 Signal not detected after tout, squelch is closed.")
                ##############################


                # Process pending block of data
                ctr, idx = du.prefilter_data(tb, fidx)
                tot_ctr += ctr
                print(f"INFO: Total messages decoded {tot_ctr}, last idx {fidx}")

                # Reset buffer and control variables
                tb.vector_sink_sym_sync.reset()
                sq_trigger = 0
                fidx = 250000
                tot_ctr = 0


    elif abs(val.real) > 0.1:

        # This block is executed when the squelch is switched on.
        if sq_trigger == 0:
            print(f"INFO: 🔊 Signal detected, squelch is open.")

            # Reset buffer to discard garbage and set squelch trigger flag
            tb.vector_sink_sym_sync.reset()
            sq_trigger = 1

        # Decode data from last idx 
        len_sym = len(tb.vector_sink_sym_sync.data())
        if len_sym > fidx:
            print(f"INFO: Looking at idx {fidx}")
            ctr, idx = du.prefilter_data(tb, fidx)
            if ctr:
                fidx = idx + 1
                tot_ctr += ctr
            

class bpsk_rx_nogui(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "bpsk_rx_nogui", catch_exceptions=True)
        # Only keep essential blocks for decoding
        self.bw = bw = BWIDTH
        self.samp_rate = samp_rate = SAMP_RATE
        self.rf_gain = rf_gain = RF_GAIN
        self.loop_bw_0 = loop_bw_0 = LOOP_BW_0
        self.loop_bw = loop_bw = LOOP_BW
        self.freq = freq = FREQ
        self.bwidth = bwidth = BW

        if 0:
            self.source = uhd.usrp_source(
                ",".join(("", '')),
                uhd.stream_args(
                    cpu_format="sc16",
                    args='',
                    channels=list(range(0,1)),
                ),
            )
            self.source.set_samp_rate(samp_rate)
            self.source.set_center_freq(freq, 0)
            self.source.set_antenna("RX2", 0)
            self.source.set_bandwidth(bw, 0)
            self.source.set_gain(rf_gain, 0)
            self.source.set_auto_dc_offset(True, 0)
            self.source.set_auto_iq_balance(True, 0)
        else:
            self.source = iio.fmcomms2_source_fc32('' if '' else iio.get_pluto_uri(), [True, True], 32768)
            self.source.set_len_tag_key('packet_len')
            self.source.set_frequency(2230000000)
            self.source.set_samplerate(1000000)
            self.source.set_gain_mode(0, 'manual')
            self.source.set_gain(0, rf_gain)
            self.source.set_quadrature(True)
            self.source.set_rfdc(True)
            self.source.set_bbdc(True)
            self.source.set_filter_params('Auto', '', 0, 0)

        self.low_pass_filter_0 = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                (bwidth*1.2),
                FILTER_TRANSITION,
                window.WIN_HAMMING,
                0.35))
        self.digital_symbol_sync_xx_0_0 = digital.symbol_sync_cc(
                                                        digital.TED_MUELLER_AND_MULLER,
                                                        SPS,
                                                        loop_bw_0,
                                                        1.0,
                                                        0.1,
                                                        1.5,
                                                        1,
                                                        digital.constellation_bpsk().base(),
                                                        digital.IR_MMSE_8TAP,
                                                        128,
                                                        [])
        self.digital_costas_loop_cc_0_0 = digital.costas_loop_cc(loop_bw, 2, False)
        # self.blocks_throttle2_0 = blocks.throttle(  
        #                             gr.sizeof_gr_complex*1, 
        #                             samp_rate, 
        #                             True, 
        #                             0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 
        #                             1) )
        self.blocks_interleaved_short_to_complex_0 = blocks.interleaved_short_to_complex(True, False,2047)
        self.blocks_correctiq_auto_0_0 = blocks.correctiq_auto(samp_rate, freq, 1.5, 2)
        self.blocks_complex_to_float_0 = blocks.complex_to_float(1)
        self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_cc((ANALOG_SQUELCH), (1e-4), True, False)
        self.vector_sink_sym_sync = blocks.vector_sink_f()
        self.probe = blocks.probe_signal_c()

        # self.connect((self.source, 0), (self.blocks_interleaved_short_to_complex_0, 0))
        self.connect((self.source, 0), (self.low_pass_filter_0, 0))
        # self.connect((self.blocks_interleaved_short_to_complex_0, 0), (self.blocks_throttle2_0, 0))
        # self.connect((self.blocks_throttle2_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.connect(self.analog_pwr_squelch_xx_0, self.probe)
        self.connect((self.analog_pwr_squelch_xx_0, 0), (self.blocks_correctiq_auto_0_0, 0))
        self.connect((self.blocks_correctiq_auto_0_0, 0), (self.digital_costas_loop_cc_0_0, 0))
        # self.connect((self.analog_pwr_squelch_xx_0, 0), (self.digital_costas_loop_cc_0_0, 0))
        self.connect((self.digital_costas_loop_cc_0_0, 0), (self.digital_symbol_sync_xx_0_0, 0))
        self.connect((self.digital_symbol_sync_xx_0_0, 0), (self.blocks_complex_to_float_0, 0))
        self.connect((self.blocks_complex_to_float_0, 0), (self.vector_sink_sym_sync, 0))


def main(options=None):

    profiler = cProfile.Profile()
    profiler.enable()

    tb = bpsk_rx_nogui()
    tb.start()
    tb.flowgraph_started = threading.Event()
    tb.flowgraph_started.set()
    squelch_th = threading.Thread(target=monitor_squelch, args=(tb,), daemon=True)
    squelch_th.start()
    decoder_th = threading.Thread(target=du.decoder_thread, daemon=True)
    decoder_th.start()

    try:
        tb.wait()
        # while True:
        #     # check_squelch_state(tb)
        #     continue

    except KeyboardInterrupt:
        tb.stop()
        tb.wait()
        squelch_th.join()
        decoder_th.join()
        profiler.disable()
        profiler.print_stats(sort='cumtime')

if __name__ == '__main__':
    main()
