import ctypes as C
import struct
import sys
from pathlib import Path
from PIL import Image

OUT = Path(__file__).parent
LIB = C.CDLL('/Applications/mGBA.app/Contents/MacOS/mGBA')
LIB.GBACoreCreate.restype = C.c_void_p
LIB.mCoreInitConfig.argtypes = [C.c_void_p, C.c_char_p]
LIB.mCoreLoadFile.argtypes = [C.c_void_p, C.c_char_p]
LIB.mCoreLoadFile.restype = C.c_bool
LIB.mCoreGetMemoryBlock.argtypes = [C.c_void_p, C.c_uint32, C.POINTER(C.c_size_t)]
LIB.mCoreGetMemoryBlock.restype = C.c_void_p
LOG_FN = C.CFUNCTYPE(None, C.c_void_p, C.c_int, C.c_int, C.c_char_p, C.c_void_p)
class Logger(C.Structure):
    _fields_ = [('log', LOG_FN), ('filter', C.c_void_p)]
LOG_CALLBACK = LOG_FN(lambda *args: None)
LOGGER = Logger(LOG_CALLBACK, None)
LIB.mLogSetDefaultLogger.argtypes = [C.c_void_p]
LIB.mLogSetDefaultLogger(C.byref(LOGGER))

NAMES = '''init deinit platform supportsFeature setSync loadConfig reloadConfigOption desiredVideoDimensions setVideoBuffer setVideoGLTex getPixels putPixels getAudioChannel setAudioBufferSize getAudioBufferSize addCoreCallbacks clearCoreCallbacks setAVStream isROM loadROM loadSave loadTemporarySave unloadROM romSize checksum loadBIOS selectBIOS loadPatch reset runFrame runLoop step stateSize loadState saveState setKeys addKeys clearKeys getKeys frameCounter frameCycles frequency getGameTitle getGameCode setPeripheral busRead8 busRead16 busRead32 busWrite8 busWrite16 busWrite32 rawRead8 rawRead16 rawRead32 rawWrite8 rawWrite16 rawWrite32 listMemoryBlocks getMemoryBlock listRegisters readRegister writeRegister supportsDebuggerType debuggerPlatform cliDebuggerSystem attachDebugger detachDebugger loadSymbols lookupIdentifier cheatDevice savedataClone savedataRestore listVideoLayers listAudioChannels enableVideoLayer enableAudioChannel adjustVideoLayer startVideoLog endVideoLog'''.split()

class Emulator:
    def __init__(self, rom):
        self.core = LIB.GBACoreCreate()
        # The init address is verified against this exact installed 0.10.5 build.
        slide = C.cast(LIB.GBACoreCreate, C.c_void_p).value - 0x1002d2b98
        init_addr = slide + 0x1002d2f80
        raw = C.string_at(self.core, 0x1000)
        self.vtable = raw.find(struct.pack('<Q', init_addr))
        if self.vtable < 0 or self.vtable % 8:
            raise RuntimeError('mCore ABI verification failed')
        assert self.func('init', C.c_bool)(self.core)
        LIB.mCoreInitConfig(self.core, b'ss2-isolated-test')
        self.video = (C.c_uint32 * (240 * 160))()
        self.func('setVideoBuffer', None, C.c_void_p, C.c_size_t)(self.core, self.video, 240)
        self.func('setAudioBufferSize', None, C.c_size_t)(self.core, 512)
        assert LIB.mCoreLoadFile(self.core, str(rom).encode())
        self.func('reset')(self.core)
        self.frame = self.func('runFrame')
        self.step = self.func('step')
        self.read16 = self.func('busRead16', C.c_uint32, C.c_uint32)
        self.read32 = self.func('busRead32', C.c_uint32, C.c_uint32)
        self.keys = self.func('setKeys', None, C.c_uint32)

    def func(self, name, restype=None, *args):
        pointer = C.c_void_p.from_address(self.core + self.vtable + NAMES.index(name) * 8).value
        return C.CFUNCTYPE(restype, C.c_void_p, *args)(pointer)

    def memory(self, base, length):
        size = C.c_size_t()
        ptr = LIB.mCoreGetMemoryBlock(self.core, base, C.byref(size))
        if not ptr or length > size.value:
            raise RuntimeError(f'Invalid block {base:x} {size.value}')
        return C.string_at(ptr, length)

    def register(self, name):
        value = C.c_uint32()
        assert self.func('readRegister', C.c_bool, C.c_char_p, C.c_void_p)(self.core, name.encode(), C.byref(value))
        return value.value

    def screenshot(self, path):
        Image.frombytes('RGBA', (240, 160), bytes(self.video)).convert('RGB').save(path)

    def dump(self, label):
        self.screenshot(OUT / f'{label}.png')
        for name, base, length in [('vram', 0x06000000, 0x18000), ('palette', 0x05000000, 0x400), ('ewram', 0x02000000, 0x40000), ('iwram', 0x03000000, 0x8000)]:
            (OUT / f'{label}-{name}.bin').write_bytes(self.memory(base, length))
        print(label, 'PC', hex(self.register('pc')), 'DISPCNT', hex(self.read16(self.core, 0x04000000)), 'BG1CNT', hex(self.read16(self.core, 0x0400000a)), flush=True)

if __name__ == '__main__':
    e = Emulator(sys.argv[1])
    for n in range(1, 901):
        e.frame(e.core)
        if n in [120, 300, 600, 900]:
            e.dump(f'original-{n}')
