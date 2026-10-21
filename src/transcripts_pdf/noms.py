import re


def nom_pseudonymise(nom: str) -> str:
    return (
        f"pseudonymiser_{re.sub(r'^(?:pseudonymiser_)+', '', nom, flags=re.IGNORECASE)}"
    )
