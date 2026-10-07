from emulate import Emulator
from pathlib import Path
import sys

def start_new_game(e, skip_book=True):
    def wait(frames):
        for _ in range(frames):e.frame(e.core)
    def press(keys,after):
        e.keys(e.core,keys);wait(2);e.keys(e.core,0);wait(after)
    wait(900)
    press(8,120)
    press(1,120)
    press(1,100)
    press(1,280)
    press(1,60)
    press(1,60)
    press(1,60)
    press(8,120)
    press(1,200)
    wait(600)
    if skip_book:press(8,240)
    wait(600)

if __name__=='__main__':
    e=Emulator(Path(sys.argv[1]))
    start_new_game(e)
    e.dump(sys.argv[2] if len(sys.argv)>2 else 'new-game')
    print('context',hex(e.read32(e.core,0x0300331c)),'room',hex(e.read32(e.core,0x03003320)))
