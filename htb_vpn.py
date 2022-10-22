#!/usr/bin/env python3

import os
import re


class VpnDetails:
    def __init__(self):
        self.country = ""  # (EU, UE, SG, AU)
        self.type = ""  # (FREE, VIP, VIP+)
        self.server_id = ""  # (1, 2, 3, 4, 5)
        self.proto = ""  # (tcp, udp)
        self.port = ""  # (tcp -> 443, udp -> 1337)

    def __str__(self):
        return f'{self.country} - {self.type} {self.server_id} ({self.proto}:{self.port})'


class OVPN:
    def __init__(self, name, path):
        self.name = name
        self.full_path = path
        self.details = self.__extract_details__()

    def __str__(self):
        return f'{self.name} [{self.details}]'

    def __extract_details__(self):
        if not self.full_path.endswith(".ovpn"):
            print(f'[WARN] File "{self.full_path}" has an incorrect file extension (.ovpn expected)')
        try:
            with open(self.full_path, 'r') as _ovpn:
                lines = _ovpn.readlines()
                vpn_details = VpnDetails()

                # protocol line 2
                if re.fullmatch("^proto (tcp|udp)\n$", lines[2]) is None:
                    print(lines[2])
                    print(f'[ERROR] Error reading the protocol ({self.full_path}:2)')
                else:
                    vpn_details.proto = lines[2].replace('\n', '').split(' ')[1].strip()
                # remote & port line 3
                remote = lines[3].split(' ')[1].split('.')[0].replace('edge-', '').replace('dedivip', 'vip+')
                vpn_details.port = lines[3].split(' ')[2].replace('\n', '')
                vpn_details.country = remote.split('-')[0].upper()
                vpn_details.type = remote.split('-')[1].upper()
                vpn_details.server_id = remote.split('-')[2]
                return vpn_details
        except IsADirectoryError:
            print(f'[ERROR] File "{self.full_path}" is a directory')
            exit(2)
        except FileNotFoundError:
            print(f'[ERROR] File "{self.full_path}" does not exists')
            exit(2)
        except PermissionError:
            print(f'[ERROR] Not enough permissions on the file "{self.full_path}"')
            exit(2)


def get_available_vpns(conn_dir):
    _available = []
    for f in os.listdir(conn_dir):
        ovpn = OVPN(f, f'{conn_dir}/{f}')
        _available.append(ovpn)
    return _available

def check_updates(*args):
    for pkg in args:
        if os.system(f'which {pkg} > /dev/null') != 0:
            while True:
                opt = input(f'[ERROR] {pkg} is not installed. Do you want to install it? (additional packages may be installed) [Y/n]\t').lower()
                if opt == '' or re.fullmatch('^(yes|y)$', opt) is not None:
                    print(f'[INFO] Installing {pkg}. Sudo required to execute apt install {pkg}')
                    os.system(f'sudo apt install {pkg}')
                    break
                elif re.fullmatch('^(no|n)$', opt) is not None:
                    break
                else:
                    print('Please type y (yes) or n (no)')
        elif os.system(f'apt list --upgradable 2> /dev/null | grep {pkg}') == 0:
            while True:
                opt = input('[WARN] Update available for {pkg}. It is recommended to install. Continue? (additional packages may be updated) [Y/n]\t').lower()
                if opt == '' or re.fullmatch('^(yes|y)$', opt) is not None:
                    print(f'[INFO] Updating {pkg}. Sudo required to execute apt upgrade')
                    os.system('sudo apt update; sudo apt upgrade')
                    break
                elif re.fullmatch('^(no|n)$', opt) is not None:
                    break
                else:
                    print('Please type y (yes) or n (no)')
        else:
            print(f'[INFO] {pkg} installed and updated')

if __name__ == '__main__':
    
    # 0. Find installation dir
    _root_dir = None
    os.system('find $HOME -name "htb-vpn" > /tmp/yKmnLc75wC2JF7e')
    try:
        with open('/tmp/yKmnLc75wC2JF7e', 'r') as rdir:
            _root_dir = rdir.readlines()[0].replace('\n', '')
    except:
        print(f'[ERROR] Installation dir not found')
        print(f'[INFO] Creating app directory in $HOME/htb-vpn. You may change the location later')
        if os.system('mkdir -p $HOME/htb-vpn $HOME/htb-vpn/conn') == 0:
            print(f'[INFO] Directory structure created successfully. Please restart the application')
            exit(0)
        else:
            print(f'[INFO] Directory structure could not be initialized. Enough permissions granted?')
    if _root_dir is None:
        exit(4)
    
    # 1. Print the banner
    _banner = f"+----------------+\n|  HTB VPN  v$(cat {_root_dir}/version.txt) |\n+----------------+  By @uRHL\n"
    os.system(f'echo "{_banner}"')
    print(f'[INFO] Using root dir: {_root_dir}')

    # 2. Check openvpn installation & updates
    check_updates('python3', 'openvpn')
    
    # 3. Get available VPN configurations
    available = get_available_vpns(f'{_root_dir}/conn')
    selected_vpn = None
    opt = -1
    if len(available) == 0:
        print(f'[ERROR] No VPN available. Please read the section "Select your VPN" in the README file')
        exit(3)
    elif len(available) == 1:
        selected_vpn = available[0]
    else:
        while True:
            try:
                print(f'\nAvailable VPNs:')
                # print available VPNs
                count = 1
                print(f'>')
                for vpn in available:
                    print(f'  {count}. {vpn}')
                    count += 1
                print(f'>')
                opt = int(input("\nSelect a vpn configuration to continue:\t"))
                if opt not in range(1, len(available)+1):
                    raise IndexError
                else:
                    selected_vpn = available[opt - 1]
                    # print(f'\n[INFO] You selected {opt} ({available[opt - 1]})')
                    break
            except ValueError:
                print("Option not recognized. Please select a valid option")
            except IndexError:
                print("Index out of range. Please select a valid option")
            except KeyboardInterrupt:
                print("\n[INFO] Operation aborted. Exiting...")
                break

    if selected_vpn is None:
        exit(4)
    else:
        # 4. Connect to the VPN
        print(f'[INFO] Loading VPN configuration from {selected_vpn}')
        print(f'[INFO] Establishing VPN connection...')
        os.system(f'sudo openvpn {selected_vpn.full_path}')
        print('[INFO] VPN connection closed')
        exit(0)
