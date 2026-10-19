import hashlib
import json
from typing import Any
from uuid import UUID

from rapports_claude.depot import (
    DepotRapportsClaude,
    EntreeInvalide,
    RapportClaude,
    RapportIntrouvable,
    RapportClaudeMetadonnees,
    SourceTranscriptClaude,
    SourceIntrouvable,
    SourceModifiee,
    SourceNonEligible,
    TranscriptCatalogueClaude,
)

TAILLE_PAGE_DEFAUT = 20
TAILLE_PAGE_MAXIMALE = 100
TAILLE_BLOC = 30000
TAILLE_RAPPORT_MAXIMALE = 200000


class ServiceRapportsClaude:
    def __init__(self, depot: DepotRapportsClaude) -> None:
        self._depot = depot

    def lister_transcripts(
        self,
        produit_id: int | None = None,
        projet_id: int | None = None,
        type_source: str | None = None,
        statut: str = "tous",
        limite: int = TAILLE_PAGE_DEFAUT,
        curseur: int | None = None,
    ) -> tuple[list[TranscriptCatalogueClaude], int | None]:
        if not 1 <= limite <= TAILLE_PAGE_MAXIMALE:
            raise EntreeInvalide
        if statut not in {"tous", "analyses", "non_analyses"}:
            raise EntreeInvalide
        if type_source not in {None, "produit", "bizdev"}:
            raise EntreeInvalide
        return self._depot.lister_transcripts(
            produit_id, projet_id, type_source, statut, limite, curseur
        )

    def lire_source(
        self,
        transcript_id: int,
        offset: int = 0,
        revision: int | None = None,
        empreinte: str | None = None,
    ) -> dict[str, Any]:
        if offset > 0 and (revision is None or empreinte is None):
            raise EntreeInvalide
        source = self._depot.obtenir_source(transcript_id)
        if source is None:
            raise SourceIntrouvable
        if not source.confirme or source.type_source not in {"produit", "bizdev"}:
            raise SourceNonEligible
        empreinte_courante = empreinte_source(source)
        if revision is not None and revision != source.revision:
            raise SourceModifiee
        if empreinte is not None and empreinte != empreinte_courante:
            raise SourceModifiee
        if offset < 0:
            raise EntreeInvalide
        contenu = f"Contexte\n{source.contexte}\n\n--- Transcript ---\n{source.contenu}"
        if offset > len(contenu):
            raise EntreeInvalide
        return {
            "transcript_id": source.id,
            "type_source": source.type_source,
            "produit_id": source.produit_id,
            "projet_id": source.projet_id,
            "revision": source.revision,
            "empreinte": empreinte_courante,
            "longueur_totale": len(contenu),
            "offset": offset,
            "bloc": contenu[offset : offset + TAILLE_BLOC],
            "offset_suivant": (
                min(offset + TAILLE_BLOC, len(contenu))
                if offset + TAILLE_BLOC < len(contenu)
                else None
            ),
        }

    def lister_rapports(
        self,
        transcript_id: int,
        limite: int = TAILLE_PAGE_DEFAUT,
        curseur: int | None = None,
    ) -> tuple[list[RapportClaudeMetadonnees], int | None]:
        if not 1 <= limite <= TAILLE_PAGE_MAXIMALE:
            raise EntreeInvalide
        source = self._depot.obtenir_source(transcript_id)
        if source is None:
            raise SourceIntrouvable
        if not source.confirme or source.type_source not in {"produit", "bizdev"}:
            raise SourceNonEligible
        return self._depot.lister_rapports(transcript_id, limite, curseur)

    def lire_rapport(self, rapport_id: int, offset: int = 0) -> dict[str, Any]:
        rapport = self._depot.obtenir_rapport(rapport_id)
        if rapport is None:
            raise RapportIntrouvable
        source = self._depot.obtenir_source(rapport.transcript_id)
        if source is None:
            raise RapportIntrouvable
        if not source.confirme or source.type_source not in {"produit", "bizdev"}:
            raise SourceNonEligible
        if offset < 0 or offset > len(rapport.contenu):
            raise EntreeInvalide
        return {
            "rapport_id": rapport.id,
            "transcript_id": rapport.transcript_id,
            "revision": rapport.revision,
            "cree_le": rapport.cree_le,
            "courant": rapport.revision == source.revision,
            "longueur_totale": len(rapport.contenu),
            "offset": offset,
            "bloc": rapport.contenu[offset : offset + TAILLE_BLOC],
            "offset_suivant": (
                min(offset + TAILLE_BLOC, len(rapport.contenu))
                if offset + TAILLE_BLOC < len(rapport.contenu)
                else None
            ),
        }

    def enregistrer_analyse(
        self,
        transcript_id: int,
        revision: int,
        empreinte: str,
        cle_idempotence: UUID,
        contenu: str,
    ) -> RapportClaude:
        if not contenu.strip() or len(contenu) > TAILLE_RAPPORT_MAXIMALE:
            raise EntreeInvalide
        return self._depot.enregistrer(
            transcript_id, revision, empreinte, cle_idempotence, contenu
        )


def empreinte_source(source: SourceTranscriptClaude) -> str:
    valeur = {
        "type_source": source.type_source,
        "contenu": source.contenu,
        "contexte": source.contexte,
        "locuteurs": source.locuteurs,
    }
    canonique = json.dumps(
        valeur, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonique.encode("utf-8")).hexdigest()
