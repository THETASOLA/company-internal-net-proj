#!/usr/bin/env python3

import argparse
import subprocess
import sys
import time

def run_command(command, vm_name=None):
    if vm_name:
        command = f"vagrant ssh {vm_name} -c '{command}'"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return process.returncode, output.decode('utf-8'), error.decode('utf-8')

def test_vm(vm_name):
    print(f"Testing {vm_name}...")
    
    # Run specific tests based on VM name
    if "firewall" in vm_name:
        success = test_firewall(vm_name)
    elif "dhcp" in vm_name:
        success = test_dhcp(vm_name)
    elif "dns" in vm_name:
        success = test_dns(vm_name)
    elif "smtp" in vm_name:
        success = test_smtp(vm_name)
    elif "nas" in vm_name:
        success = test_nas(vm_name)
    elif "vpn" in vm_name:
        success = test_vpn(vm_name)
    else:
        print(f"No specific test for {vm_name}")
        success = True

    return success

def test_firewall(vm_name):
    print("Testing firewall...")
    success = True

    # Test if iptables is running
    returncode, output, error = run_command("sudo iptables -L", vm_name)
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
        returncode, output, error = run_command(f"sudo iptables -C INPUT {rule}", vm_name)
        if returncode != 0:
            print(f"Error: Firewall rule for {description} is missing")
            success = False

    # Test NAT
    returncode, output, error = run_command("sudo iptables -t nat -L POSTROUTING -n -v", vm_name)
    if "MASQUERADE" not in output:
        print("Error: NAT (MASQUERADE) rule is missing")
        success = False

    return success

def test_dhcp(vm_name):
    print("Testing DHCP server...")
    success = True

    # Test if DHCP server is running
    returncode, output, error = run_command("systemctl is-active isc-dhcp-server", vm_name)
    if "active" not in output:
        print("Error: DHCP server is not running")
        success = False

    # Test DHCP configuration
    returncode, output, error = run_command("cat /etc/dhcp/dhcpd.conf", vm_name)
    if "subnet 192.168.32.0 netmask 255.255.240.0" not in output:
        print("Error: DHCP configuration for subnet 192.168.32.0/20 is missing")
        success = False

    return success

def test_dns(vm_name):
    print("Testing DNS server...")
    success = True

    # Test if BIND is running
    returncode, output, error = run_command("systemctl is-active bind9", vm_name)
    if "active" not in output:
        print("Error: BIND (DNS server) is not running")
        success = False

    # Test DNS resolution for both Lille and Rennes domains
    domains_to_check = ["lille.local", "rennes.local"]
    for domain in domains_to_check:
        returncode, output, error = run_command(f"dig @localhost {domain}", vm_name)
        if "ANSWER SECTION" not in output:
            print(f"Error: Unable to resolve {domain}")
            success = False

    # Test reverse DNS lookup
    returncode, output, error = run_command("dig @localhost -x 192.168.10.1", vm_name)
    if "firewall-externe.lille.local" not in output:
        print("Error: Reverse DNS lookup failed for 192.168.10.1")
        success = False

    return success

def test_smtp(vm_name):
    print("Testing SMTP server...")
    success = True

    # Test if Postfix is running
    returncode, output, error = run_command("systemctl is-active postfix", vm_name)
    if "active" not in output:
        print("Error: Postfix (SMTP server) is not running")
        success = False

    # Test SMTP connection
    returncode, output, error = run_command("echo 'QUIT' | telnet localhost 25", vm_name)
    if "220 smtp.lille.local ESMTP Postfix" not in output:
        print("Error: Unable to connect to SMTP server")
        success = False

    return success

def test_nas(vm_name):
    print("Testing NAS...")
    success = True

    # Test if Samba is running
    returncode, output, error = run_command("systemctl is-active smbd", vm_name)
    if "active" not in output:
        print("Error: Samba (NAS service) is not running")
        success = False

    # Test Samba configuration
    returncode, output, error = run_command("testparm -s", vm_name)
    if "share" not in output or "/srv/samba/share" not in output:
        print("Error: Samba share configuration is incorrect")
        success = False

    return success

def test_vpn(vm_name):
    print("Testing VPN server...")
    success = True

    # Test if OpenVPN is running
    returncode, output, error = run_command("systemctl is-active openvpn@server", vm_name)
    if "active" not in output:
        print("Error: OpenVPN server is not running")
        success = False

    # Test OpenVPN configuration
    returncode, output, error = run_command("cat /etc/openvpn/server.conf", vm_name)
    if "10.8.0.0 255.255.255.0" not in output:
        print("Error: OpenVPN server configuration is incorrect")
        success = False

    return success

def test_inter_vm_communication():
    print("Testing inter-VM communication...")
    success = True

    # Test DNS resolution from DHCP server
    returncode, output, error = run_command("dig @192.168.12.2 smtp.lille.local", "dhcp-server-lille")
    if "192.168.13.2" not in output:
        print("Error: DHCP server unable to resolve SMTP server via DNS")
        success = False

    # Test connectivity from VPN server to NAS
    returncode, output, error = run_command("ping -c 3 192.168.14.2", "vpn-server-lille")
    if "3 packets transmitted, 3 received" not in output:
        print("Error: VPN server unable to reach NAS")
        success = False

    return success

def main():
    parser = argparse.ArgumentParser(description="Run unit tests on Vagrant VMs")
    parser.add_argument("--all", action="store_true", help="Test all VMs")
    parser.add_argument("--vm", type=str, help="Test a specific VM")
    parser.add_argument("--inter-vm", action="store_true", help="Test inter-VM communication")
    args = parser.parse_args()

    vms = [
        "firewall-externe-lille",
        "firewall-interne-lille",
        "dhcp-server-lille",
        "dns-server-lille",
        "smtp-server-lille",
        "nas-lille",
        "vpn-server-lille",
        "firewall-externe-rennes",
        "dhcp-server-rennes"
    ]

    if args.all:
        success = all(test_vm(vm) for vm in vms)
    elif args.vm:
        if args.vm not in vms:
            print(f"Error: {args.vm} is not a valid VM name")
            sys.exit(1)
        success = test_vm(args.vm)
    elif args.inter_vm:
        success = test_inter_vm_communication()
    else:
        print("Please specify either --all, --vm, or --inter-vm")
        sys.exit(1)

    if success:
        print("All tests passed successfully!")
    else:
        print("Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
