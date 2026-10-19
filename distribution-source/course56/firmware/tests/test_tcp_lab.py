import contextlib
import socket
import sys
import threading
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tcp_lab_server import Handler,Server,Protocol

@contextlib.contextmanager
def peer(scenario='normal',version=2):
    server=Server(('127.0.0.1',0),Handler)
    server.version,server.scenario=version,scenario
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with socket.create_connection(server.server_address,timeout=4) as sock:yield sock
    finally:server.shutdown();server.server_close();thread.join(3)

class LabTests(unittest.TestCase):
    def test_sequence_contract_and_ranges(self):
        p=Protocol(2)
        cases=[('1|LED,1','1|OK,LED,1'),('1|LED,1','1|OK,LED,1'),('1|LED,0','1|ERR,SEQ_REUSE'),('2|PWM,128','2|OK,PWM,128'),('1|LED,1','1|ERR,STALE_SEQ'),('3|GET','3|STATE,1,128,2048,1'),('4|PWM,256','4|ERR,BAD_VALUE'),('0|GET','0|ERR,BAD_SEQ'),('2147483648|GET','0|ERR,BAD_SEQ'),('5|PWM,-1','5|ERR,BAD_VALUE')]
        for request,expected in cases:
            with self.subTest(request=request):self.assertEqual(p.process(request),expected)

    def test_fragmented_and_combined_requests(self):
        with peer() as sock:
            stream=sock.makefile('rb')
            sock.sendall(b'1|LE');sock.sendall(b'D,1\n2|GET\r\n')
            self.assertEqual(stream.readline(),b'1|OK,LED,1\n')
            self.assertEqual(stream.readline(),b'2|STATE,1,255,2048,1\n')
            sock.sendall(b'A'*65+b'\n3|GET\n')
            self.assertEqual(stream.readline(),b'0|ERR,TOO_LONG\n')
            self.assertEqual(stream.readline(),b'3|STATE,1,255,2048,1\n')
            stream.close()

    def test_reply_scenarios(self):
        for scenario in ('split','combined','old','delay','close'):
            with self.subTest(scenario=scenario),peer(scenario) as sock:
                stream=sock.makefile('rb');sock.sendall(b'1|LED,1\n')
                if scenario=='close':self.assertEqual(stream.readline(),b'')
                else:
                    self.assertEqual(stream.readline(),b'1|OK,LED,1\n')
                    if scenario=='combined':self.assertEqual(stream.readline(),b'1|OK,LED,1\n')
                    if scenario=='old':
                        sock.sendall(b'2|LED,0\n')
                        self.assertEqual(stream.readline(),b'1|OK,LED,1\n')
                        self.assertEqual(stream.readline(),b'2|OK,LED,0\n')
                stream.close()

if __name__=='__main__':unittest.main(verbosity=2)
