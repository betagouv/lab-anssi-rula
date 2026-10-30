import unicodedata

LONGUEUR_MAXIMALE = 120


def normaliser_terme(terme: str) -> tuple[str, str]:
    propre = unicodedata.normalize("NFC", " ".join(terme.split()))
    if (
        not propre
        or len(propre) > LONGUEUR_MAXIMALE
        or not any(caractere.isalnum() for caractere in propre)
    ):
        raise ValueError(
            "Le terme doit contenir des lettres ou chiffres et rester court."
        )
    return propre, propre.casefold()
