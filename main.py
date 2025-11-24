from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
key = RSA.generate(2048)

private_key = key 
public_key = key.publickey()

pub_cipher = PKCS1_OAEP.new(public_key)
priv_cipher = PKCS1_OAEP.new(key)


message = "Salam aleykoum".encode('utf-8')

msg_chiffre = pub_cipher.encrypt(message)

print("Chiffre : ",msg_chiffre)
msg_dechiffre = priv_cipher.decrypt(msg_chiffre)
print("Dechiffre : ",msg_dechiffre)

