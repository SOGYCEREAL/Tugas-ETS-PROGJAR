import json
import logging
import shlex

from file_interface import FileInterface

"""
* class FileProtocol bertugas untuk memproses 
data yang masuk, dan menerjemahkannya apakah sesuai dengan
protokol/aturan yang dibuat

* data yang masuk dari client adalah dalam bentuk bytes yang 
pada akhirnya akan diproses dalam bentuk string

* class FileProtocol akan memproses data yang masuk dalam bentuk
string
"""

class FileProtocol:
    def __init__(self):
        self.file = FileInterface()
    def proses_string(self, string_datamasuk=''):
        logging.warning(f"string diproses: {string_datamasuk}")
        try:
            # upload via JSON
            if string_datamasuk.strip().startswith('{'):
                data = json.loads(string_datamasuk)
                if data.get("command") == "upload":
                    return json.dumps(self.file.upload([data["filename"], data["filedata"]]))
            else:
                # command CLI biasa seperti LIST, GET, DELETE
                c = shlex.split(string_datamasuk)
                c_request = c[0].strip().lower()
                params = c[1:]
                cl = getattr(self.file, c_request)(params)
                return json.dumps(cl)
        except Exception as e:
            logging.warning(f"Error saat memproses string: {e}")
            return json.dumps(dict(status='ERROR', data='request tidak dikenali'))


if __name__=='__main__':
    #contoh pemakaian
    fp = FileProtocol()
    print(fp.proses_string("LIST"))
    print(fp.proses_string("GET pokijan.jpg"))
