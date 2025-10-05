# Automate SSH, sudo su, and kubectl commands as described in your manual steps.
# Requires: paramiko (install with `pip install paramiko`)
import paramiko
import getpass
import time

HOST = "vms1-tb163.versa-test.net"
USER = "admin"

def prompt_password(prompt_text, default="THS!5V3r5@vmsP@55"):
    pw = getpass.getpass(f"{prompt_text} (default: {default}): ")
    return pw if pw else default

def main():
    ssh_password = prompt_password(f"Enter SSH password for {USER}@{HOST}")
    sudo_password = prompt_password(f"Enter sudo password for {USER}")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=ssh_password, look_for_keys=False)

    shell = ssh.invoke_shell()
    time.sleep(1)
    shell.recv(10000)  # Clear banner

    # Step 1: sudo su
    shell.send("sudo su\n")
    buff = ""
    while not buff.strip().endswith("password for admin:"):
        resp = shell.recv(1000).decode()
        buff += resp
        if "password for" in buff:
            break
        time.sleep(0.2)
    shell.send(sudo_password + "\n")
    time.sleep(1.5)
    output = shell.recv(10000).decode()
    print(output)

    # Step 2: run kubectl get svc -A
    shell.send("kubectl get svc -A\n")
    time.sleep(2)
    output = shell.recv(65535).decode()
    print(output)

    shell.send("exit\n")
    time.sleep(0.5)
    ssh.close()

if __name__ == "__main__":
    main()