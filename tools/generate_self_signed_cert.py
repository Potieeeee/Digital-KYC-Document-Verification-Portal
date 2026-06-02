from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import IPAddress
import datetime
import ipaddress

# Generate private key
key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
private_key = key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
)

# Build certificate
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"State"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Locality"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Local Dev"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
])
cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=1))
    .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(u"localhost"),
            IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256(), default_backend())
)

cert_pem = cert.public_bytes(serialization.Encoding.PEM)

# Write files to project root
open("ssl.key", "wb").write(private_key)
open("ssl.crt", "wb").write(cert_pem)
print("Generated ssl.key and ssl.crt")
