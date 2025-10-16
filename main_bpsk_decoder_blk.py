#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# Author: gs
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import iio
import pmt
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
from tag_printer_blk import tag_printer_bb
from tag_to_pdu_blk import tag_to_pdu_udp_bb




class pluto(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "pluto")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.bw = bw = 250000
        self.variable_tag_object_0 = variable_tag_object_0 = gr.tag_utils.python_to_tag((0, pmt.intern("key"), pmt.intern("value"), pmt.intern("src")))
        self.sync_loop = sync_loop = 0.008
        self.samp_rate = samp_rate = 1000000
        self.rf_gain = rf_gain = 45
        self.freq = freq = 2.23e9
        self.costas_loop = costas_loop = 0.01
        self.bwidth = bwidth = bw
        self.bpsk_o_2 = bpsk_o_2 = digital.constellation_calcdist([-1-0j, +1+0j], [0, 1],
        2, 1, digital.constellation.AMPLITUDE_NORMALIZATION).base()
        # self.bpsk_o_2.set_npwr(1.0)
        self.bpsk_o = bpsk_o = digital.constellation_bpsk().base()
        # self.bpsk_o.set_npwr(1.0)
        self.TED_gain = TED_gain = 0.02

        ##################################################
        # Blocks
        ##################################################

        self._sync_loop_range = qtgui.Range(0.001, 0.05, 0.001, 0.008, 200)
        self._sync_loop_win = qtgui.RangeWidget(self._sync_loop_range, self.set_sync_loop, "'sync_loop'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._sync_loop_win)
        self._rf_gain_range = qtgui.Range(0, 150, 10, 35, 200)
        self._rf_gain_win = qtgui.RangeWidget(self._rf_gain_range, self.set_rf_gain, "'rf_gain'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rf_gain_win)
        self._freq_range = qtgui.Range(2e9, 2.5e9, 2e3, 2.23e9, 200)
        self._freq_win = qtgui.RangeWidget(self._freq_range, self.set_freq, "'freq'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._freq_win)
        self._costas_loop_range = qtgui.Range(0, 0.1, 0.01, 0.01, 200)
        self._costas_loop_win = qtgui.RangeWidget(self._costas_loop_range, self.set_costas_loop, "'costas_loop'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._costas_loop_win)
        self._bwidth_range = qtgui.Range(200e3, 10e6, 10000, bw, 200)
        self._bwidth_win = qtgui.RangeWidget(self._bwidth_range, self.set_bwidth, "'bwidth'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._bwidth_win)
        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            bw, #bw
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0.set_update_time(0.10)
        self.qtgui_waterfall_sink_x_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_0.set_intensity_range(-140, 10)

        self._qtgui_waterfall_sink_x_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0.qwidget(), Qt.QWidget)

        self.top_layout.addWidget(self._qtgui_waterfall_sink_x_0_win)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "", #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(True)
        self.qtgui_freq_sink_x_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_0_win)
        self.qtgui_const_sink_x_0_0 = qtgui.const_sink_c(
            1024, #size
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0_0.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0_0.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0_0.enable_grid(False)
        self.qtgui_const_sink_x_0_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_0_0_win)
        self.low_pass_filter_0 = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                (bwidth*1.2),
                50000,
                window.WIN_HAMMING,
                0.35))
        self.iio_pluto_source_0 = iio.fmcomms2_source_fc32('' if '' else iio.get_pluto_uri(), [True, True], 32768)
        self.iio_pluto_source_0.set_len_tag_key('packet_len')
        self.iio_pluto_source_0.set_frequency(2230000000)
        self.iio_pluto_source_0.set_samplerate(1000000)
        self.iio_pluto_source_0.set_gain_mode(0, 'manual')
        self.iio_pluto_source_0.set_gain(0, rf_gain)
        self.iio_pluto_source_0.set_quadrature(True)
        self.iio_pluto_source_0.set_rfdc(True)
        self.iio_pluto_source_0.set_bbdc(True)
        self.iio_pluto_source_0.set_filter_params('Auto', '', 0, 0)
        self.digital_symbol_sync_xx_0_0 = digital.symbol_sync_cc(
            digital.TED_MUELLER_AND_MULLER,
            8,
            sync_loop,
            1.0,
            0.1,
            1.5,
            1,
            digital.constellation_bpsk().base(),
            digital.IR_MMSE_8TAP,
            128,
            [])
        self.digital_diff_decoder_bb_0 = digital.diff_decoder_bb(2, digital.DIFF_DIFFERENTIAL)
        self.digital_costas_loop_cc_0_0 = digital.costas_loop_cc(costas_loop, 2, False)
        self.digital_correlate_access_code_tag_xx_0 = digital.correlate_access_code_tag_bb('1011100111111000101100100010000010110001110011110001001010111100', 8, 'ac_found')
        self.digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        self.blocks_correctiq_auto_0_0_0 = blocks.correctiq_auto(samp_rate, freq, 1.5, 2)
        self.blocks_complex_to_float_0 = blocks.complex_to_float(1)
        self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_cc((-70), (1e-4), True, True)
        self._TED_gain_range = qtgui.Range(0.01, 0.1, 0.01, 0.02, 200)
        self._TED_gain_win = qtgui.RangeWidget(self._TED_gain_range, self.set_TED_gain, "'TED_gain'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._TED_gain_win)
        # self.tag_printer = tag_printer_bb('ac_found')
        # self.pdu_printer = tag_to_pdu_printer_bb()
        # self.tag_to_pdu = tag_to_pdu_udp_bb('ac_found', 4144, '127.0.0.1', 52001)
        self.tag_to_pdu = tag_to_pdu_udp_bb(
            tag_key='ac_found',
            pdu_len=4144,
            # marker_len=64,
            udp_ip='127.0.0.1',
            udp_port=52001
        )





        ##################################################
        # Connections
        ##################################################
        self.connect((self.iio_pluto_source_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.qtgui_waterfall_sink_x_0, 0))
        self.connect((self.analog_pwr_squelch_xx_0, 0), (self.blocks_correctiq_auto_0_0_0, 0))
        self.connect((self.blocks_correctiq_auto_0_0_0, 0), (self.digital_costas_loop_cc_0_0, 0))
        self.connect((self.digital_costas_loop_cc_0_0, 0), (self.digital_symbol_sync_xx_0_0, 0))
        self.connect((self.digital_symbol_sync_xx_0_0, 0), (self.blocks_complex_to_float_0, 0))
        self.connect((self.digital_symbol_sync_xx_0_0, 0), (self.qtgui_const_sink_x_0_0, 0))
        self.connect((self.blocks_complex_to_float_0, 0), (self.digital_binary_slicer_fb_0, 0))
        self.connect((self.digital_binary_slicer_fb_0, 0), (self.digital_diff_decoder_bb_0, 0))
        self.connect((self.digital_diff_decoder_bb_0, 0), (self.digital_correlate_access_code_tag_xx_0, 0))
        self.connect((self.digital_correlate_access_code_tag_xx_0, 0), (self.tag_to_pdu, 0))
        # self.connect((self.digital_correlate_access_code_tag_xx_0, 0), (self.tag_printer, 0))
        # self.connect((self.digital_correlate_access_code_tag_xx_0, 0), (self.pdu_printer, 0))




    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "pluto")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_bw(self):
        return self.bw

    def set_bw(self, bw):
        self.bw = bw
        self.set_bwidth(self.bw)
        self.qtgui_waterfall_sink_x_0.set_frequency_range(0, self.bw)

    def get_variable_tag_object_0(self):
        return self.variable_tag_object_0

    def set_variable_tag_object_0(self, variable_tag_object_0):
        self.variable_tag_object_0 = variable_tag_object_0

    def get_sync_loop(self):
        return self.sync_loop

    def set_sync_loop(self, sync_loop):
        self.sync_loop = sync_loop
        self.digital_symbol_sync_xx_0_0.set_loop_bandwidth(self.sync_loop)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, (self.bwidth*1.2), 50000, window.WIN_HAMMING, 0.35))
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)

    def get_rf_gain(self):
        return self.rf_gain

    def set_rf_gain(self, rf_gain):
        self.rf_gain = rf_gain
        self.iio_pluto_source_0.set_gain(0, self.rf_gain)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.blocks_correctiq_auto_0_0_0.set_freq(self.freq)

    def get_costas_loop(self):
        return self.costas_loop

    def set_costas_loop(self, costas_loop):
        self.costas_loop = costas_loop
        self.digital_costas_loop_cc_0_0.set_loop_bandwidth(self.costas_loop)

    def get_bwidth(self):
        return self.bwidth

    def set_bwidth(self, bwidth):
        self.bwidth = bwidth
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, (self.bwidth*1.2), 50000, window.WIN_HAMMING, 0.35))

    def get_bpsk_o_2(self):
        return self.bpsk_o_2

    def set_bpsk_o_2(self, bpsk_o_2):
        self.bpsk_o_2 = bpsk_o_2

    def get_bpsk_o(self):
        return self.bpsk_o

    def set_bpsk_o(self, bpsk_o):
        self.bpsk_o = bpsk_o

    def get_TED_gain(self):
        return self.TED_gain

    def set_TED_gain(self, TED_gain):
        self.TED_gain = TED_gain




def main(top_block_cls=pluto, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
