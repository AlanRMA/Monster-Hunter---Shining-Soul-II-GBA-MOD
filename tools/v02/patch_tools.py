import struct

def thumb_bl(source, target):
    distance = target - source - 4
    assert distance % 2 == 0 and -0x400000 <= distance < 0x400000
    return struct.pack('<HH', 0xF000 | ((distance >> 12) & 0x7FF), 0xF800 | ((distance >> 1) & 0x7FF))

class Thumb:
    def __init__(self, base):
        self.base=base;self.code=bytearray();self.literals=[];self.labels={};self.branches=[]
    def h(self, *values):
        self.code.extend(struct.pack('<'+'H'*len(values),*values))
    def bl(self, target):
        self.code.extend(thumb_bl(self.base+len(self.code),target))
    def literal(self, register, value):
        offset=len(self.code);self.h(0)
        self.literals.append((offset,register,value))
    def abs_bl(self, target):
        self.literal(3,target|1)
        self.bl(self.base+len(self.code)+6)
        self.h(0xE000,0x4718) # return skips the bx-r3 interworking stub
    def label(self, name):
        self.labels[name]=len(self.code)
    def branch(self, name, condition=None):
        self.branches.append((len(self.code),name,condition));self.h(0)
    def finish(self):
        for offset,name,condition in self.branches:
            delta=self.labels[name]-offset-4
            assert delta%2==0
            if condition is None:
                assert -2048<=delta<=2046
                opcode=0xE000|((delta//2)&0x7FF)
            else:
                assert -256<=delta<=254
                opcode=0xD000|(condition<<8)|((delta//2)&0xFF)
            struct.pack_into('<H',self.code,offset,opcode)
        if len(self.code)%4:self.h(0x46C0)
        for offset,register,value in self.literals:
            target=self.base+len(self.code)
            source=(self.base+offset+4)&~3
            displacement=target-source
            assert 0<=displacement<=1020 and displacement%4==0
            struct.pack_into('<H',self.code,offset,0x4800|(register<<8)|(displacement//4))
            self.code.extend(struct.pack('<I',value))
        return bytes(self.code)
