"""

 Author: OMARF
 Email: omarf@fossa.systems

 Creation Date: 2025-09-08 11:48:44

 

"""
# from fec import PacketHandler

import os
import struct
import hashlib
import hmac
import ctypes
import codecs
from fec import PacketHandler

VITERBI_RATE = 2
VITERBI_TAIL = 1
VITERBI_CONSTRAINT = 7
BITS_PER_BYTE = 8
MAX_FEC_LENGTH = 255
RS_LENGTH = 32
RS_BLOCK_LENGTH = 255
HMAC_LENGTH = 2
HMAC_KEY_LENGTH = 16
SIZE_LENGTH = 2
CSP_OVERHEAD = 4
SHORT_FRAME_LIMIT = 25
LONG_FRAME_LIMIT = 86
TOTAL_FRAME_BIT_LEN = (255)*VITERBI_RATE*8
TOTAL_FRAME_BYTE_LEN = (255)*VITERBI_RATE
ASM_BIT_LEN = 64
ACCESS_KEY_32B = 0xe15ae893
ACCES_KEY_CONVOLVED_64B = 0xB9F8B220B1CF12BC
THRESHOLD64 = 50
THRESHOLD32 = 26

path = os.path.dirname(os.path.abspath(__file__))
bbfec = ctypes.CDLL(path + "/bbfec.so")
# viterbi
bbfec.create_viterbi.argtypes = [ctypes.c_int16]
bbfec.create_viterbi.restype = ctypes.c_void_p
bbfec.init_viterbi.argtypes = [ctypes.c_void_p, ctypes.c_int]
bbfec.init_viterbi.restype = ctypes.c_int
bbfec.update_viterbi.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint16]
bbfec.update_viterbi.restype = ctypes.c_int
bbfec.chainback_viterbi.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint]
bbfec.chainback_viterbi.restype = ctypes.c_int
bbfec.delete_viterbi.argtypes = [ctypes.c_void_p]
bbfec.delete_viterbi.restype = None
bbfec.encode_viterbi.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
bbfec.encode_viterbi.restype = None
# rs
bbfec.encode_rs.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
bbfec.encode_rs.restype = None
bbfec.decode_rs.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
bbfec.decode_rs.restype = ctypes.c_int
# randomizer
bbfec.ccsds_generate_sequence.argtypes = [ctypes.c_char_p, ctypes.c_int]
bbfec.ccsds_generate_sequence.restype = None
bbfec.ccsds_xor_sequence.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
bbfec.ccsds_xor_sequence.restype = None


def decode_data(tb, st_idx):
    # Initialize objects 
    symbols = tb.vector_sink_sym_sync.data()
    ec = PacketHandler(None)

    # Convert BPSK symbols to bits
    bits = [1 if v >= 0.0 else 0 for v in symbols]

    # BPSK differential decoding
    diff_bits = []
    prev = 0
    for b in bits:
        diff = b ^ prev
        diff_bits.append(diff)
        prev = b

    # Main decoding loop
    msg_ctr = 0
    i=st_idx
    while i + ASM_BIT_LEN + TOTAL_FRAME_BIT_LEN <= len(diff_bits):
        # Look for convolved access code
        segment = diff_bits[i:i+ASM_BIT_LEN]
        segment_int = 0
        for bit in segment:
            segment_int = (segment_int << 1) | bit
        xor_result = segment_int ^ ACCES_KEY_CONVOLVED_64B
        matches64 = 64 - bin(xor_result).count('1')

        # If enough matches, proceed with the decoding process
        if matches64 >= THRESHOLD64:
            idx = i

            ##### DEBUGGING PRINTING #####
            # print(f"INFO: Acces key found at index {idx}, matches = {matches}")
            ##############################

            # Generate a byte array with the 510 bytes encoded
            message = diff_bits[i:i+TOTAL_FRAME_BIT_LEN]
            byte_array = bytes((sum(message[k * 8 + j] << (7 - j) for j in range(8)) for k in range(TOTAL_FRAME_BYTE_LEN)))

            ##### DEBUGGING PRINTING #####
            # print("Original data:\n{0}\n".format(ec.hexdump(TESTDATA)))
            ##############################

            try:
                # Unconvolve data to check ASM
                data, bit_corr, byte_corr = ec.decode_viterbi(byte_array)


                ##### DEBUGGING PRINTING #####
                # print("Decoded data: ({0},{1})\n{2}\n".format(bit_corr, byte_corr, ec.hexdump(data)))
                # asm_found = data[0:4][::-1].hex()
                # print(f"ASM found: 0x{asm_found}")
                ##############################


                # Check Attached Sync Marker after viterbi processing
                found_asm = int.from_bytes(data[0:4], byteorder='little')
                diff = found_asm ^ ACCESS_KEY_32B
                matches32 = 32 - bin(diff).count('1')

                ##### DEBUGGING PRINTING #####
                # print(f"Matching bits: {matches}.")
                ##############################

                if matches32 >= THRESHOLD32:
                    # Decode payload 
                    data, bit_corr, byte_corr = ec.decode_fec(data[4:258])
                    payload_len = int.from_bytes(data[0:2], byteorder='little')
                    print(f"INFO: Acces key found at index {idx}, matches = {matches64}, matches2 = {matches32}")
                    print("INFO: Decode success with {} corrected bits, payload: \n{}\n".format(bit_corr, data[2:payload_len].decode('utf-8', errors='replace')))
                    msg_ctr += 1
                    i = i + TOTAL_FRAME_BIT_LEN - 8*10
                    continue

            except Exception as e:

                ##### DEBUGGING PRINTING #####
                # print("WARNING: Unable to decode original data:\n{0}".format(ec.hexdump(encoded_data)))
                # print(f"ERROR: {e}, idx {idx}, data_len {len(diff_bits)}")
                ##############################

                if ((len(diff_bits) - idx) < 4096):
                    idx -=1
                    break
        
        i+=1

    if msg_ctr:
        return msg_ctr, idx
    else:
        return 0, 0