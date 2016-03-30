import socket

def get_public_ip_address():
	_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	_socket.connect(("8.8.8.8", 80))
	result = _socket.getsockname()[0]
	_socket.close()

	return result