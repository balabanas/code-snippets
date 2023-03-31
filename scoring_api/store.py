import json
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

    @staticmethod
    def _parse_redis_response(response):
        if response in (b'$-1\r\n', b'*0\r\n'):  # meaning (nil) or (empty array)
            return None
        if response[0] == 42:  # meaning b'*'
            list_elements = response.split(b'\r\n')
            list_elements = list_elements[2:]
            list_elements = list_elements[::2]  # takes every second element, thus ignoring len components of a response
            return [el.decode('utf-8') for el in list_elements]
        elif response[0] == 36:  # meaning b'$'
            list_elements = response.split(b'\r\n')
            return list_elements[1].decode()

    def get(self, a):
        # cmd = 'GET ttt\r\n'.encode()
        self.rs.sendall(f'LRANGE {a} 0 -1\r\n'.encode())
        response = self.rs.recv(1024)
        response = self._parse_redis_response(response)
        print('json dumps: ', json.dumps(response))
        return json.dumps(response)

    def cache_get(self, a):
        self.rs.sendall(f'GET {a}\r\n'.encode())
        response = self.rs.recv(1024)
        response = self._parse_redis_response(response)
        return response

    def cache_set(self, key: str, value: float, ex: int) -> None:
        self.rs.sendall(f'SET {key} {value} EX {ex}\r\n'.encode())
        response = self.rs.recv(1024)
        if not response == b'+OK\r\n':
            raise TypeError('Storing value has been failed!')

    def rpush(self, key: str, value: list) -> None:
        self.rs.sendall(f'RPUSH {key} {" ".join(value)}\r\n'.encode())
        response = self.rs.recv(1024)
        if not isinstance(int(response[1:-2]), int):
            raise TypeError('Storing value has been failed!')  # expects n of els in list


if __name__ == "__main__":
    rs = RedisStorage()
    rs.connect()
    print(rs.get('ttt'))
    print(rs.cache_set('my', 345.0, 15))
    print(rs.cache_get('my'))
    rs.close_connection()
