from collections import Counter, defaultdict

from adaptateurs.albert import AdaptateurAlbert
from correspondance.depot import Cle, Cluster, DepotCorrespondance, DepotCorrespondancesCalculees, Feature, Membre


class ServiceCorrespondance:
    def __init__(
        self,
        depot: DepotCorrespondance,
        depot_calcule: DepotCorrespondancesCalculees,
        albert: AdaptateurAlbert,
        seuil: float,
        prompt_libelle: str,
    ) -> None:
        self._depot = depot
        self._depot_calcule = depot_calcule
        self._albert = albert
        self._seuil = seuil
        self._prompt_libelle = prompt_libelle

    def charger(self) -> list[Cluster]:
        return self._depot_calcule.charger()

    def analyser(self) -> list[Cluster]:
        manquantes = self._depot.features_sans_embedding()
        if manquantes:
            vecteurs = self._albert.plonger([f.texte for f in manquantes])
            self._depot.enregistrer_embeddings([(f.source, f.id, v) for f, v in zip(manquantes, vecteurs)])
        clusters = self._regrouper(self._depot.lister_features(), self._depot.paires_proches(self._seuil))
        clusters = self._nommer(clusters)
        self._depot_calcule.sauvegarder(clusters)
        return clusters

    def _nommer(self, clusters: list[Cluster]) -> list[Cluster]:
        return [
            Cluster(
                libelle=self._albert.completer(
                    [
                        {"role": "system", "content": self._prompt_libelle},
                        {"role": "user", "content": "\n".join(f"- {m.texte}" for m in c.membres)},
                    ]
                ).strip(),
                occurrences=c.occurrences,
                membres=c.membres,
            )
            if c.occurrences > 1
            else c
            for c in clusters
        ]

    def _regrouper(self, features: list[Feature], paires: list[tuple[Cle, Cle]]) -> list[Cluster]:
        parent = {(f.source, f.id): (f.source, f.id) for f in features}

        def racine(c: Cle) -> Cle:
            while parent[c] != c:
                parent[c] = parent[parent[c]]
                c = parent[c]
            return c

        for a, b in paires:
            parent[racine(a)] = racine(b)
        degre: Counter[Cle] = Counter()
        for a, b in paires:
            degre[a] += 1
            degre[b] += 1
        groupes: dict[Cle, list[Feature]] = defaultdict(list)
        for f in features:
            groupes[racine((f.source, f.id))].append(f)
        clusters = [
            Cluster(
                libelle=max(membres, key=lambda f: (degre[(f.source, f.id)], -len(f.texte))).texte,
                occurrences=len(membres),
                membres=[Membre(f.source, f.texte, f.transcript_id, f.verbatim) for f in membres],
            )
            for membres in groupes.values()
        ]
        return sorted(clusters, key=lambda c: (-c.occurrences, c.libelle))
