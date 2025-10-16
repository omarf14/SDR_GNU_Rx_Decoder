import socket
from fec import PacketHandler
from crypto import decrypt_aes
from zlib import crc32


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

ASM_SIZE    = 4

# Decoding payload indexes
PAYLOAD_LEN_IDX             = 0
PAYLOAD_LEN_SIZE            = 2
CSP_HEADER_IDX              = PAYLOAD_LEN_SIZE
CSP_HEADER_SIZE             = 4
CONTROL_HEADER_IDX          = CSP_HEADER_IDX+CSP_HEADER_SIZE
CONTROL_HEADER_SIZE         = 5
PAYLOAD_DATA_IDX            = CONTROL_HEADER_IDX+CONTROL_HEADER_SIZE
PAYLOAD_DATA_SIZE           = 208
CRC_IDX                     = PAYLOAD_DATA_IDX+PAYLOAD_DATA_SIZE
CRC_SIZE                    = 4
TOTAL_PAYLOAD_SIZE          = CRC_IDX+CRC_SIZE


aes_key = "1fcbf1aa4e41f18c08524712541e432a"

def decoder(message):
    ec = PacketHandler(None)
    print(f"INFO: Decoding message len {len(message)}")
    
    byte_array = bytes((sum(message[k * 8 + j] << (7 - j) for j in range(8)) for k in range(TOTAL_FRAME_BYTE_LEN)))


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
        found_asm = int.from_bytes(data[:ASM_SIZE], byteorder='little')
        diff = found_asm ^ ACCESS_KEY_32B
        matches32 = 32 - bin(diff).count('1')

        ##### DEBUGGING PRINTING #####
        # print(f"Matching bits: {matches32}.")
        ##############################

        if matches32 >= THRESHOLD32:
            # Decode payload 
            payload, bit_corr, byte_corr = ec.decode_fec(data[ASM_SIZE:ASM_SIZE+RS_BLOCK_LENGTH])
            payload_len = int.from_bytes(payload[:PAYLOAD_LEN_SIZE], byteorder='little')
            print(f"payload_len {payload_len}")
            # print("INFO: Decode success with {} corrected bits, payload_len {} payload: \n{}\n".
            #         format(bit_corr, payload_len, payload[2:payload_len].decode('utf-8', errors='replace')))
            # print("Decoded data: \n{0}\n".format(ec.hexdump(payload[PAYLOAD_LEN_SIZE:TOTAL_PAYLOAD_SIZE])))
            payload_crc = crc32(payload[CSP_HEADER_IDX:CRC_IDX]) & 0xFFFFFFFF
            received_crc = int.from_bytes(payload[CRC_IDX:TOTAL_PAYLOAD_SIZE], byteorder='little')  # or 'little'
            if payload_crc != received_crc:
                print("ERROR: payload CRC missmatch")
            decrypted = decrypt_aes(payload[PAYLOAD_DATA_IDX:CRC_IDX], aes_key)
            print("Decrypted payload data: \n{0}\n".format(ec.hexdump(decrypted[:payload_len])))
        else:
            print(f"ERROR: Matches below threshold {matches32}")


    except Exception as e:

        ##### DEBUGGING PRINTING #####
        # print("WARNING: Unable to decode original data:\n{0}".format(ec.hexdump(byte_array)))
        print(f"ERROR: {e}, idx {0}, data_len {0}")
        ##############################
    

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 52001))

    while 1:
        data, addr = sock.recvfrom(4144)
        decoder(data)


if __name__ == '__main__':
    main()