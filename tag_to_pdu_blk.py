from gnuradio import gr
import numpy as np
import pmt
import socket

class tag_to_pdu_udp_bb(gr.basic_block):
    def __init__(self, tag_key="ac_found", pdu_len=1441, udp_ip="127.0.0.1", udp_port=52001):
        gr.basic_block.__init__(
            self,
            name="tag_to_pdu_udp_bb",
            in_sig=[np.uint8],
            out_sig=[]
        )
        self.tag_key = pmt.intern(tag_key)
        self.pdu_len = pdu_len
        self.buffer = np.array([], dtype=np.uint8)
        self.waiting_for_pdu = False

         # Keep only last 64 samples
        self.pre_tag_len = 64
        self.last_64 = np.array([], dtype=np.uint8)

        # Setup UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.counter = 0

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        nread = self.nitems_read(0)
        ninput = len(in0)

        # If not buffering, look for tag
        if not self.waiting_for_pdu:
            tags = self.get_tags_in_range(0, nread, nread + ninput)
            for tag in tags:
                if tag.key == self.tag_key:
                    relative_offset = tag.offset - nread - 64
                    # print(f"[INFO] Tag found at offset {tag.offset}, relative offset {relative_offset} start buffering.")
                    if 0 <= relative_offset < ninput:
                        self.buffer = in0[relative_offset:].copy()
                        self.waiting_for_pdu = True
                        break
                    elif relative_offset < 0:
                        self.buffer = np.concatenate((self.last_64[relative_offset:], in0[0:]))
                        self.waiting_for_pdu = True
                        break

        else:
            # Continue buffering
            self.buffer = np.concatenate((self.buffer, in0))

        # If full PDU is ready
        if self.waiting_for_pdu and len(self.buffer) >= self.pdu_len:
            pdu_bytes = self.buffer[:self.pdu_len]
            meta = pmt.make_dict()
            vec = pmt.init_u8vector(self.pdu_len, list(pdu_bytes))
            pdu = pmt.cons(meta, vec)

            # Print (optional)
            # print(f"\n🔔 PDU ready: {self.pdu_len} bytes")
            # print(list(pdu_bytes[:20]), "...")

            # Send over UDP
            try:
                self.sock.sendto(pdu_bytes.tobytes(), (self.udp_ip, self.udp_port))
                self.counter += 1
                print(f"Sent PDU to {self.udp_ip}:{self.udp_port}, ctr {self.counter}")
            except Exception as e:
                print(f"UDP send failed: {e}")

            # Reset
            self.buffer = np.array([], dtype=np.uint8)
            self.waiting_for_pdu = False
        
        # Save last 64 symbols for next execution
        if len(in0) >= self.pre_tag_len:
            self.last_64 = in0[-self.pre_tag_len:].copy()
        else:
            self.last_64 = np.concatenate((self.last_64, in0))
            if len(self.last_64) > self.pre_tag_len:
                self.last_64 = self.last_64[-self.pre_tag_len:]

        self.consume(0, ninput)
        return ninput if ninput > 0 else 1

    def stop(self):
        self.sock.close()
        return True
