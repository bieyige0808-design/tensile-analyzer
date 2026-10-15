"""Check the actual PE icon resources, not just the runtime Tk icon."""
import struct
import sys
from pathlib import Path
import pefile

source=Path('assets/tensile-analyzer.ico').read_bytes()
count=struct.unpack_from('<H',source,4)[0]
expected=[]
for i in range(count):
    length,offset=struct.unpack_from('<II',source,6+i*16+8)
    expected.append(source[offset:offset+length])
pe=pefile.PE(sys.argv[1])
icons=[];groups=[]
for resource in pe.DIRECTORY_ENTRY_RESOURCE.entries:
    if resource.id==3:
        for entry in resource.directory.entries:
            for lang in entry.directory.entries:
                data=lang.data.struct
                icons.append(pe.get_data(data.OffsetToData,data.Size))
    if resource.id==14: groups.extend(resource.directory.entries)
assert groups,'Executable has no icon group'
assert all(data in icons for data in expected),'Embedded icon differs from supplied ICO'
print(f'Verified {count} exact icon frames embedded in executable')
