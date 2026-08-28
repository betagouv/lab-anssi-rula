import math

from correspondance.depot import Cle, DepotCorrespondance, Feature


class DepotCorrespondanceMemoire(DepotCorrespondance):
    def __init__(self, features: list[Feature]) -> None:
        self._features = features
        self._embeddings: dict[Cle, list[float]] = {}

    def features_sans_embedding(self, produit_id: int | None = None) -> list[Feature]:
        return [f for f in self._features if (produit_id is None or f.produit_id == produit_id) and (f.source, f.id) not in self._embeddings]

    def enregistrer_embeddings(self, items: list[tuple[str, int, list[float]]]) -> None:
        for source, id_, vecteur in items:
            self._embeddings[(source, id_)] = vecteur

    def lister_features(self, produit_id: int | None = None) -> list[Feature]:
        return [f for f in self._features if (produit_id is None or f.produit_id == produit_id) and (f.source, f.id) in self._embeddings]

    def paires_proches(self, seuil: float, produit_id: int | None = None) -> list[tuple[Cle, Cle]]:
        cles = [(f.source, f.id) for f in self._features if (produit_id is None or f.produit_id == produit_id) and (f.source, f.id) in self._embeddings]
        return [
            (cles[i], cles[j])
            for i in range(len(cles))
            for j in range(i + 1, len(cles))
            if _distance_cosinus(self._embeddings[cles[i]], self._embeddings[cles[j]]) < seuil
        ]


def _distance_cosinus(a: list[float], b: list[float]) -> float:
    produit = sum(x * y for x, y in zip(a, b))
    norme = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return 1 - produit / norme
