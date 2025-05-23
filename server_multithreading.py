from socket import *
import socket
import logging
from threading import Thread
from file_protocol import FileProtocol

fp = FileProtocol()

class Server:
    def __init__(self, ipaddress='0.0.0.0', port=6970):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def handle_client(self, connection, address):
        try:
            data_received = ""
            while True:
                data = connection.recv(16384)
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

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(5)

        while True:
            connection, client_address = self.my_socket.accept()
            logging.warning(f"connection from {client_address}")
            t = Thread(target=self.handle_client, args=(connection, client_address))
            t.start()

def main():
    svr = Server(ipaddress='0.0.0.0', port=6970)
    svr.run()

if __name__ == "__main__":
    main()
