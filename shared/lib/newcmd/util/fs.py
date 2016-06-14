import os, hashlib

file_size = os.path.getsize
exists = os.path.exists

def checksum(file, algo="md5"):
    hash = hashlib.new(algo)
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()