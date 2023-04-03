import json
import logging
import socket
import time
from typing import Union


class RedisStorage:
    rs = None
    """Simple wrap to work with Redis without installing `redis` or alike libraries.
    Allows to set up connection, select database, put and get values and lists.
    The connection to the databas is established via socket.
    There are important defaults: localhost as host, 6379 as port and 0 as db index."""

    def __init__(self, host='localhost', port=6379, db_idx: int = 0):
        """Crates socket and initialise `host` and `port` attributes. Pass them to __init__ if need
        to override defaults."""
        self.host = host
        self.port = port
        self.db_idx = db_idx

    def switch_db(self, db_num: int):
        """Activates the database to work with by index `db_num`"""
        cli_cmd = f"SELECT {db_num}\r\n"
        self.rs.sendall(cli_cmd.encode('utf-8'))
        response = self.rs.recv(1024)
        if not response == b'+OK\r\n':
            msg = 'Switching database failed!'
            logging.error(msg)
            raise TypeError(msg)

    def connect(self) -> None:  # let 0 be the prod
        """Sets up connection to Redis and activates the db by index (default is 0)"""
        retry_count = 0
        max_retry_count = 1
        retry_interval = 0.5
        while True:
            try:
                if self.rs:
                    self.close_connection()
                self.rs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.rs.settimeout(1)
                self.rs.connect((self.host, self.port))
                self.switch_db(self.db_idx)
                break
            except TimeoutError as e:
                retry_count += 1
                if retry_count > max_retry_count:
                    logging.error('Maximum connection retry count exceeded. Not connected to Redis.')
                    raise e
                time.sleep(retry_interval * retry_count)
                logging.info(f"Connection to Redis failed. Retrying to connect... {retry_count}")

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
        try:
            self.connect()
            cli_cmd = f'LRANGE {key} 0 -1\r\n'
            self.rs.sendall(cli_cmd.encode('utf-8'))
            response = self.rs.recv(1024)
            self.close_connection()
            response = self._parse_redis_response(response)
            return json.dumps(response)
        except TimeoutError:
            logging.error("Store unavailable! Return nothing!")
            return None

    def cache_set(self, key: str, value: float, ex: int = 0) -> None:
        """Sets key-value pair with optional expire period"""
        try:
            self.connect()
            self.rs.sendall(f'SET {key} {value} EX {ex}\r\n'.encode())
            response = self.rs.recv(1024)
            self.close_connection()
            if not response == b'+OK\r\n':
                msg = f"Caching value has been failed! Response: {response}"
                logging.error(msg)
                raise TypeError(msg)
        except TimeoutError:  # cache is not available
            logging.error("Timeout: cache is not ready to save to")  # not a problem, just log it and go

    def cache_get(self, key: str) -> Union[str, None]:
        """Returns cached value by key"""
        try:
            self.connect()
            cli_cmd = f'GET {key}\r\n'
            self.rs.sendall(cli_cmd.encode())
            response = self.rs.recv(1024)
            self.close_connection()
            response = self._parse_redis_response(response)
        except TimeoutError:  # cache is not available
            logging.error("Timeout: cache is not ready to read from")  # not a problem, just log it and go
            response = None  # not a problem, return None
        return response

    def rpush(self, key: str, value: list) -> None:
        """Sets key-value pair, where value is a list."""
        """"Assumes that .connect() is made before. Excepts the connection to be closed after function call"""
        try:
            cli_cmd = f'RPUSH {key} {" ".join(value)}\r\n'
            self.rs.sendall(cli_cmd.encode())
            response = self.rs.recv(1024)
            if not isinstance(int(response[1:-2]), int):
                msg = "Storing value has been failed!"
                logging.error(msg)
                raise TypeError(msg)  # expects n of els in list
        except TimeoutError:
            msg = "Timeout: unable to store with RPUSH"
            logging.error(msg)
            raise TimeoutError(msg)


if __name__ == "__main__":
    store = RedisStorage()
    print(store.get('ttt'))
    print(store.cache_set('my', 345.0, 15))
    print(store.cache_get('my'))
