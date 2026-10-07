"""Read-only check of the game currently loaded in the user's mGBA."""
import json
import socket

requests=[('get_info',{}),
          ('read_range',{'address':'0x09001000','length':32}),
          ('read_range',{'address':'0x09004000','length':12}),
          ('read_range',{'address':'0x09004400','length':12}),
          ('read_range',{'address':'0x0203FF00','length':16}),
          ('read_range',{'address':'0x0300331C','length':8}),
          ('read32',{'address':'0x03007710'})]
try:
    with socket.create_connection(('127.0.0.1',8765),timeout=3) as connection:
        connection.settimeout(3)
        stream=connection.makefile('r',encoding='utf-8')
        for n,(command,params) in enumerate(requests,1):
            connection.sendall((json.dumps({'id':n,'command':command,'params':params})+'\n').encode())
            reply=json.loads(stream.readline())
            print(json.dumps({'command':command,'params':params,'reply':reply}),flush=True)
except (OSError,ValueError) as error:
    print(json.dumps({'bridge_unavailable':str(error)}))
