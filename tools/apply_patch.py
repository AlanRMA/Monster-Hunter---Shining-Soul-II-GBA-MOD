"""Apply BPS1 with CRC validation; no dependency on an emulator or native tools.

Format reference: https://github.com/Sir-Walrus/Flips/blob/master/bps_spec.md
"""
from pathlib import Path
import argparse, struct, zlib

def apply(source, patch):
    if patch[:4] != b'BPS1' or len(patch) < 19:
        raise ValueError('Not a BPS1 patch')
    source_crc, target_crc, patch_crc = struct.unpack_from('<III', patch, len(patch)-12)
    if zlib.crc32(source) != source_crc or zlib.crc32(patch[:-4]) != patch_crc:
        raise ValueError('Original ROM or patch checksum mismatch')
    cursor = 4
    def number():
        nonlocal cursor
        value, shift = 0, 1
        while True:
            if cursor >= len(patch)-12:
                raise ValueError('Truncated BPS number')
            byte = patch[cursor]; cursor += 1
            value += (byte & 127)*shift
            if byte & 128: return value
            shift <<= 7; value += shift
            if shift > 1 << 63: raise ValueError('Excessive BPS number')
    size_in, size_out, metadata = number(), number(), number()
    if size_in != len(source) or size_out > 64*1024*1024:
        raise ValueError('Unexpected ROM size')
    cursor += metadata
    if cursor > len(patch)-12: raise ValueError('Truncated metadata')
    out = bytearray(); src_relative = dst_relative = 0
    while len(out) < size_out:
        action = number(); mode, length = action & 3, (action >> 2)+1
        if len(out)+length > size_out: raise ValueError('Output overrun')
        if mode == 0:
            start = len(out)
            if start+length > len(source): raise ValueError('Source overrun')
            out.extend(source[start:start+length])
        elif mode == 1:
            if cursor+length > len(patch)-12: raise ValueError('Literal overrun')
            out.extend(patch[cursor:cursor+length]); cursor += length
        else:
            delta = number(); offset = -(delta >> 1) if delta & 1 else delta >> 1
            if mode == 2:
                src_relative += offset
                if src_relative < 0 or src_relative+length > len(source):
                    raise ValueError('Source copy overrun')
                out.extend(source[src_relative:src_relative+length]); src_relative += length
            else:
                dst_relative += offset
                if not 0 <= dst_relative < len(out): raise ValueError('Invalid target copy')
                # Overlap is intentional in BPS, including long repeated zero runs.
                period = bytes(out[dst_relative:])
                out.extend((period*((length+len(period)-1)//len(period)))[:length])
                dst_relative += length
    if cursor != len(patch)-12 or zlib.crc32(out) != target_crc:
        raise ValueError('Output checksum or patch length mismatch')
    return bytes(out)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('patch', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists(): parser.error('Output already exists; choose a new filename')
    data = apply(args.original.read_bytes(), args.patch.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as f: f.write(data)
    print(f'Created {args.output} ({len(data)} bytes)')

if __name__ == '__main__': main()
