from typing import Any

from configuration import BaseDeDonnees
from correspondance.depot import Cle, DepotCorrespondance, Feature
from infra.connexion_base_de_donnees import avec_connexion

class DepotCorrespondancePostgres(DepotCorrespondance):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def features_sans_embedding(self) -> list[Feature]:
        with self._connexion.cursor() as cur:
            cur.execute("SELECT source, id, texte, transcript_id, verbatim FROM features_embeddables WHERE embedding IS NULL")
            return [Feature(source=r[0], id=r[1], texte=r[2], transcript_id=r[3], verbatim=r[4]) for r in cur.fetchall()]

    @avec_connexion
    def enregistrer_embeddings(self, items: list[tuple[str, int, list[float]]]) -> None:
        with self._connexion.cursor() as cur:
            for source, id_, vecteur in items:
                cur.execute(
                    "UPDATE besoins_detectes SET embedding = %s::vector WHERE source = %s AND source_id = %s",
                    (str(vecteur), source, id_),
                )

    @avec_connexion
    def lister_features(self) -> list[Feature]:
        with self._connexion.cursor() as cur:
            cur.execute("SELECT source, id, texte, transcript_id, verbatim FROM features_embeddables WHERE embedding IS NOT NULL")
            return [Feature(source=r[0], id=r[1], texte=r[2], transcript_id=r[3], verbatim=r[4]) for r in cur.fetchall()]

    @avec_connexion
    def paires_proches(self, seuil: float) -> list[tuple[Cle, Cle]]:
        with self._connexion.cursor() as cur:
            cur.execute(
                """SELECT a.source, a.id, b.source, b.id
                   FROM features_embeddables a JOIN features_embeddables b
                     ON (a.source, a.id) < (b.source, b.id)
                   WHERE a.embedding IS NOT NULL AND b.embedding IS NOT NULL
                     AND a.embedding <=> b.embedding < %s""",
                (seuil,),
            )
            return [((r[0], r[1]), (r[2], r[3])) for r in cur.fetchall()]
