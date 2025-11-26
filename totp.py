#Creation TOTP ensuite scan en mettant sur un convertisseur lien vers qr code on scan avec telephone et c'est bon 
import pyotp
secret = pyotp.random_base32()
print("Cle TOTP secrete : ",secret)

totp = pyotp.TOTP(secret)
uri = totp.provisioning_uri(name="Al-Misri", issuer_name="Boite Secrète")

print(uri)