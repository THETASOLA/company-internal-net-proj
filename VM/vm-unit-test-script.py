#!/usr/bin/env python3

import argparse
import subprocess
import sys
import time
import os

def run_command(command, vm_name=None, vm_dir=None):
    if vm_name and vm_dir:
        os.chdir(vm_dir)
        command = f"vagrant ssh -c '{command}'"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if vm_name and vm_dir:
        os.chdir('../..')  # Return to the original directory
    return process.returncode, output.decode('utf-8'), error.decode('utf-8')

def start_vm(vm_name, vm_dir):
    if vm_name and vm_dir:
        os.chdir(vm_dir)
    else:
        print("Error: VM name and directory must be provided")
        return 1, "", "Error: VM name and directory must be provided"
    process = subprocess.Popen(f"vagrant up  '{vm_name}'", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return process.returncode, output.decode('utf-8'), error.decode('utf-8')

def test_vm(vm_name, vm_dir):
    print(f"Testing {vm_name}...")
    
    # Start the VM
    returncode, output, error = run_command(f"vagrant up", vm_name=vm_name, vm_dir=vm_dir)
    if returncode != 0:
        print(f"Error starting {vm_name}: {error}")
        return False

    # Run specific tests based on VM name
    if "firewall" in vm_name:
        success = test_firewall(vm_name, vm_dir)
    elif "dhcp" in vm_name:
        success = test_dhcp(vm_name, vm_dir)
    elif "dns" in vm_name:
        success = test_dns(vm_name, vm_dir)
    elif "smtp" in vm_name:
        success = test_smtp(vm_name, vm_dir)
    elif "nas" in vm_name:
        success = test_nas(vm_name, vm_dir)
    elif "vpn" in vm_name:
        success = test_vpn(vm_name, vm_dir)
    else:
        print(f"No specific test for {vm_name}")
        success = True

    # Stop the VM
    run_command(f"vagrant halt", vm_name=vm_name, vm_dir=vm_dir)

    return success

def test_firewall(vm_name, vm_dir):
    print("Testing firewall...")
    success = True

    # Test if iptables is running
    returncode, output, error = run_command("sudo iptables -L", vm_name=vm_name, vm_dir=vm_dir)
    if returncode != 0:
        print("Error: iptables is not running")
        success = False

    # Test specific firewall rules
    rules_to_check = [
        ("-A INPUT -p tcp --dport 22 -j ACCEPT", "SSH allowed"),
        ("-A INPUT -p tcp --dport 80 -j ACCEPT", "HTTP allowed"),
        ("-A INPUT -p tcp --dport 443 -j ACCEPT", "HTTPS allowed"),
        ("-A INPUT -p icmp -j ACCEPT", "ICMP (ping) allowed")
    ]

    for rule, description in rules_to_check:
        returncode, output, error = run_command(f"sudo iptables -C INPUT {rule}", vm_name=vm_name, vm_dir=vm_dir)
        if returncode != 0:
            print(f"Error: Firewall rule for {description} is missing")
            success = False

    # Test NAT
    returncode, output, error = run_command("sudo iptables -t nat -L POSTROUTING -n -v", vm_name=vm_name, vm_dir=vm_dir)
    if "MASQUERADE" not in output:
        print("Error: NAT (MASQUERADE) rule is missing")
        success = False

    return success

def test_dhcp(vm_name, vm_dir):
    print("Testing DHCP server...")
    success = True

    # Test if DHCP server is running
    returncode, output, error = run_command("systemctl is-active isc-dhcp-server", vm_name=vm_name, vm_dir=vm_dir)
    if "active" not in output:
        print("Error: DHCP server is not running")
        success = False

    # Test DHCP configuration
    returncode, output, error = run_command("cat /etc/dhcp/dhcpd.conf", vm_name=vm_name, vm_dir=vm_dir)
    if "subnet 192.168.32.0 netmask 255.255.240.0" not in output:
        print("Error: DHCP configuration for subnet 192.168.32.0/20 is missing")
        success = False

    # Test DHCP lease
    returncode, output, error = run_command("sudo dhclient -v eth1", vm_name=vm_name, vm_dir=vm_dir)
    if "bound to" not in output:
        print("Error: Unable to obtain IP address via DHCP")
        success = False

    return success

def test_dns(vm_name, vm_dir):
    print("Testing DNS server...")
    success = True

    # Test if BIND is running
    returncode, output, error = run_command("systemctl is-active bind9", vm_name=vm_name, vm_dir=vm_dir)
    if "active" not in output:
        print("Error: BIND (DNS server) is not running")
        success = False

    # Test DNS resolution for both Lille and Rennes domains
    domains_to_check = ["lille.local", "rennes.local"]
    for domain in domains_to_check:
        returncode, output, error = run_command(f"dig @localhost {domain}", vm_name=vm_name, vm_dir=vm_dir)
        if "ANSWER SECTION" not in output:
            print(f"Error: Unable to resolve {domain}")
            success = False

    # Test reverse DNS lookup
    returncode, output, error = run_command("dig @localhost -x 192.168.10.1", vm_name=vm_name, vm_dir=vm_dir)
    if "firewall-externe.lille.local" not in output:
        print("Error: Reverse DNS lookup failed for 192.168.10.1")
        success = False

    return success

def test_smtp(vm_name, vm_dir):
    print("Testing SMTP server...")
    success = True

    # Test if Postfix is running
    returncode, output, error = run_command("systemctl is-active postfix", vm_name=vm_name, vm_dir=vm_dir)
    if "active" not in output:
        print("Error: Postfix (SMTP server) is not running")
        success = False

    # Test SMTP connection
    returncode, output, error = run_command("telnet localhost 25", vm_name=vm_name, vm_dir=vm_dir)
    if "220 smtp.lille.local ESMTP Postfix" not in output:
        print("Error: Unable to connect to SMTP server")
        success = False

    # Test sending an email
    test_email = """Subject: Test Email
From: test@lille.local
To: test@lille.local

This is a test email."""

    returncode, output, error = run_command(f"echo '{test_email}' | sendmail -t", vm_name=vm_name, vm_dir=vm_dir)
    if returncode != 0:
        print("Error: Unable to send test email")
        success = False

    # Check if email was received
    time.sleep(5)  # Wait for email to be processed
    returncode, output, error = run_command("grep 'This is a test email' /var/mail/vagrant", vm_name=vm_name, vm_dir=vm_dir)
    if returncode != 0:
        print("Error: Test email was not received")
        success = False

    return success

def test_nas(vm_name, vm_dir):
    print("Testing NAS...")
    success = True

    # Test if Samba is running
    returncode, output, error = run_command("systemctl is-active smbd", vm_name=vm_name, vm_dir=vm_dir)
    if "active" not in output:
        print("Error: Samba (NAS service) is not running")
        success = False

    # Test Samba configuration
    returncode, output, error = run_command("testparm -s", vm_name=vm_name, vm_dir=vm_dir)
    if "share" not in output or "/srv/samba/share" not in output:
        print("Error: Samba share configuration is incorrect")
        success = False

    # Test accessing the share
    returncode, output, error = run_command("smbclient -N -L //localhost", vm_name=vm_name, vm_dir=vm_dir)
    if "share" not in output:
        print("Error: Unable to list Samba shares")
        success = False

    # Test writing to the share
    returncode, output, error = run_command("echo 'test' | smbclient -N //localhost/share -c 'put - test.txt'", vm_name=vm_name, vm_dir=vm_dir)
    if returncode != 0:
        print("Error: Unable to write to Samba share")
        success = False

    return success

def test_vpn(vm_name, vm_dir):
    print("Testing VPN server...")
    success = True

    # Test if OpenVPN is running
    returncode, output, error = run_command("systemctl is-active openvpn@server", vm_name=vm_name, vm_dir=vm_dir)
    if "active" not in output:
        print("Error: OpenVPN server is not running")
        success = False

    # Test OpenVPN configuration
    returncode, output, error = run_command("cat /etc/openvpn/server.conf", vm_name=vm_name, vm_dir=vm_dir)
    if "10.8.0.0 255.255.255.0" not in output:
        print("Error: OpenVPN server configuration is incorrect")
        success = False

    # Test VPN connectivity (this would typically be done from a client machine)
    # For this example, we'll just check if the tun0 interface is up
    returncode, output, error = run_command("ip addr show tun0", vm_name=vm_name, vm_dir=vm_dir)
    if returncode != 0:
        print("Error: OpenVPN tun0 interface is not up")
        success = False

    return success

def test_inter_vm_communication():
    print("Testing inter-VM communication...")
    success = True

    # Test DNS resolution from DHCP server
    returncode, output, error = run_command("dig @192.168.12.2 smtp.lille.local", vm_name="dhcp-server-lille", vm_dir="Lille/dhcp")
    if "192.168.13.2" not in output:
        print("Error: DHCP server unable to resolve SMTP server via DNS")
        success = False

    # Test email sending from NAS to SMTP server
    test_email = """Subject: Test Email from NAS
From: nas@lille.local
To: admin@lille.local

This is a test email from NAS."""

    returncode, output, error = run_command(f"echo '{test_email}' | sendmail -t", vm_name="nas-lille", vm_dir="Lille/nas")
    if returncode != 0:
        print("Error: Unable to send test email from NAS to SMTP server")
        success = False

    # Test VPN access to internal resources
    returncode, output, error = run_command("ping -c 3 192.168.14.2", vm_name="vpn-server-lille", vm_dir="Lille/vpn")
    if "3 packets transmitted, 3 received" not in output:
        print("Error: VPN server unable to reach NAS")
        success = False

    return success

def main():
    parser = argparse.ArgumentParser(description="Run unit tests on Vagrant VMs")
    parser.add_argument("--on", action="store_true", help="Starts all VMS")
    parser.add_argument("--all", action="store_true", help="Test all VMs")
    parser.add_argument("--vm", type=str, help="Test a specific VM")
    parser.add_argument("--inter-vm", action="store_true", help="Test inter-VM communication")
    args = parser.parse_args()
    vms = []

    if args.all:
        vms = [
            ("firewall-externe-lille", "Lille/firewall_ext"),
            ("firewall-interne-lille", "Lille/firewall_int"),
            ("dhcp-server-lille", "Lille/dhcp"),
            ("dns-server-lille", "Lille/dns"),
            ("smtp-server-lille", "Lille/smtp"),
            ("nas-lille", "Lille/nas"),
            ("vpn-server-lille", "Lille/vpn"),
            ("firewall-externe-rennes", "Rennes/firewall_ext"),
            ("dhcp-server-rennes", "Rennes/dhcp")
        ]
    elif args.vm:
        # Determine the directory based on the VM name
        if "lille" in args.vm.lower():
            site = "Lille"
        elif "rennes" in args.vm.lower():
            site = "Rennes"
        else:
            print(f"Unable to determine site for VM: {args.vm}")
            sys.exit(1)
        
        vm_type = args.vm.split('-')[0]
        vm_dir = f"{site}/{vm_type}"
        vms = [(args.vm, vm_dir)]
    elif args.on:
        #start all VMs
        arg = [
            ("firewall-externe-lille", "Lille/firewall_ext"),
            ("firewall-interne-lille", "Lille/firewall_int"),
            ("dhcp-server-lille", "Lille/dhcp"),
            ("dns-server-lille", "Lille/dns"),
            ("smtp-server-lille", "Lille/smtp"),
            ("nas-lille", "Lille/nas"),
            ("vpn-server-lille", "Lille/vpn"),
            ("firewall-externe-rennes", "Rennes/firewall_ext"),
            ("dhcp-server-rennes", "Rennes/dhcp")
        ]
        for vm_name, vm_dir in arg:
            returncode, output, error = start_vm(vm_name=vm_name, vm_dir=vm_dir)
            if returncode != 0:
                print(f"Error starting {vm_name}: {error}")
                sys.exit(1)
    elif args.inter_vm:
        return test_inter_vm_communication()
    else:
        print("Please specify either --all, --vm, or --inter-vm")
        sys.exit(1)

    success = True
    for vm_name, vm_dir in vms:
        if not test_vm(vm_name, vm_dir):
            success = False

    if success:
        print("All tests passed successfully!")
    else:
        print("Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
