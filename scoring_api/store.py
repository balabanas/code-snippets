import json
import socket
import time
from typing import Union


class RedisStorage:
    """Simple wrap to work with Redis without installing `redis` or alike libraries.
    Allows to set up connection, select database, put and get values and lists.
    The connection to the databas is established via socket.
    There are important defaults: localhost as host, 6379 as port and 0 as db index."""
    def __init__(self, host='localhost', port=6379):
        """Crates socket and initialise `host` and `port` attributes. Pass them to __init__ if need
        to override defaults."""
        self.host = host
        self.port = port
        self.rs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def switch_db(self, db_num: int):
        """Activates the database to work with by index `db_num`"""
        cli_cmd = f"SELECT {db_num}\r\n"
        self.rs.sendall(cli_cmd.encode('utf-8'))
        response = self.rs.recv(1024)
        if not response == b'+OK\r\n':
            raise TypeError('Switching database failed!')

    def connect(self, db_num: int = 0) -> None:  # let 0 be the prod
        """Sets up connection to Redis and activates the db by index (default is 0)"""
        retry_count = 0
        max_retry_count = 3
        retry_interval = 1
        while True:
            try:
                self.rs.connect((self.host, self.port))
                self.switch_db(db_num)
                break
            except ConnectionRefusedError as e:
                retry_count += 1
                if retry_count > max_retry_count:
                    print('Maximum connection retry count exceeded. Not connected to Redis.')
                    raise e
                time.sleep(retry_interval * retry_count)
                print(f"Connection to Redis failed. Retrying to connect... {retry_count}")


    def close_connection(self):
        """Closes the socket"""
        self.rs.close()

    @staticmethod
    def _parse_redis_response(response):
        """Takes byte-response from Redis and parse it either to return
        - None if response is empty
        - list if response returns list
        - value if returns specific value
        The returning values are decoded to strings"""
        if response in (b'$-1\r\n', b'*0\r\n'):  # meaning (nil) or (empty array)
            return None
        if response[0] == 42:  # meaning b'*'
            list_elements = response.split(b'\r\n')
            list_elements = list_elements[2:]
            list_elements = list_elements[::2]  # takes every second element, thus ignoring len components of a response
            return [el.decode('utf-8') for el in list_elements]
        elif response[0] == 36:  # meaning b'$', i.e. single value has been returned
            list_elements = response.split(b'\r\n')
            return list_elements[1].decode()

    def get(self, key: str) -> Union[str, None]:
        """Returns list value by key"""
        cli_cmd = f'LRANGE {key} 0 -1\r\n'
        self.rs.sendall(cli_cmd.encode('utf-8'))
        response = self.rs.recv(1024)
        response = self._parse_redis_response(response)
        # print('json dumps: ', json.dumps(response))
        return json.dumps(response)

    def cache_get(self, key: str) -> Union[str, None]:
        """Returns cached value by key"""
        cli_cmd = f'GET {key}\r\n'
        self.rs.sendall(cli_cmd.encode())
        response = self.rs.recv(1024)
        response = self._parse_redis_response(response)
        return response

    def cache_set(self, key: str, value: float, ex: int = 0) -> None:
        """Sets key-value pair with optional expire period"""
        self.rs.sendall(f'SET {key} {value} EX {ex}\r\n'.encode())
        response = self.rs.recv(1024)
        if not response == b'+OK\r\n':
            raise TypeError('Storing value has been failed!')

    def rpush(self, key: str, value: list) -> None:
        """Sets key-value pair, where value is a list."""
        cli_cmd = f'RPUSH {key} {" ".join(value)}\r\n'
        self.rs.sendall(cli_cmd.encode())
        response = self.rs.recv(1024)
        if not isinstance(int(response[1:-2]), int):
            raise TypeError('Storing value has been failed!')  # expects n of els in list


if __name__ == "__main__":
    pass
    # rs = RedisStorage()
    # rs.connect()
    # print(rs.get('ttt'))
    # print(rs.cache_set('my', 345.0, 15))
    # print(rs.cache_get('my'))
    # rs.close_connection()
