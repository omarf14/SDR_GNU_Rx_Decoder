import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 52001))


import os
import struct
import hashlib
import hmac
import ctypes
import codecs
import time
from fec import PacketHandler
# from bpsk_decoder_fec import decoder_queue


VITERBI_RATE = 2
VITERBI_TAIL = 1
VITERBI_CONSTRAINT = 7
BITS_PER_BYTE = 8
MAX_FEC_LENGTH = 255
RS_LENGTH = 32
RS_BLOCK_LENGTH = 255
ASM_BIT_LEN = 64
RAW_ASM_BYTE_LEN = 4 
HMAC_LENGTH = 2
HMAC_KEY_LENGTH = 16
SIZE_LENGTH = 2
CSP_OVERHEAD = 4
SHORT_FRAME_LIMIT = 25
LONG_FRAME_LIMIT = 86
TOTAL_FRAME_BIT_LEN = (RS_BLOCK_LENGTH + RAW_ASM_BYTE_LEN)*VITERBI_RATE*8
TOTAL_FRAME_BYTE_LEN = (RS_BLOCK_LENGTH + RAW_ASM_BYTE_LEN)*VITERBI_RATE
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

def decoder(message):
    ec = PacketHandler(None)
    print(f"INFO: Decoding message len {len(message)}")
    
    byte_array = bytes((sum(message[k * 8 + j] << (7 - j) for j in range(8)) for k in range(TOTAL_FRAME_BYTE_LEN)))
    # byte_array = bytes((
    #     sum(message[k * 8 + j] << j for j in range(8))  # LSB first
    #     for k in range(TOTAL_FRAME_BYTE_LEN)
    #     ))


    ##### DEBUGGING PRINTING #####
    # print("Original data:\n{0}\n".format(ec.hexdump(byte_array)))
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
        # print(f"Matching bits: {matches32}.")
        ##############################

        if matches32 >= THRESHOLD32:
            # Decode payload 
            payload, bit_corr, byte_corr = ec.decode_fec(data[4:258])
            payload_len = int.from_bytes(payload[0:2], byteorder='little')
            # print(f"INFO: Acces key found at index {idx}, matches = {matches64}, matches2 = {matches32}")
            # payload_len = 255 if payload_len > 255 else payload_len
            print("INFO: Decode success with {} corrected bits, payload_len {} payload: \n{}\n".
                    format(bit_corr, payload_len, payload[2:payload_len].decode('utf-8', errors='replace')))
            # msg_ctr += 1
            # i = i + TOTAL_FRAME_BIT_LEN - 8*10
            # continue

    except Exception as e:

        ##### DEBUGGING PRINTING #####
        # print("WARNING: Unable to decode original data:\n{0}".format(ec.hexdump(byte_array)))
        print(f"ERROR: {e}, idx {0}, data_len {0}")
        ##############################
    

while True:
    data, addr = sock.recvfrom(4144)

    # print(f"\n🔔 PDU ready: {len(data)} bytes")
    # print(list(data[:20]), "...")
    # print("Received:", data)
    decoder(data)
