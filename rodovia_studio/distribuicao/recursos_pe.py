"""Recursos Win32 em build Mono: preserva VERSIONINFO e embute manifesto asInvoker."""
import struct

def version_resource(data):
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if data[:2]!=b'MZ' or data[pe:pe+4]!=b'PE\0\0':raise ValueError('Executável PE inválido.')
    sections=struct.unpack_from('<H',data,pe+6)[0];size=struct.unpack_from('<H',data,pe+20)[0];optional=pe+24
    directory=optional+(112 if struct.unpack_from('<H',data,optional)[0]==0x20b else 96)
    resource_rva=struct.unpack_from('<I',data,directory+16)[0]
    def offset(rva):
        for i in range(sections):
            pos=optional+size+40*i;virtual_size,virtual,raw_size,raw=struct.unpack_from('<IIII',data,pos+8)
            if virtual<=rva<virtual+max(virtual_size,raw_size):return raw+rva-virtual
        raise ValueError('RVA fora das seções PE.')
    base=offset(resource_rva)
    def entries(position):
        named,ids=struct.unpack_from('<HH',data,position+12)
        return [struct.unpack_from('<II',data,position+16+8*i) for i in range(named+ids)]
    type_entry=next(value for key,value in entries(base) if key==16)
    identifier=entries(base+(type_entry&0x7fffffff))[0][1]
    language,entry=entries(base+(identifier&0x7fffffff))[0]
    rva,length=struct.unpack_from('<II',data,base+(entry&0x7fffffff));start=offset(rva)
    return data[start:start+length],language

def res_entry(kind,name,language,data):
    header=struct.pack('<IIHHHHIHHII',len(data),32,0xffff,kind,0xffff,name,0,0x1030,language,0,0)
    return header+data+b'\0'*((-len(data))%4)

def resources(binary,manifest):
    version,language=version_resource(binary)
    null=struct.pack('<IIHHHHIHHII',0,32,0xffff,0,0xffff,0,0,0,0,0,0)
    return null+res_entry(16,1,language,version)+res_entry(24,1,0x409,manifest)
