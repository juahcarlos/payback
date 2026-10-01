from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509.oid import NameOID

from .utils import get_cert_dict


current_dir = Path(__file__).resolve().parent


class CertificateBuilderService:  # TODO: refactor
    @staticmethod
    def generate_private_key_pem(
            key_size: int = 2048,
            private_key_pass: bytes = b"",
    ) -> bytes:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        if not private_key_pass:
            unencrypted_pem_private_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            return unencrypted_pem_private_key

        encrypted_pem_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(private_key_pass)
        )
        return encrypted_pem_private_key

    @staticmethod
    def generate_csr(
            priv_key_pem: bytes,
            password: bytes | None = None,
            cn: str = "",
    ) -> bytes:
        key = load_pem_private_key(priv_key_pem, password=password)
        csr = x509.CertificateSigningRequestBuilder().subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, cn),
            ])
        ).add_extension(
                x509.SubjectKeyIdentifier.from_public_key(key.public_key()),  # type: ignore[arg-type]
                critical=False,
        ).sign(key, hashes.SHA256())  # type: ignore[arg-type]

        csr_pem = csr.public_bytes(serialization.Encoding.PEM)

        return csr_pem

    @staticmethod
    def _build_certificate(
            csr_cert: x509.CertificateSigningRequest,
            ca_cert: x509.Certificate,
    ) -> x509.CertificateBuilder:
        return x509.CertificateBuilder().subject_name(
            csr_cert.subject
        ).issuer_name(
            ca_cert.subject
        ).public_key(
            csr_cert.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(UTC)
        ).not_valid_after(
            datetime.now(UTC) + timedelta(days=7300)
        )

    def sign_certificate_request(
            self,
            csr_cert: x509.CertificateSigningRequest,
            ca_cert: x509.Certificate,
            private_ca_key: rsa.RSAPrivateKey,
            certtype: str = "client",
    ) -> str:
        cert = self._build_certificate(csr_cert=csr_cert, ca_cert=ca_cert)

        cert = cert.add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=False
        )
        if isinstance(csr_cert.extensions, x509.Extensions):
            for ext in csr_cert.extensions:
                cert = cert.add_extension(
                    extval=ext.value,
                    critical=ext.critical,
                )

        cert = cert.add_extension(
            x509.KeyUsage(
                key_cert_sign=False,
                crl_sign=False,
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=True,
                encipher_only=False,
                decipher_only=False
            ),
            critical=False,
        )

        if certtype == "server":
            cert = cert.add_extension(
                x509.UnrecognizedExtension(
                    oid=x509.ObjectIdentifier('2.16.840.1.113730.1.1'),
                    value=b'\x03\x02\x06@',
                ),
                critical=False,
            ).add_extension(
                x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
                critical=False,
            )

        if certtype == "client":
            cert = cert.add_extension(
                x509.UnrecognizedExtension(
                    oid=x509.ObjectIdentifier('2.16.840.1.113730.1.1'),
                    value=b'\x03\x02\x07\x80',
                ),
                critical=False,
            )
            cert = cert.add_extension(
                x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]),
                critical=False,
            )

        try:
            ca_key_identifier = ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier)
            cert = cert.add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ca_key_identifier.value),
                critical=False
            )
        except x509.ExtensionNotFound:
            pass

        cert = cert.sign(private_ca_key, hashes.SHA256())  # type: ignore[assignment]

        return cert.public_bytes(serialization.Encoding.PEM).decode()  # type: ignore[attr-defined,no-any-return]

    def generate_cert_from_csr(self, csr_pem: bytes, certtype: str = "client") -> str:
        csr_cert = x509.load_pem_x509_csr(csr_pem)

        # TODO - checks needed
        if isinstance(csr_cert, x509.CertificateSigningRequest):
            pass

        if isinstance(csr_cert.signature_hash_algorithm, hashes.SHA256):
            pass

        with open(current_dir / 'cacert.pem', 'rb') as file:
            ca_cert_data = file.read()
            ca_cert = x509.load_pem_x509_certificate(ca_cert_data)

        with open(current_dir / 'cakey.pem', 'rb') as file:
            ca_privkey_data = file.read()
            ca_privkey = load_pem_private_key(ca_privkey_data, password=None)

        return self.sign_certificate_request(
            csr_cert=csr_cert,
            ca_cert=ca_cert,
            private_ca_key=ca_privkey,  # type: ignore[arg-type]
            certtype=certtype,
        )

    def build(self, username: str) -> dict[str, str]:
        openvpn_user_key = self.generate_private_key_pem()
        openvpn_user_csr = self.generate_csr(priv_key_pem=openvpn_user_key, cn=username)
        cert_from_csr = self.generate_cert_from_csr(csr_pem=openvpn_user_csr)

        return get_cert_dict(username=username, cert=cert_from_csr, key=openvpn_user_key.decode())
