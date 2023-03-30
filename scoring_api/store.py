import socket


class RedisStorage:
    def __init__(self, host='localhost', port=6379):
        self.host = host
        self.port = port
        self.rs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.rs.connect((self.host, self.port))

    def close_connection(self):
        self.rs.close()

    def get(self, a):
        # cmd = 'GET ttt\r\n'.encode()
        self.rs.sendall(f'GET {a}\r\n'.encode())
        response = self.rs.recv(1024)
        return response.decode()


    def cache_get(self, a):
        self.rs.sendall(f'GET {a}\r\n'.encode())
        response = self.rs.recv(1024)
        return response.decode()


    def cache_set(self, key: str, value: float, ex: int):
        self.rs.sendall(f'SET {key} {value} EX {ex}\r\n'.encode())
        response = self.rs.recv(1024)
        return response.decode()


if __name__ == "__main__":
    rs = RedisStorage()
    rs.connect()
    print(rs.get('ttt'))
    print(rs.cache_set('my', 345.0, 15))
    print(rs.cache_get('my'))
    rs.close_connection()
