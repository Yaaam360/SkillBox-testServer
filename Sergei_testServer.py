#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from typing import Optional

class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode(encoding="utf8", errors="replace")

        if self.login is not None:
            if (decoded != "\r\n"):
                self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r", "")
                login_used = self.check_login(login)
                if (login_used == True):
                    self.transport.write(f"Логин {login} занят, попробуйте другой\n".encode())
                    self.transport.close()
                else:
                    self.login = login
                    self.transport.write(f"Привет, {self.login}!\n\r".encode())
                    self.send_history()
            else:
                self.transport.write('Неверный логин!\n\r'.encode())


    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exeption):
        self.server.clients.remove(self)
        print("Клиент вышел")


    def send_message(self, content: str):
        message = f"{self.login}: {content}\n\r"
        self.server.histories.append(message)
        for user in self.server.clients:
            user.transport.write(message.encode())

    def check_login(self, login: str):
        for user in self.server.clients:
            if login == user.login:
                return True
        return False

    def send_history(self):
        history_count = len(self.server.histories)
        if history_count <= 10:
            i=-(history_count)
        else:
            i = -10
        while i<0:
            self.transport.write(f"{self.server.histories[i]}".encode())
            i = i + 1

class Server:
    clients: list
    histories: list

    def __init__(self):
        self.clients = []
        self.histories = []

    def build_protocol(self):
        return ServerProtocol(self)


    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
           self.build_protocol,
            '127.0.0.1',
            9999
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер установлен вручную!")

