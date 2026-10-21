import unicodedata

from liste_blanche.depot import DepotListeBlanche, TermeListeBlanche

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


class ServiceListeBlanche:
    def __init__(self, depot: DepotListeBlanche) -> None:
        self._depot = depot

    def lister(self) -> list[TermeListeBlanche]:
        return self._depot.lister()

    def ajouter(self, terme: str) -> TermeListeBlanche:
        propre, cle = normaliser_terme(terme)
        return self._depot.ajouter(propre, cle)

    def modifier(
        self, identifiant: int, terme: str, revision: int
    ) -> TermeListeBlanche:
        propre, cle = normaliser_terme(terme)
        return self._depot.modifier(identifiant, propre, cle, revision)

    def supprimer(self, identifiant: int, revision: int) -> None:
        self._depot.supprimer(identifiant, revision)
