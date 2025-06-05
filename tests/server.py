from paramiko import SSHClient
from paramiko.client import AutoAddPolicy


def check_server():
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy)

    commands = {
        "cpu": "top -bn1",
        "memory": "free -m",
        "disk": "df -h",
    }
    try:
        client.connect("localhost", port=32768, username="root", password="root")
        for key, cmd in commands.items():
            stdin, stdout, stderr = client.exec_command(cmd)
            res = stdout.read().decode('utf-8')
            print(key)
            print(res)
    except Exception as e:
        print(e)


check_server()
