# Automate SSH, sudo su, and kubectl commands as described in your manual steps.
# Requires: paramiko (install with `pip install paramiko`)
import paramiko
import getpass
import time
import json
import re

HOST = "vms1-tb163.versa-test.net"
USER = "admin"

def prompt_password(prompt_text, default="THS!5V3r5@vmsP@55"):
    pw = getpass.getpass(f"{prompt_text} (default: {default}): ")
    return pw if pw else default

def parse_kubectl_output(output):
    """Parse kubectl get svc -A output and extract tenant information"""
    tenant_services = {}
    lines = output.strip().split('\n')
    
    # Skip header line and empty lines
    for line in lines:
        line = line.strip()
        if not line or line.startswith('NAMESPACE') or line.startswith('kubectl'):
            continue
        
        # Split by whitespace and get first two columns
        parts = line.split()
        if len(parts) >= 2:
            namespace = parts[0]  # First column is tenant (namespace)
            service = parts[1]    # Second column is service name
            
            # Skip system namespaces (optional filtering)
            if namespace in ['kube-system', 'kube-public', 'kube-node-lease', 'default']:
                continue
            
            if namespace not in tenant_services:
                tenant_services[namespace] = []
            
            if service not in tenant_services[namespace]:
                tenant_services[namespace].append(service)
    
    return tenant_services

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

    # Set alias for kubectl
    shell.send("alias k=kubectl\n")
    time.sleep(0.5)
    shell.recv(10000).decode()  # Clear the response

    # Step 2: run kubectl get svc -A
    shell.send("kubectl get svc -A\n")
    time.sleep(2)
    kubectl_output = shell.recv(65535).decode()
    print("kubectl get svc -A output:")
    print(kubectl_output)
    
    # Step 3: Ask user if they want to see tenant list
    show_tenants = input("\nDo you want to see the list of tenants and their services? (y/n): ").lower().strip()
    
    if show_tenants in ['y', 'yes']:
        print("\nExtracting tenant information from kubectl output...")
        tenant_services = parse_kubectl_output(kubectl_output)
        
        if tenant_services:
            print("\n" + "="*50)
            print("TENANT INFORMATION")
            print("="*50)
            
            for tenant, services in tenant_services.items():
                print(f"\nTenant: {tenant}")
                print(f"Services: {', '.join(services)}")
            
            print("\n" + "="*50)
            print("JSON OBJECT - TENANT SERVICES MAPPING")
            print("="*50)
            tenant_json = json.dumps(tenant_services, indent=2)
            print(tenant_json)
            
            # Optionally save to file
            save_file = input("\nDo you want to save this information to a file? (y/n): ").lower().strip()
            if save_file in ['y', 'yes']:
                filename = f"tenant_services_{time.strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(tenant_services, f, indent=2)
                print(f"Tenant information saved to: {filename}")
        else:
            print("No tenant information found in the kubectl output.")

    shell.send("exit\n")
    time.sleep(0.5)
    ssh.close()

if __name__ == "__main__":
    main()