import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import subprocess
import queue
import argparse
import math

class VMConsole(ttk.Frame):
    def __init__(self, master, vm_name, width=80, height=10):
        super().__init__(master)
        self.vm_name = vm_name
        self.width = width
        self.height = height
        self.create_widgets()

    def create_widgets(self):
        self.console = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=self.width, height=self.height)
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
        full_command = f"""vagrant ssh {self.vm_name} -c "{command}" """
        self.console.write(f"{command}\n")
        print(full_command)
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        print(output.decode('utf-8'))
        print(error.decode('utf-8'))
        if process.returncode != 0:
            self.console.write(f"--- ERROR {process.returncode} ---:\n{error.decode('utf-8')}\n")
        self.console.write(output.decode('utf-8'))
        return process.returncode, output.decode('utf-8'), error.decode('utf-8')

    def test_vm(self):
        self.console.write(f"Testing {self.vm_name}...\n")
        
        if "fire" in self.vm_name:
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
            ("-p tcp --dport 22 -j ACCEPT", "SSH allowed"),
            ("-p tcp --dport 80 -j ACCEPT", "HTTP allowed"),
            ("-p tcp --dport 443 -j ACCEPT", "HTTPS allowed"),
            ("-p icmp -j ACCEPT", "ICMP (ping) allowed")
        ]

        for rule, description in rules_to_check:
            returncode, output, error = self.run_command(f"sudo iptables -C INPUT {rule}")
            if returncode != 0:
                self.console.write(f"Error: Firewall rule for {description} is missing\n")
                success = False

        if "ext" in self.vm_name:
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
        if self.vm_name == "dhcp-lille":
            if "subnet 192.168.50.0 netmask 255.255.255.0" not in output:
                self.console.write("Error: DHCP configuration for subnet 192.168.32.0/24 is missing\n")
                success = False
        else:
            if "subnet 192.168.51.0 netmask 255.255.255.0" not in output:
                self.console.write("Error: DHCP configuration for subnet 192.168.51.0/24 is missing\n")
                success = False

        self.console.write("Testing DHCP IP request...\n")
        returncode, output, error = self.run_command("sudo dhclient -v enp0s3")
        if returncode != 0 or "bound to" not in output:
            self.console.write("Error: Failed to obtain IP address from DHCP server\n")
            success = False
        else:
            self.console.write("Successfully obtained IP address from DHCP server\n")

        return success

    def test_dns(self):
        self.console.write("Testing DNS server...\n")
        success = True

        returncode, output, error = self.run_command("systemctl is-active bind9")
        if "active" not in output:
            self.console.write("Error: BIND (DNS server) is not running\n")
            success = False

        returncode, output, error = self.run_command(f"dig @localhost")
        if "ANSWER SECTION" not in output:
            self.console.write(f"Error: Unable to resolve localhost\n")
            success = False

        returncode, output, error = self.run_command("dig @localhost firewall-externe.lille.local")
        if "192.168.10.254" not in output:
            self.console.write("Error: Reverse DNS lookup failed for firewall-externe.lille.local\n")
            success = False

        returncode, output, error = self.run_command("dig @localhost smtp.lille.local")
        if "192.168.13.2" not in output:
            self.console.write("Error: Reverse DNS lookup failed for smtp.lille.local\n")
            success = False

        return success

    def test_smtp(self):
        self.console.write("Testing SMTP server...\n")
        success = True

        returncode, output, error = self.run_command("systemctl is-active postfix")
        if "active" not in output:
            self.console.write("Error: Postfix (SMTP server) is not running\n")
            success = False
        
        self.console.write("Sending test email...\n")
        
        send_email_command = f"echo 'Subject: Test Email   This is a test.' | /usr/sbin/sendmail smtp_test_user@localhost"
        returncode, output, error = self.run_command(send_email_command)

        if returncode != 0:
            self.console.write(f"Error: Failed to send email. Error: {error}\n")
            success = False
        else:
            self.console.write("Test email sent successfully.\n")
        
        self.console.write("Checking for received email...\n")
        
        mail_check_command = "sudo grep 'Subject: Test Email' /var/mail/smtp_test_user"
        returncode, output, error = self.run_command(mail_check_command)
        
        if returncode != 0:
            self.console.write("Error: Test email was not received in smtp_test_user's mailbox\n")
            success = False
        else:
            self.console.write("Test email received successfully.\n")
        
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

        test_file = "/srv/samba/share/test_file.txt"
        create_file_command = f"echo 'This is a test file' | sudo tee {test_file}"
        returncode, output, error = self.run_command(create_file_command)
        if returncode != 0:
            self.console.write(f"Error: Failed to create test file {test_file}\n")
            success = False
        else:
            self.console.write(f"Successfully created test file {test_file}\n")

        check_file_command = f"sudo test -f {test_file} && echo 'File exists' || echo 'File does not exist'"
        returncode, output, error = self.run_command(check_file_command)
        if "File exists" not in output:
            self.console.write(f"Error: Test file {test_file} does not exist\n")
            success = False
        else:
            self.console.write(f"Test file {test_file} exists\n")

        cat_file_command = f"sudo cat {test_file}"
        returncode, output, error = self.run_command(cat_file_command)
        if "This is a test file" not in output:
            self.console.write(f"Error: Test file {test_file} does not contain expected content\n")
            success = False
        else:
            self.console.write(f"Test file {test_file} contains correct content\n")

        remove_file_command = f"sudo rm {test_file}"
        returncode, output, error = self.run_command(remove_file_command)
        if returncode != 0:
            self.console.write(f"Warning: Failed to remove test file {test_file}\n")
        else:
            self.console.write(f"Successfully removed test file {test_file}\n")

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
    def __init__(self, vms, use_grid=False):
        super().__init__()
        self.title("VM Unit Test GUI")
        self.vms = vms
        self.use_grid = use_grid
        self.create_widgets()

    def create_widgets(self):
        self.consoles = {}

        if self.use_grid:
            self.create_grid_layout()
        else:
            self.create_notebook_layout()

        self.start_button = ttk.Button(self, text="Start Tests", command=self.start_tests)
        self.start_button.pack()

    def create_notebook_layout(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        for vm in self.vms:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=vm)
            console = VMConsole(frame, vm)
            console.pack(expand=True, fill='both')
            self.consoles[vm] = console

    def create_grid_layout(self):
        num_vms = len(self.vms)
        grid_size = math.ceil(math.sqrt(num_vms))

        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill='both')

        for i, vm in enumerate(self.vms):
            row = i // grid_size
            col = i % grid_size
            frame = ttk.Frame(main_frame)
            frame.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)
            
            label = ttk.Label(frame, text=vm)
            label.pack()
            
            console = VMConsole(frame, vm, width=40, height=5)  # Size
            console.pack(expand=True, fill='both')
            self.consoles[vm] = console

        for i in range(grid_size):
            main_frame.grid_columnconfigure(i, weight=1)
            main_frame.grid_rowconfigure(i, weight=1)

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
        "fire-ext-lille",
        "fire-int-lille",
        "dhcp-lille",
        "dns-lille",
        "smtp-lille",
        "nas-lille",
        "vpn-lille",
        "fire-ext-rennes",
        "dhcp-rennes"
    ], help="List of VMs to test")
    parser.add_argument("--grid", action="store_true", help="Use grid layout instead of notebook")
    args = parser.parse_args()

    app = Application(args.vms, use_grid=args.grid)
    app.mainloop()

if __name__ == "__main__":
    main()