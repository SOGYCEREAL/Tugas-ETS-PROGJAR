from socket import *
import socket
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from file_protocol import FileProtocol

fp = FileProtocol()

def handle_client(connection, address):
    try:
        data_received = ""
        while True:
            data = connection.recv(1024 * 1024)
            if not data:
                break
            data_received += data.decode()
            if "\r\n\r\n" in data_received:
                break

        data_received = data_received.replace("\r\n\r\n", "")
        hasil = fp.proses_string(data_received)
        hasil = hasil + "\r\n\r\n"
        connection.sendall(hasil.encode())

    except Exception as e:
        logging.warning(f"Exception: {e}")
    finally:
        connection.close()

class Server:
    def __init__(self, ipaddress='0.0.0.0', port=7777, max_workers=10):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(100)

        while True:
            connection, client_address = self.my_socket.accept()
            logging.warning(f"connection from {client_address}")
            self.executor.submit(handle_client, connection, client_address)

def main():
    svr = Server(ipaddress='0.0.0.0', port=7777, max_workers=50)
    svr.run()

if __name__ == "__main__":
    main()
