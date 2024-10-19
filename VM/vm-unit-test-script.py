import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import subprocess
import queue
import argparse

class VMConsole(ttk.Frame):
    def __init__(self, master, vm_name):
        super().__init__(master)
        self.vm_name = vm_name
        self.create_widgets()

    def create_widgets(self):
        self.console = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=10)
        self.console.pack(expand=True, fill='both')
        self.console.config(state='disabled')

    def write(self, text):
        self.console.config(state='normal')
        self.console.insert(tk.END, text)
        self.console.see(tk.END)
        self.console.config(state='disabled')

class VMTester(threading.Thread):
    def __init__(self, vm_name, console, result_queue):
        threading.Thread.__init__(self)
        self.vm_name = vm_name
        self.console = console
        self.result_queue = result_queue

    def run(self):
        success = self.test_vm()
        self.result_queue.put((self.vm_name, success))

    def run_command(self, command):
        full_command = f"vagrant ssh {self.vm_name} -c '{command}'"
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        return process.returncode, output.decode('utf-8'), error.decode('utf-8')

    def test_vm(self):
        self.console.write(f"Testing {self.vm_name}...\n")
        
        if "firewall" in self.vm_name:
            success = self.test_firewall()
        elif "dhcp" in self.vm_name:
            success = self.test_dhcp()
        elif "dns" in self.vm_name:
            success = self.test_dns()
        elif "smtp" in self.vm_name:
            success = self.test_smtp()
        elif "nas" in self.vm_name:
            success = self.test_nas()
        elif "vpn" in self.vm_name:
            success = self.test_vpn()
        else:
            self.console.write(f"No specific test for {self.vm_name}\n")
            success = True

        return success

    def test_firewall(self):
        self.console.write("Testing firewall...\n")
        success = True

        returncode, output, error = self.run_command("sudo iptables -L")
        if returncode != 0:
            self.console.write("Error: iptables is not running\n")
            success = False

        rules_to_check = [
            ("-A INPUT -p tcp --dport 22 -j ACCEPT", "SSH allowed"),
            ("-A INPUT -p tcp --dport 80 -j ACCEPT", "HTTP allowed"),
            ("-A INPUT -p tcp --dport 443 -j ACCEPT", "HTTPS allowed"),
            ("-A INPUT -p icmp -j ACCEPT", "ICMP (ping) allowed")
        ]

        for rule, description in rules_to_check:
            returncode, output, error = self.run_command(f"sudo iptables -C INPUT {rule}")
            if returncode != 0:
                self.console.write(f"Error: Firewall rule for {description} is missing\n")
                success = False

        returncode, output, error = self.run_command("sudo iptables -t nat -L POSTROUTING -n -v")
        if "MASQUERADE" not in output:
            self.console.write("Error: NAT (MASQUERADE) rule is missing\n")
            success = False

        return success

    def test_dhcp(self):
        self.console.write("Testing DHCP server...\n")
        success = True

        returncode, output, error = self.run_command("systemctl is-active isc-dhcp-server")
        if "active" not in output:
            self.console.write("Error: DHCP server is not running\n")
            success = False

        returncode, output, error = self.run_command("cat /etc/dhcp/dhcpd.conf")
        if "subnet 192.168.32.0 netmask 255.255.240.0" not in output:
            self.console.write("Error: DHCP configuration for subnet 192.168.32.0/20 is missing\n")
            success = False

        return success

    def test_dns(self):
        self.console.write("Testing DNS server...\n")
        success = True

        returncode, output, error = self.run_command("systemctl is-active bind9")
        if "active" not in output:
            self.console.write("Error: BIND (DNS server) is not running\n")
            success = False

        domains_to_check = ["lille.local", "rennes.local"]
        for domain in domains_to_check:
            returncode, output, error = self.run_command(f"dig @localhost {domain}")
            if "ANSWER SECTION" not in output:
                self.console.write(f"Error: Unable to resolve {domain}\n")
                success = False

        returncode, output, error = self.run_command("dig @localhost -x 192.168.10.1")
        if "firewall-externe.lille.local" not in output:
            self.console.write("Error: Reverse DNS lookup failed for 192.168.10.1\n")
            success = False

        return success

    def test_smtp(self):
        self.console.write("Testing SMTP server...\n")
        success = True

        returncode, output, error = self.run_command("systemctl is-active postfix")
        if "active" not in output:
            self.console.write("Error: Postfix (SMTP server) is not running\n")
            success = False

        returncode, output, error = self.run_command("echo 'QUIT' | telnet localhost 25")
        if "220 smtp.lille.local ESMTP Postfix" not in output:
            self.console.write("Error: Unable to connect to SMTP server\n")
            success = False

        return success

    def test_nas(self):
        self.console.write("Testing NAS...\n")
        success = True

        returncode, output, error = self.run_command("systemctl is-active smbd")
        if "active" not in output:
            self.console.write("Error: Samba (NAS service) is not running\n")
            success = False

        returncode, output, error = self.run_command("testparm -s")
        if "share" not in output or "/srv/samba/share" not in output:
            self.console.write("Error: Samba share configuration is incorrect\n")
            success = False

        return success

    def test_vpn(self):
        self.console.write("Testing VPN server...\n")
        success = True

        returncode, output, error = self.run_command("systemctl is-active openvpn@server")
        if "active" not in output:
            self.console.write("Error: OpenVPN server is not running\n")
            success = False

        returncode, output, error = self.run_command("cat /etc/openvpn/server.conf")
        if "10.8.0.0 255.255.255.0" not in output:
            self.console.write("Error: OpenVPN server configuration is incorrect\n")
            success = False

        return success

class Application(tk.Tk):
    def __init__(self, vms):
        super().__init__()
        self.title("VM Unit Test GUI")
        self.vms = vms
        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        self.consoles = {}
        for vm in self.vms:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=vm)
            console = VMConsole(frame, vm)
            console.pack(expand=True, fill='both')
            self.consoles[vm] = console

        self.start_button = ttk.Button(self, text="Start Tests", command=self.start_tests)
        self.start_button.pack()

    def start_tests(self):
        self.start_button.config(state='disabled')
        self.result_queue = queue.Queue()
        self.threads = []

        for vm in self.vms:
            thread = VMTester(vm, self.consoles[vm], self.result_queue)
            self.threads.append(thread)
            thread.start()

        self.after(100, self.check_threads)

    def check_threads(self):
        try:
            while True:
                vm, success = self.result_queue.get_nowait()
                self.consoles[vm].write(f"\nTest {'passed' if success else 'failed'} for {vm}\n")
                self.result_queue.task_done()
        except queue.Empty:
            pass

        if any(thread.is_alive() for thread in self.threads):
            self.after(100, self.check_threads)
        else:
            self.start_button.config(state='normal')

def main():
    parser = argparse.ArgumentParser(description="Run unit tests on Vagrant VMs with GUI")
    parser.add_argument("--vms", nargs="+", default=[
        "firewall-externe-lille",
        "firewall-interne-lille",
        "dhcp-server-lille",
        "dns-server-lille",
        "smtp-server-lille",
        "nas-lille",
        "vpn-server-lille",
        "firewall-externe-rennes",
        "dhcp-server-rennes"
    ], help="List of VMs to test")
    args = parser.parse_args()

    app = Application(args.vms)
    app.mainloop()

if __name__ == "__main__":
    main()