from datetime import date
from typing import Any

import psycopg2

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from projets.depot import DepotProjets, Entretien, Projet, ScanProjet, SourceProjet
from projets.service import ProjetDejaExistant

_COLONNES_PROJET = "id, produit_id, nom, brief, cree_le"
_COLONNES_ENTRETIEN = (
    "id, projet_id, participant, date_entretien, moderateur, contenu, "
    "note_moderateur, cree_le"
)


def _obtenir_projet(curseur: Any, projet_id: int) -> Projet:  # pragma: no cover
    curseur.execute(
        f"SELECT {_COLONNES_PROJET} FROM projets_recherche WHERE id = %s",
        (projet_id,),
    )
    return Projet(*curseur.fetchone())


def _ajouter_entretien(
    curseur: Any,
    valeurs: tuple[Any, ...],
) -> Entretien:  # pragma: no cover
    curseur.execute(
        "INSERT INTO transcripts "
        "(projet_id, participant, date_entretien, moderateur, contenu, note_moderateur) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING "
        f"{_COLONNES_ENTRETIEN}",
        valeurs,
    )
    return Entretien(*curseur.fetchone())


class DepotProjetsPostgres(DepotProjets):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def ajouter(self, produit_id: int, nom: str, brief: str) -> Projet:
        with self._connexion.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO projets_recherche (produit_id, nom, brief) VALUES (%s, %s, %s) RETURNING id, produit_id, nom, brief, cree_le",
                    (produit_id, nom, brief),
                )
            except psycopg2.errors.UniqueViolation as erreur:
                raise ProjetDejaExistant from erreur
            return Projet(*cur.fetchone())

    @avec_connexion
    def lister(self, produit_id: int) -> list[Projet]:
        with self._connexion.cursor() as cur:
            cur.execute(
                f"SELECT {_COLONNES_PROJET} FROM projets_recherche WHERE produit_id = %s ORDER BY cree_le DESC",
                (produit_id,),
            )
            return [Projet(*row) for row in cur.fetchall()]

    @avec_connexion
    def obtenir(self, id: int) -> Projet | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                f"SELECT {_COLONNES_PROJET} FROM projets_recherche WHERE id = %s",
                (id,),
            )
            row = cur.fetchone()
            return Projet(*row) if row else None

    @avec_connexion
    def supprimer(self, id: int) -> bool:
        with self._connexion.cursor() as cur:
            cur.execute("DELETE FROM projets_recherche WHERE id = %s", (id,))
            return cur.rowcount > 0

    @avec_connexion
    def ajouter_entretien(
        self,
        projet_id: int,
        participant: str,
        date_entretien: date,
        moderateur: str,
        contenu: str,
        note_moderateur: str,
    ) -> Entretien:
        with self._connexion.cursor() as cur:
            return _ajouter_entretien(
                cur,
                (
                    projet_id,
                    participant,
                    date_entretien,
                    moderateur,
                    contenu,
                    note_moderateur,
                ),
            )

    @avec_connexion
    def obtenir_entretien(self, projet_id: int, entretien_id: int) -> Entretien | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                f"SELECT {_COLONNES_ENTRETIEN} FROM transcripts WHERE projet_id = %s AND id = %s",
                (projet_id, entretien_id),
            )
            row = cur.fetchone()
            return Entretien(*row) if row else None

    @avec_connexion
    def ajouter_source(
        self,
        produit_id: int,
        projet_id: int | None,
        nom: str | None,
        brief: str,
        participant: str,
        date_entretien: date,
        moderateur: str,
        contenu: str,
        note_moderateur: str,
    ) -> SourceProjet:
        self._connexion.autocommit = False
        try:
            with self._connexion.cursor() as cur:
                if projet_id is None:
                    try:
                        cur.execute(
                            "INSERT INTO projets_recherche (produit_id, nom, brief) VALUES (%s, %s, %s) RETURNING id, produit_id, nom, brief, cree_le",
                            (produit_id, nom, brief),
                        )
                    except psycopg2.errors.UniqueViolation as erreur:
                        raise ProjetDejaExistant from erreur
                    projet = Projet(*cur.fetchone())
                else:
                    projet = _obtenir_projet(cur, projet_id)
                entretien = _ajouter_entretien(
                    cur,
                    (
                        projet.id,
                        participant,
                        date_entretien,
                        moderateur,
                        contenu,
                        note_moderateur,
                    ),
                )
            self._connexion.commit()
            return SourceProjet(projet, entretien)
        except Exception:
            self._connexion.rollback()
            raise

    @avec_connexion
    def lister_entretiens(self, projet_id: int) -> list[Entretien]:
        with self._connexion.cursor() as cur:
            cur.execute(
                f"SELECT {_COLONNES_ENTRETIEN} FROM transcripts WHERE projet_id = %s ORDER BY cree_le",
                (projet_id,),
            )
            return [Entretien(*row) for row in cur.fetchall()]

    @avec_connexion
    def enregistrer_scan(self, projet_id: int, brouillon: str) -> ScanProjet:
        with self._connexion.cursor() as cur:
            cur.execute(
                "INSERT INTO scans_projets (projet_id, brouillon) VALUES (%s, %s) ON CONFLICT (projet_id) DO UPDATE SET brouillon = EXCLUDED.brouillon, valide = NULL, modifie_le = NOW() RETURNING projet_id, brouillon, valide, cree_le, modifie_le",
                (projet_id, brouillon),
            )
            return ScanProjet(*cur.fetchone())

    @avec_connexion
    def obtenir_scan(self, projet_id: int) -> ScanProjet | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT projet_id, brouillon, valide, cree_le, modifie_le FROM scans_projets WHERE projet_id = %s",
                (projet_id,),
            )
            row = cur.fetchone()
            return ScanProjet(*row) if row else None

    @avec_connexion
    def modifier_scan(self, projet_id: int, brouillon: str) -> ScanProjet | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                "UPDATE scans_projets SET brouillon = %s, valide = NULL, modifie_le = NOW() WHERE projet_id = %s RETURNING projet_id, brouillon, valide, cree_le, modifie_le",
                (brouillon, projet_id),
            )
            row = cur.fetchone()
            return ScanProjet(*row) if row else None

    @avec_connexion
    def valider_scan(self, projet_id: int) -> ScanProjet | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                "UPDATE scans_projets SET valide = brouillon, modifie_le = NOW() WHERE projet_id = %s RETURNING projet_id, brouillon, valide, cree_le, modifie_le",
                (projet_id,),
            )
            row = cur.fetchone()
            return ScanProjet(*row) if row else None
