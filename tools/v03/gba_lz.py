"""GBA BIOS LZ77; adapted from the project's original title patch."""
def compress(data):
    out=bytearray(b'\x10'+len(data).to_bytes(3,'little'));positions={};p=0
    while p<len(data):
        flagpos=len(out);out.append(0);flags=0
        for bit in range(7,-1,-1):
            if p>=len(data):break
            best=0;distance=0
            for q in reversed(positions.get(data[p:p+3],[])):
                if p-q>4096:break
                n=3
                while n<18 and p+n<len(data) and data[q+n]==data[p+n]:n+=1
                if n>best:best=n;distance=p-q
                if n==18:break
            count=best if best>=3 else 1
            if best>=3:
                flags|=1<<bit;d=distance-1
                out.extend((((best-3)<<4)|(d>>8),d&255))
            else:out.append(data[p])
            for q in range(p,p+count):positions.setdefault(data[q:q+3],[]).append(q)
            p+=count
        out[flagpos]=flags
    return bytes(out)

def decompress(data):
    size=int.from_bytes(data[1:4],'little');result=bytearray();p=4
    while len(result)<size:
        flags=data[p];p+=1
        for bit in range(7,-1,-1):
            if flags&(1<<bit):
                a,b=data[p:p+2];p+=2;distance=((a&15)<<8|b)+1
                for _ in range(min((a>>4)+3,size-len(result))):result.append(result[-distance])
            else:result.append(data[p]);p+=1
            if len(result)==size:break
    return bytes(result)
