from paramiko import SSHClient
from paramiko.client import AutoAddPolicy


def check_server():
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())

    commands = {
        "cpu": "grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}'",
        "memory": "free -m | grep Mem | awk '{print $3/$2 * 100.0}'",
        "disk": "df -h / | awk 'NR==2 {print $5}' | sed 's/%//'",
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
