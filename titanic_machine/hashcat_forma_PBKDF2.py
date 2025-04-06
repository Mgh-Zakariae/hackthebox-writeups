import base64

salt_list = ["2d149e5fbd1b20cf31db3e3c6a28fc9b", "8bf3e3452b78544f8bee9400d6936d34", "e5492a913aef3ed1d914f4b73f027f55"]
hash_passwd_list = ["cba20ccf927d3ad0567b68161732d3fbca098ce886bbc923b4062a3960d459c08d2dfc063b2406ac9207c980c47c5d017136", "e531d398946137baea70ed6a680a54385ecff131309c0bd8f225f284406b7cbc8efc5dbef30bf1682619263444ea594cfb56", "34eb463d5102aea22d11d1521bd2e556906219ffb3b203a125d375d349b13e12be89ba99657970b78f6a95da0bc0f33fd952"]




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
