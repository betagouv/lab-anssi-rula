import json
from collections import Counter, defaultdict
from dataclasses import dataclass

from adaptateurs.albert import AdaptateurAlbert
from correspondance.depot import Cle, Cluster, DepotCorrespondance, DepotCorrespondancesCalculees, Feature, Membre


@dataclass(frozen=True)
class ConfigurationCorrespondance:
    seuil: float
    prompt_libelle: str
    prompt_validation: str


class ServiceCorrespondance:
    def __init__(
        self,
        depot: DepotCorrespondance,
        depot_calcule: DepotCorrespondancesCalculees,
        albert: AdaptateurAlbert,
        configuration: ConfigurationCorrespondance,
    ) -> None:
        self._depot = depot
        self._depot_calcule = depot_calcule
        self._albert = albert
        self._seuil = configuration.seuil
        self._prompt_libelle = configuration.prompt_libelle
        self._prompt_validation = configuration.prompt_validation

    def charger(self) -> list[Cluster]:
        return self._depot_calcule.charger()

    def analyser(self) -> list[Cluster]:
        manquantes = self._depot.features_sans_embedding()
        if manquantes:
            vecteurs = self._albert.plonger([f.texte for f in manquantes])
            self._depot.enregistrer_embeddings([(f.source, f.id, v) for f, v in zip(manquantes, vecteurs)])
        clusters = self._regrouper(self._depot.lister_features(), self._depot.paires_proches(self._seuil))
        clusters = self._valider(clusters)
        clusters = self._nommer(clusters)
        self._depot_calcule.sauvegarder(clusters)
        return clusters

    def _valider(self, clusters: list[Cluster]) -> list[Cluster]:
        result = []
        for c in clusters:
            if c.occurrences < 2:
                result.append(c)
                continue
            contenu = "\n".join(f"{i}. {m.texte}" for i, m in enumerate(c.membres))
            try:
                reponse = self._albert.completer([
                    {"role": "system", "content": self._prompt_validation},
                    {"role": "user", "content": contenu},
                ])
                sous_groupes: list[list[int]] = json.loads(reponse.strip())
                for indices in sous_groupes:
                    membres = [c.membres[i] for i in indices if 0 <= i < len(c.membres)]
                    if membres:
                        result.append(Cluster(libelle="", occurrences=len(membres), membres=membres))
            except (json.JSONDecodeError, ValueError, IndexError):
                result.append(c)
        return result

    def _nommer(self, clusters: list[Cluster]) -> list[Cluster]:
        result = []
        for c in clusters:
            if c.occurrences > 1:
                libelle = self._albert.completer(
                    [
                        {"role": "system", "content": self._prompt_libelle},
                        {"role": "user", "content": "\n".join(f"- {m.texte}" for m in c.membres)},
                    ]
                ).strip()
            else:
                libelle = c.libelle

            # La validation peut créer un groupe unitaire avec un libellé vide.
            # Dans ce cas, le texte du besoin reste un intitulé fiable et lisible.
            if not libelle and c.membres:
                libelle = c.membres[0].texte

            result.append(Cluster(libelle=libelle, occurrences=c.occurrences, membres=c.membres))
        return result

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
                membres=[
                    Membre(
                        source=f.source,
                        texte=f.texte,
                        transcript_id=f.transcript_id,
                        verbatim=f.verbatim,
                        source_id=f.id,
                    )
                    for f in membres
                ],
            )
            for membres in groupes.values()
        ]
        return sorted(clusters, key=lambda c: (-c.occurrences, c.libelle))
