#!/usr/bin/env python

'''
https://gist.github.com/mafayaz/faf938a896357c3a4c9d6da27edcff08
https://dwightreid.com/blog/2017/05/22/create-web-service-python-rest-api/

for multi-thread
https://stackoverflow.com/a/14089457/335181
http://pymotw.com/2/BaseHTTPServer/index.html#module-BaseHTTPServer
https://stackoverflow.com/questions/46210672/python-2-7-streaming-http-server-supporting-multiple-connections-on-one-port
'''

import os
import SimpleHTTPServer
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn, ForkingMixIn
import threading
import time
import socket
import re
import urlparse
from dmx.utillib.utils import run_command
import json


PORT = 9090

class CustomHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if re.search('/api/listproject/?', self.path):
            exitcode, stdout, stderr = run_command('dmx report list -p ')
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write("<pre>" + stdout.replace('\n', '<br>') + "</pre>") 
            return
        elif re.search('/api/arcdataquota/*', self.path):
            userid = self.path.split('/')[-1]
            exitcode, stdout, stderr = run_command('arc-data-quota -u {}'.format(userid))
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write("<pre>" + stdout.replace('\n', '<br>') + "</pre>")
            return
        elif re.search('/api/test/?', self.path):
            print '{}: 111 ...'.format(os.getpid())
            time.sleep(5)
            print '{}: 222...'.format(os.getpid())
            time.sleep(5)
            print '{}: 333...'.format(os.getpid())
            time.sleep(5)

            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            self.wfile.write('{"name": "Lionel", "age": 16, "sex": "male"}')
            return

        else:
            #serve files, and directory listings by following self.path from
            #current working directory
            #SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
            #BaseHTTPRequestHandler.do_GET(self)
            parsed_path = urlparse.urlparse(self.path)
            message_parts = [
                    'CLIENT VALUES:',
                    'client_address=%s (%s)' % (self.client_address,
                                                self.address_string()),
                    'command=%s' % self.command,
                    'path=%s' % self.path,
                    'real path=%s' % parsed_path.path,
                    'query=%s' % parsed_path.query,
                    'request_version=%s' % self.request_version,
                    '',
                    'SERVER VALUES:',
                    'server_version=%s' % self.server_version,
                    'sys_version=%s' % self.sys_version,
                    'protocol_version=%s' % self.protocol_version,
                    '',
                    'HEADERS RECEIVED:',
                    ]
            for name, value in sorted(self.headers.items()):
                message_parts.append('%s=%s' % (name, value.rstrip()))
            message_parts.append('')
            message = '\r\n'.join(message_parts)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(message)
            return

#class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
class ThreadedHTTPServer(ForkingMixIn, HTTPServer):
    '''Handle requests in a separate thread.'''

if __name__ == '__main__':
    #httpd = SocketServer.ThreadingTCPServer(('', PORT),CustomHandler)
    httpd = ThreadedHTTPServer(('', PORT), CustomHandler)
    print "serving at port", PORT
    httpd.serve_forever()
