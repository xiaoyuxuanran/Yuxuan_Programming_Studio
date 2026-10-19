"""Classroom TCP peer; simulated values only, no GPIO or Bluetooth hardware."""
import argparse
import socketserver
import time

class Protocol:
    def __init__(self, version):
        self.version=version
        self.led=self.pwm=0
        self.last=0
        self.command=self.reply=''

    def v1(self,line):
        if line=='PING':return 'PONG'
        if line=='GET':return 'STATE,{},{},2048,1'.format(self.led,self.pwm)
        parts=line.split(',')
        if len(parts)!=2 or parts[0] not in ('LED','PWM'):return 'ERR,BAD_CMD'
        command,value=parts
        if not value or not value.isascii() or not value.isdecimal() or int(value)>(1 if command=='LED' else 255):return 'ERR,BAD_VALUE'
        if command=='LED':self.led=int(value);self.pwm=255 if self.led else 0
        else:self.pwm=int(value);self.led=int(self.pwm>0)
        return 'OK,{},{}'.format(command,int(value))

    def process(self,line):
        if self.version==1:return self.v1(line)
        parts=line.split('|')
        if len(parts)!=2:return '0|ERR,BAD_SEQ'
        sequence,command=parts
        if not sequence or not sequence.isascii() or not sequence.isdecimal() or not 1<=int(sequence)<=2147483647:return '0|ERR,BAD_SEQ'
        seq=int(sequence)
        if seq==self.last:return '{}|{}'.format(seq,self.reply if command==self.command else 'ERR,SEQ_REUSE')
        if seq<self.last:return '{}|ERR,STALE_SEQ'.format(seq)
        self.last,self.command,self.reply=seq,command,self.v1(command)
        return '{}|{}'.format(seq,self.reply)

class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        protocol=Protocol(self.server.version)
        pending=bytearray();overflow=False;previous=None
        while True:
            data=self.request.recv(4096)
            if not data:return
            for char in data:
                if char==10:
                    if not pending and not overflow:continue
                    if overflow:reply='0|ERR,TOO_LONG' if protocol.version==2 else 'ERR,TOO_LONG'
                    else:
                        try:reply=protocol.process(bytes(pending).rstrip(b'\r').decode('ascii'))
                        except UnicodeDecodeError:reply='0|ERR,BAD_CMD' if protocol.version==2 else 'ERR,BAD_CMD'
                    pending.clear();overflow=False
                    print('{} -> {}'.format(self.client_address[0],reply),flush=True)
                    scenario=self.server.scenario
                    if scenario=='close':return
                    packet=(reply+'\n').encode('ascii')
                    if scenario=='delay':time.sleep(1.8)
                    if scenario=='old' and previous is not None:self.request.sendall(previous)
                    if scenario=='combined':self.request.sendall(packet+packet)
                    elif scenario=='split':
                        cut=max(1,len(packet)//2)
                        self.request.sendall(packet[:cut]);time.sleep(.2);self.request.sendall(packet[cut:])
                    else:self.request.sendall(packet)
                    previous=packet
                elif not overflow:
                    if len(pending)>=64 and not(len(pending)==64 and char==13):overflow=True;pending.clear()
                    else:pending.append(char)

class Server(socketserver.TCPServer):
    allow_reuse_address=True

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host',default='127.0.0.1');ap.add_argument('--port',type=int,default=9000)
    ap.add_argument('--version',type=int,choices=(1,2),default=2)
    ap.add_argument('--scenario',choices=('normal','split','combined','delay','old','close'),default='normal')
    a=ap.parse_args()
    with Server((a.host,a.port),Handler) as server:
        server.version,server.scenario=a.version,a.scenario
        print('SIMULATION ONLY: {}:{}, v{}, {}; ADC=2048, button=1 are fixed mock values.'.format(a.host,a.port,a.version,a.scenario),flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass

if __name__=='__main__':main()
