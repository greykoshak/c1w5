# Предположим, необходимо собирать метрики о работе операционной системы: cpu (загрузка процессора),
# memory usage (потребление памяти), disk usage (потребление места на жестком диске), network usage
# (статистика сетевых интерфейсов) и т.д. Это понадобится для контроля загрузки серверов и прогноза
# по расширению парка железа компании - проще говоря для мониторинга.
# Пусть у нас имеется в наличии два сервера palm и eardrum. Мы будем получать загрузку центрального
# процессора на сервере и отправлять метрику с названием имя_сервера.cpu

# client -> server: put palm.cpu 10.6 1501864247\n
# server -> client: ok\n\n
# client -> server: put eardrum.cpu 15.3 1501864259\n
# server -> client: ok\n\n

# Чтобы отправить метрику на сервер, вы отправляете в TCP-соединение строку вида:
# put palm.cpu 10.6 1501864247\n
# Ключевое слово put означает команду отправки метрики. За ней через пробел следует название (имя) самой метрики, например palm.cpu, далее опять через пробел значение метрики, и через еще один пробел временная метка unix timestamp. Таким образом, во время 1501864247 значение метрики palm.cpu было равно 10.6. Наконец, команда заканчивается символом переноса строки \n.
# В ответ на эту команду put сервер присылает уведомление об успешном сохранении метрики в виде строки:
# ok\n\n

# Реализация клиента.
# Необходимо реализовать класс Client, в котором будет инкапсулировано соединение с сервером,
# клиентский сокет и методы для получения и отправки метрик на сервер. В конструктор класса Client
# должна передаваться адресная пара хост и порт, а также необязательный аргумент timeout
# (timeout=None по умолчанию). У класса Client должно быть 2 метода: put и get, соответствующих
# протоколу выше.
# Пример вызова клиента для отправки метрик и затем их получения:

# client = Client("127.0.0.1", 8888, timeout=15)
#
# client.put("palm.cpu", 0.5, timestamp=1150864247)
# client.put("palm.cpu", 2.0, timestamp=1150864248)
# client.put("palm.cpu", 0.5, timestamp=1150864248)
#
# client.put("eardrum.cpu", 3, timestamp=1150864250)
# client.put("eardrum.cpu", 4, timestamp=1150864251)
# client.put("eardrum.memory", 4200000)
#
# print(client.get("*"))

# Клиент получает данные в текстовом виде, метод get должен возвращать словарь с полученными ключами
# с сервера. Значением ключа в словаре является список кортежей [(timestamp, metric_value), ...],
# отсортированный по timestamp от меньшего к большему. Значение timestamp должно быть преобразовано к
# целому числу int. Значение метрики metric_value нужно преобразовать к числу с плавающей точкой
# float.
# Метод put принимает первым аргументом название метрики, вторым численное значение, третьим -
# необязательный именованный аргумент timestamp. Если пользователь вызвал метод put без аргумента
# timestamp, то клиент автоматически должен подставить текущее время в команду put -
# str(int(time.time()))
# Метод put не возвращает ничего в случае успешной отправки и выбрасывает исключение ClientError в
# случае неуспешной.
# Метод get принимает первым аргументом имя метрики, значения которой мы хотим выгрузить. Также вместо
# имени метрики можно использовать символ *, о котором говорилось в описании протокола.
# Метод get возвращает словарь с метриками (смотрите ниже пример) в случае успешного получения ответа
# от сервера и выбрасывает исключение ClientError в случае неуспешного.
# Пример возвращаемого значения при успешном вызове client.get("palm.cpu"):

# {
#   'palm.cpu': [
#     (1150864247, 0.5),
#     (1150864248, 0.5)
#   ]
# }

import socket
import time


class Client:
    """
    Инкапсуляция соединения с сервером, клиентский сокет и
    методы для получения и отправки метрик на сервер
    """

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = socket.create_connection((self.host, self.port), self.timeout)
        # self.sock.close()

    # Метод put не возвращает ничего в случае успешной отправки и выбрасывает исключение ClientError в случае неуспешной.
    def put(self, metric, value, timestamp=None):
        try:
            if timestamp is None:
                # timestamp = str((int(time.time())))
                timestamp = int(time.time())

            message = f'put {metric} {value} {timestamp}\n'
            self.sock.sendall(message.encode("utf-8"))

            data = self.sock.recv(1024).decode().split("\n")  # Server answer

            if not data[0] == "ok":
                raise ClientError

        except socket.timeout:
            raise ClientError

    """
    Метод get принимает первым аргументом имя метрики, значения которой мы хотим выгрузить. 
    Вместо имени метрики можно использовать символ *
    """

    def get(self, metric=None):

        if metric is None:
            raise ClientError

        try:
            message = f'get {metric}\n'
            self.sock.sendall(message.encode("utf-8"))

            data = ""
            while True:
                data += self.sock.recv(1024).decode()  # Server answer
                if "\n\n" in data:
                    break

            if data.split()[0] == 'ok':
                answer = (data[3::]).split()  # Получился список
                return self.get_dict(answer)
            else:
                return dict()

        except socket.timeout:
            raise ClientError

    def get_dict(self, data):
        ans_dict = dict()

        for i, key in enumerate(data[::3]):
            if key in ans_dict:
                ans_dict[key].append(tuple([int(float(data[i * 3 + 2])), float(data[i * 3 + 1])]))
            else:
                ans_dict.update({key: [tuple([int(float(data[i * 3 + 2])), float(data[i * 3 + 1])])]})
        return ans_dict

    def close(self):
        return self.sock.close()


# except ClientError:
class ClientError(Exception):
    pass

# def _main():
#     client = Client("127.0.0.1", 8888, timeout=15)
#
#     client.put("palm.cpu", 0.5, timestamp=1150864247)
#     client.put("palm.cpu", 2.0, timestamp=1150864248)
#     client.put("palm.cpu", 0.5, timestamp=1150864248)
#
#     client.put("eardrum.cpu", 3, timestamp=1150864250)
#     client.put("eardrum.cpu", 4, timestamp=1150864251)
#     client.put("eardrum.memory", 4200000)
#
#     print(client.get("*"))
#
#
# if __name__ == "__main__":
#     _main()
