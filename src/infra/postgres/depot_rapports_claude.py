from typing import Any
from uuid import UUID

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from rapports_claude.depot import (
    ConflitIdempotence,
    DepotRapportsClaude,
    RapportClaude,
    RapportClaudeMetadonnees,
    SourceIntrouvable,
    SourceModifiee,
    SourceNonEligible,
    SourceTranscriptClaude,
    TranscriptCatalogueClaude,
)
from rapports_claude.service import empreinte_source


class DepotRapportsClaudePostgres(DepotRapportsClaude):
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def lister_transcripts(
        self,
        produit_id: int | None,
        projet_id: int | None,
        type_source: str | None,
        statut: str,
        limite: int,
        curseur: int | None,
    ) -> tuple[list[TranscriptCatalogueClaude], int | None]:
        clauses = ["t.confirme", "t.type_source IN ('produit', 'bizdev')"]
        parametres: list[object] = []
        for valeur, colonne, operateur in (
            (produit_id, "t.produit_id", "="),
            (projet_id, "t.projet_id", "="),
            (type_source, "t.type_source", "="),
            (curseur, "t.id", ">"),
        ):
            if valeur is not None:
                clauses.append(f"{colonne} {operateur} %s")
                parametres.append(valeur)
        courant = "EXISTS (SELECT 1 FROM rapports_claude r WHERE r.transcript_id = t.id AND r.revision = t.revision_corpus)"
        if statut == "analyses":
            clauses.append(courant)
        elif statut == "non_analyses":
            clauses.append(f"NOT {courant}")
        parametres.append(limite + 1)
        with self._connexion.cursor() as cur:
            cur.execute(
                f"""SELECT t.id, t.type_source, t.produit_id, t.projet_id,
                           t.revision_corpus,
                           (SELECT COUNT(*) FROM rapports_claude r WHERE r.transcript_id = t.id),
                           {courant}, t.cree_le
                    FROM transcripts t
                    WHERE {" AND ".join(clauses)}
                    ORDER BY t.id ASC LIMIT %s""",
                parametres,
            )
            lignes = cur.fetchall()
        page = [TranscriptCatalogueClaude(*ligne) for ligne in lignes[:limite]]
        return page, page[-1].id if len(lignes) > limite and page else None

    @avec_connexion
    def obtenir_source(self, transcript_id: int) -> SourceTranscriptClaude | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                """SELECT id, type_source, produit_id, projet_id, revision_corpus,
                          confirme, contenu, contexte, locuteurs, cree_le
                   FROM transcripts WHERE id = %s""",
                (transcript_id,),
            )
            ligne = cur.fetchone()
        return SourceTranscriptClaude(*ligne) if ligne else None

    @avec_connexion
    def lister_rapports(
        self, transcript_id: int, limite: int, curseur: int | None
    ) -> tuple[list[RapportClaudeMetadonnees], int | None]:
        conditions = ["r.transcript_id = %s"]
        parametres: list[object] = [transcript_id]
        if curseur is not None:
            conditions.append("r.id > %s")
            parametres.append(curseur)
        parametres.append(limite + 1)
        with self._connexion.cursor() as cur:
            cur.execute(
                f"""SELECT r.id, r.transcript_id, r.revision,
                           r.cree_le, r.revision = t.revision_corpus
                    FROM rapports_claude r JOIN transcripts t ON t.id = r.transcript_id
                    WHERE {" AND ".join(conditions)} ORDER BY r.id ASC LIMIT %s""",
                parametres,
            )
            lignes = cur.fetchall()
        page = [RapportClaudeMetadonnees(*ligne) for ligne in lignes[:limite]]
        return page, page[-1].id if len(lignes) > limite and page else None

    @avec_connexion
    def obtenir_rapport(self, rapport_id: int) -> RapportClaude | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                """SELECT r.id, r.transcript_id, r.revision, r.empreinte,
                          r.cree_le, r.revision = t.revision_corpus,
                          r.contenu_markdown, r.cle_idempotence
                   FROM rapports_claude r JOIN transcripts t ON t.id = r.transcript_id
                   WHERE r.id = %s""",
                (rapport_id,),
            )
            ligne = cur.fetchone()
        return self._rapport(ligne) if ligne else None

    @avec_connexion
    def enregistrer(
        self,
        transcript_id: int,
        revision: int,
        empreinte: str,
        cle_idempotence: UUID,
        contenu: str,
    ) -> RapportClaude:
        with self._connexion.cursor() as cur:
            existant = self._par_cle(cur, cle_idempotence)
            if existant is not None:
                self._verifier_eligibilite(cur, existant.transcript_id)
                return self._verifier_rejeu(
                    existant, transcript_id, revision, empreinte, contenu
                )
            cur.execute(
                """SELECT id, type_source, produit_id, projet_id, revision_corpus,
                          confirme, contenu, contexte, locuteurs, cree_le
                   FROM transcripts WHERE id = %s FOR UPDATE""",
                (transcript_id,),
            )
            ligne_source = cur.fetchone()
            if ligne_source is None:
                raise SourceIntrouvable
            source = SourceTranscriptClaude(*ligne_source)
            if not source.confirme or source.type_source not in {"produit", "bizdev"}:
                raise SourceNonEligible
            existant = self._par_cle(cur, cle_idempotence)
            if existant is not None:
                self._verifier_eligibilite(cur, existant.transcript_id)
                return self._verifier_rejeu(
                    existant, transcript_id, revision, empreinte, contenu
                )
            if source.revision != revision or empreinte_source(source) != empreinte:
                raise SourceModifiee
            cur.execute(
                """INSERT INTO rapports_claude
                       (transcript_id, revision, empreinte, cle_idempotence, contenu_markdown)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (cle_idempotence) DO NOTHING
                   RETURNING id, transcript_id, revision, empreinte, cree_le,
                             TRUE, contenu_markdown, cle_idempotence""",
                (transcript_id, revision, empreinte, str(cle_idempotence), contenu),
            )
            ligne_rapport = cur.fetchone()
            if ligne_rapport is not None:
                return self._rapport(ligne_rapport)
            existant = self._par_cle(cur, cle_idempotence)
            if existant is None:
                raise ConflitIdempotence
            return self._verifier_rejeu(
                existant, transcript_id, revision, empreinte, contenu
            )

    def _par_cle(self, cur: Any, cle: UUID) -> RapportClaude | None:
        cur.execute(
            """SELECT r.id, r.transcript_id, r.revision, r.empreinte,
                      r.cree_le, r.revision = t.revision_corpus,
                      r.contenu_markdown, r.cle_idempotence
               FROM rapports_claude r JOIN transcripts t ON t.id = r.transcript_id
               WHERE r.cle_idempotence = %s""",
            (str(cle),),
        )
        ligne = cur.fetchone()
        return self._rapport(ligne) if ligne else None

    @staticmethod
    def _verifier_eligibilite(cur: Any, transcript_id: int) -> None:
        cur.execute(
            "SELECT confirme, type_source FROM transcripts WHERE id = %s",
            (transcript_id,),
        )
        ligne = cur.fetchone()
        if ligne is None:
            raise SourceIntrouvable
        if not ligne[0] or ligne[1] not in {"produit", "bizdev"}:
            raise SourceNonEligible

    @staticmethod
    def _rapport(ligne: tuple[Any, ...]) -> RapportClaude:
        return RapportClaude(
            ligne[0],
            ligne[1],
            ligne[2],
            ligne[3],
            ligne[4],
            ligne[5],
            ligne[6],
            UUID(str(ligne[7])),
        )

    @staticmethod
    def _verifier_rejeu(
        rapport: RapportClaude,
        transcript_id: int,
        revision: int,
        empreinte: str,
        contenu: str,
    ) -> RapportClaude:
        if (
            rapport.transcript_id,
            rapport.revision,
            rapport.empreinte,
            rapport.contenu,
        ) != (
            transcript_id,
            revision,
            empreinte,
            contenu,
        ):
            raise ConflitIdempotence
        return rapport
