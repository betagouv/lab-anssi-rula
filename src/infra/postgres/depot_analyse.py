from typing import Any

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from projets.analyse import ETAPES, BlocPrompt, DepotAnalyse, EtapeAnalyse


class DepotAnalysePostgres(DepotAnalyse):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def lister_blocs_produit(self, produit_id: int) -> list[BlocPrompt]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT cle, libelle, contenu, ordre FROM prompts_produits WHERE produit_id = %s ORDER BY ordre",
                (produit_id,),
            )
            return [BlocPrompt(*row) for row in cur.fetchall()]

    @avec_connexion
    def lister_blocs_projet(self, projet_id: int) -> list[BlocPrompt]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT cle, libelle, contenu, ordre FROM prompts_projets WHERE projet_id = %s ORDER BY ordre",
                (projet_id,),
            )
            return [BlocPrompt(*row) for row in cur.fetchall()]

    @avec_connexion
    def enregistrer_configuration(
        self, projet_id: int, blocs: list[BlocPrompt]
    ) -> list[BlocPrompt]:
        with self._connexion.cursor() as cur:
            cur.execute("DELETE FROM prompts_projets WHERE projet_id = %s", (projet_id,))
            cur.executemany(
                "INSERT INTO prompts_projets (projet_id, cle, libelle, contenu, ordre) VALUES (%s, %s, %s, %s, %s)",
                [(projet_id, bloc.cle, bloc.libelle, bloc.contenu, bloc.ordre) for bloc in blocs],
            )
        return blocs

    @avec_connexion
    def initialiser_etapes(self, projet_id: int) -> list[EtapeAnalyse]:
        with self._connexion.cursor() as cur:
            cur.executemany(
                "INSERT INTO etapes_analyses (projet_id, cle, libelle, ordre) VALUES (%s, %s, %s, %s) ON CONFLICT (projet_id, cle) DO NOTHING",
                [(projet_id, cle, libelle, ordre) for cle, libelle, ordre in ETAPES],
            )
        return self.lister_etapes(projet_id)

    @avec_connexion
    def lister_etapes(self, projet_id: int) -> list[EtapeAnalyse]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT projet_id, cle, libelle, ordre, prompt, brouillon, valide, statut, cree_le, modifie_le FROM etapes_analyses WHERE projet_id = %s ORDER BY ordre",
                (projet_id,),
            )
            return [EtapeAnalyse(*row) for row in cur.fetchall()]

    @avec_connexion
    def obtenir_etape(self, projet_id: int, cle: str) -> EtapeAnalyse | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT projet_id, cle, libelle, ordre, prompt, brouillon, valide, statut, cree_le, modifie_le FROM etapes_analyses WHERE projet_id = %s AND cle = %s",
                (projet_id, cle),
            )
            row = cur.fetchone()
            return EtapeAnalyse(*row) if row else None

    @avec_connexion
    def enregistrer_etape(
        self, projet_id: int, cle: str, prompt: str, brouillon: str
    ) -> EtapeAnalyse:
        with self._connexion.cursor() as cur:
            cur.execute(
                "UPDATE etapes_analyses SET prompt = %s, brouillon = %s, valide = NULL, statut = 'brouillon', modifie_le = NOW() WHERE projet_id = %s AND cle = %s RETURNING projet_id, cle, libelle, ordre, prompt, brouillon, valide, statut, cree_le, modifie_le",
                (prompt, brouillon, projet_id, cle),
            )
            return EtapeAnalyse(*cur.fetchone())

    @avec_connexion
    def modifier_etape(self, projet_id: int, cle: str, brouillon: str) -> EtapeAnalyse | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                "UPDATE etapes_analyses SET brouillon = %s, valide = NULL, statut = 'brouillon', modifie_le = NOW() WHERE projet_id = %s AND cle = %s RETURNING projet_id, cle, libelle, ordre, prompt, brouillon, valide, statut, cree_le, modifie_le",
                (brouillon, projet_id, cle),
            )
            row = cur.fetchone()
            return EtapeAnalyse(*row) if row else None

    @avec_connexion
    def valider_etape(self, projet_id: int, cle: str) -> EtapeAnalyse | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                "UPDATE etapes_analyses SET valide = brouillon, statut = 'validee', modifie_le = NOW() WHERE projet_id = %s AND cle = %s AND brouillon IS NOT NULL RETURNING projet_id, cle, libelle, ordre, prompt, brouillon, valide, statut, cree_le, modifie_le",
                (projet_id, cle),
            )
            row = cur.fetchone()
            return EtapeAnalyse(*row) if row else None

    @avec_connexion
    def invalider_etapes_suivantes(self, projet_id: int, ordre: int) -> None:
        with self._connexion.cursor() as cur:
            cur.execute(
                "UPDATE etapes_analyses SET prompt = '', brouillon = NULL, valide = NULL, statut = 'a_faire', modifie_le = NOW() WHERE projet_id = %s AND ordre > %s",
                (projet_id, ordre),
            )
