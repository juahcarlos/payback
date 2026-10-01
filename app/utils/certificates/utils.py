from pathlib import Path


current_dir = Path(__file__).resolve().parent


def get_cert_dict(username: str, cert: str, key: str) -> dict[str, str]:
    with open(current_dir / "cacert.pem", encoding="utf-8") as ca_file:
        ca = ca_file.read().strip()

    with open(current_dir / "ta.key", encoding="utf-8") as ta_file:
        tls = ta_file.read().strip()

    return {
        "username": username,
        "ca": ca,
        "cert": cert,
        "key": key,
        "tls": tls,
    }
