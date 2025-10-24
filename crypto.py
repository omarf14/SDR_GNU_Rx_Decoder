"""

 Author: Álvaro Mazo Palomo
 Email: alvarom@fossa.systems

 Creation Date: 2025-04-22 10:02:14
 Last Modification Date: 2025-06-09 13:46:25

 

"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii

def hex_to_bytes(hex_str):
    try:
        return binascii.unhexlify(hex_str)
    except binascii.Error:
        print("Error: Entrada no válida. Asegúrate de que sea hexadecimal.")
        exit(1)

def parse_key_input(key_input):
    key_input = key_input.strip()
    
    # Formato: 0xAA, 0xBB, ...
    if ',' in key_input and '0x' in key_input.lower():
        try:
            bytes_list = key_input.split(',')
            key_bytes = bytes(int(b.strip(), 16) for b in bytes_list)
            return key_bytes
        except ValueError:
            exit(1)
    else:
        # Hex plano
        if len(key_input) != 32:
            print("Error: La clave debe tener 32 caracteres hexadecimales (16 bytes).")
            exit(1)
        return hex_to_bytes(key_input)

def encrypt_aes( payload: bytearray, key_hex: str ):
    key = parse_key_input(key_hex)
    iv = bytes([0] * 16)  # IV de 16 bytes en cero

    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        # print(len(payload))
        #print(payload)
        #padded_payload = pad(payload, AES.block_size)
        cipher_payload = cipher.encrypt(payload)
    except Exception as e:
        print(f"Error al encriptar: {e}")
    return cipher_payload

def decrypt_aes(payload: bytearray, key_hex: str) -> bytes:
    key = parse_key_input(key_hex)
    iv = bytes([0] * 16)  # IV de 16 bytes en cero
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_payload = cipher.decrypt(payload)
    except Exception as e:
        print(f"Error al desencriptar: {e}")
    return decrypted_payload
