from gnuradio import gr
import numpy as np
import pmt

class tag_printer_bb(gr.sync_block):
    """
    Custom sink block to print bytes in the stream near the 'ac_found' tag.
    """
    def __init__(self, tag_key='ac_found', window=64):
        gr.sync_block.__init__(
            self,
            name="tag_printer_bb",
            in_sig=[np.uint8],
            out_sig=[]
        )
        self.tag_key = pmt.intern(tag_key)
        self.window = window

    def work(self, input_items, output_items):
        in0 = input_items[0]
        nread = self.nitems_read(0)

        # Get all tags in this range
        tags = self.get_tags_in_range(0, nread, nread + len(in0))

        for tag in tags:
            if tag.key == self.tag_key:
                tag_offset = tag.offset - nread  # position in current buffer

                if 0 <= tag_offset < len(in0):
                    start = max(0, tag_offset)
                    end = min(len(in0), tag_offset + self.window)
                    tagged_bytes = in0[start:end]

                    print(f"[Tag @ {tag.offset}] ac_found -> Bytes: {list(tagged_bytes)}")

        return len(in0)
