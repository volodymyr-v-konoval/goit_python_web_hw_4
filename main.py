import datetime
import json
import logging
import mimetypes
import pathlib
import socket
import urllib.parse

from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread


BUFFER_SIZE = 1024
HTTP_HOST = '0.0.0.0'
HTTP_PORT = 3000
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000

class HttpHandler(BaseHTTPRequestHandler):
    '''The main class for managing web app.'''

    def do_GET(self):
        '''The function parses input from browser and returns the web page.'''
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message.html':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    
    def do_POST(self):
        '''The function posts data.'''

        data = self.rfile.read(int(self.headers['Content-Length']))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


    def send_html_file(self, filename, status=200):
        '''The function sends html file from server to browser.'''
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


    def render_template(self, filename, status_code=200):
        '''The function writes information to the file.'''
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()

        with open('storage/data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

     
    def send_static(self):
        '''The function sends static files to the browser.'''

        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    
def save_data_from_form(data):
    '''The function parses data from the web form and sends it to the file.'''

    parse_data = urllib.parse.unquote_plus(data.decode())
    try:
        parse_dict = {key: value for key, value in 
                      [el.split('=') for el in parse_data.split('&')]}
        finall_data = {datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S.%f') : parse_dict}
        with open('storage/data.json', 'a', encoding='utf-8') as file:
            json.dump(finall_data, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)


def run_socket_server(host, port):
    '''This runs a socket server.'''

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info('Starting socket server')
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f'Socket received {address}: {msg}')
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()


def run_http_server(host, port):
    '''This runs a http server.'''
    
    address = (host, port)
    http_server = HTTPServer(address, HttpHandler)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(threadName)s %(message)s')
    
    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, 
                           args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()


