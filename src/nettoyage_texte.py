_CARACTERES_A_REMPLACER = str.maketrans(
    {
        "\x19": "’",
        "\x1c": "«",
        "\x1d": "»",
    }
)


def nettoie_texte(texte: str) -> str:
    """Rend lisibles les caractères de contrôle présents dans certains exports CSV."""
    texte = texte.translate(_CARACTERES_A_REMPLACER)
    return "".join(caractere for caractere in texte if caractere in "\n\r\t" or ord(caractere) >= 0x20)
