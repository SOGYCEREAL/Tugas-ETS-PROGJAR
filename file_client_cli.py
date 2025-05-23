import socket
import json
import base64
import logging
import os
import time
import csv
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool

FILE_SIZES_MB = {"1": 10, "2": 50, "3": 100}
CLIENT_POOLS = {"1": [1], "2": [5], "3": [50], "4": [1, 5, 50]}
SERVER_POOLS = {"1": 1, "2": 5, "3": 50}
PORT_DOWNLOAD = 6969
PORT_UPLOAD = 6970

def send_command(command_str="", port=6969):
    server_address = ('172.16.16.101', port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    try:
        if not command_str.endswith("\r\n\r\n"):
            command_str += "\r\n\r\n"
        sock.sendall(command_str.encode())
        data_received = ""
        while True:
            data = sock.recv(16384)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        return json.loads(data_received)
    except:
        return False
    finally:
        sock.close()

def perform_upload(file_path):
    try:
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            filedata = base64.b64encode(f.read()).decode()
        payload = json.dumps({
            "command": "upload",
            "filename": filename,
            "filedata": filedata
        }) + "\r\n\r\n"

        start = time.time()
        response = send_command(payload, port=PORT_UPLOAD)
        duration = time.time() - start
        size_bytes = os.path.getsize(file_path)
        success = response and response.get("status") == "OK"
        return (success, duration, size_bytes)
    except Exception as e:
        return (False, 0, 0)

def perform_download(filename):
    try:
        command = f"GET {filename}"
        start = time.time()
        response = send_command(command, port=PORT_DOWNLOAD)
        duration = time.time() - start

        if response and response.get("status") == "OK":
            data = base64.b64decode(response['data_file'])
            return (True, duration, len(data))
        else:
            return (False, 0, 0)
    except:
        return (False, 0, 0)

def stress_test(task, file_path, pool_type="thread", client_pool=1):
    results = []
    if pool_type == "thread":
        with ThreadPoolExecutor(max_workers=client_pool) as executor:
            if task == 'upload':
                futures = [executor.submit(perform_upload, file_path) for _ in range(client_pool)]
            else:
                filename = os.path.basename(file_path)
                futures = [executor.submit(perform_download, filename) for _ in range(client_pool)]
            for f in futures:
                results.append(f.result())
    else:
        pool = Pool(client_pool)
        if task == 'upload':
            results = pool.map(perform_upload, [file_path] * client_pool)
        else:
            filename = os.path.basename(file_path)
            results = pool.map(perform_download, [filename] * client_pool)
        pool.close()
        pool.join()
    return results

def init_csv(filename="stress_test_results.csv"):
    if not os.path.exists(filename):
        with open(filename, mode='w', newline='') as csv_file:
            fieldnames = ["Nomor", "Operasi", "Volume", "Jumlah client worker pool", "Jumlah server worker pool", "Waktu total per client", "Throughput per client", "Jumlah sukses", "Jumlah gagal"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

def get_existing_row_count(filename="stress_test_results.csv"):
    if not os.path.exists(filename):
        return 0
    with open(filename, 'r') as f:
        return sum(1 for line in f) - 1  # kurangi header

def append_to_csv(row, filename="stress_test_results.csv"):
    with open(filename, mode='a', newline='') as csv_file:
        fieldnames = ["Nomor", "Operasi", "Volume", "Jumlah client worker pool", "Jumlah server worker pool", "Waktu total per client", "Throughput per client", "Jumlah sukses", "Jumlah gagal"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow(row)
        print(row)

def main():
    print("""
    ===============================
    File Server Stress Tester
    ===============================
    """)

    print("File Size Options (MB):\n1. 10 MB\n2. 50 MB\n3. 100 MB\n4. All")
    file_choice = input("Choose file sizes (comma separated, e.g. 1,3 or 4 for all): ").split(',')

    print("\nClient Pool Sizes:\n1. 1\n2. 5\n3. 50\n4. All (1,5,50)")
    client_choice = input("Choose option (1-4): ")

    print("\nServer Pool Sizes:\n1. 1\n2. 5\n3. 50")
    server_choice = input("Choose option (1-3): ")

    sizes = FILE_SIZES_MB.values() if '4' in file_choice else [FILE_SIZES_MB[c] for c in file_choice if c in FILE_SIZES_MB]
    client_pools = CLIENT_POOLS.get(client_choice, [1])
    server_pools = SERVER_POOLS.get(server_choice, 1)

    init_csv()
    row_id = get_existing_row_count() + 1

    for size in sizes:
        file_path = f"files/test_{size}MB.bin"
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                f.write(os.urandom(size * 1024 * 1024))

        for cp in client_pools:
            for sp in [server_pools]:
                for op in ['upload', 'download']:
                    print(f"\n--- Testing {op.upper()} for {size}MB file with {cp} clients and {sp} server workers ---")
                    pool_type = "thread" if op == 'upload' else "process"
                    results = stress_test(op, file_path, pool_type=pool_type, client_pool=cp)
                    success = sum(1 for r in results if r[0])
                    failed = len(results) - success
                    total_time = sum(r[1] for r in results if r[0]) / max(success, 1)
                    throughput = sum(r[2] for r in results if r[0]) / max(total_time * success, 1)
                    row = {
                        "Nomor": row_id,
                        "Operasi": op,
                        "Volume": f"{size}MB",
                        "Jumlah client worker pool": cp,
                        "Jumlah server worker pool": sp,
                        "Waktu total per client": f"{total_time:.2f}",
                        "Throughput per client": f"{throughput:.2f}",
                        "Jumlah sukses": success,
                        "Jumlah gagal": failed
                    }
                    append_to_csv(row)
                    row_id += 1

if __name__ == '__main__':
    main()
