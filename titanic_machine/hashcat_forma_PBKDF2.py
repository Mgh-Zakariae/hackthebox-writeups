import base64

salt_list = []
hash_passwd_list = []




def hex_to_base64(hex_salt, hex_passwd):
    for i in range(0,3):
        # Convert hex string to bytes
        hex_bytes_salt = bytes.fromhex(hex_salt[i])
        hex_bytes_passwd = bytes.fromhex(hex_passwd[i])
        # Convert bytes to base64
        base64_bytes_salt = base64.b64encode(hex_bytes_salt)
        base64_bytes_passwd = base64.b64encode(hex_bytes_passwd)
        # Decode base64 bytes to string
        base64_string_salt = base64_bytes_salt.decode('utf-8')
        base64_string_passwd = base64_bytes_passwd.decode('utf-8')
        print(f"sha256:50000:{base64_string_salt}:{base64_string_passwd}")


hex_to_base64(salt_list, hash_passwd_list)
