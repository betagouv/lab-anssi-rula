from datetime import datetime, timezone
from uuid import UUID

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


class DepotRapportsClaudeDeTest(DepotRapportsClaude):
    def __init__(self) -> None:
        self.sources: dict[int, SourceTranscriptClaude] = {}
        self.rapports: list[RapportClaude] = []
        self._prochain_id = 1

    def ajouter_source(self, source: SourceTranscriptClaude) -> None:
        self.sources[source.id] = source

    def lister_transcripts(
        self,
        produit_id: int | None,
        projet_id: int | None,
        type_source: str | None,
        statut: str,
        limite: int,
        curseur: int | None,
    ) -> tuple[list[TranscriptCatalogueClaude], int | None]:
        sources = [
            source
            for source in sorted(self.sources.values(), key=lambda item: item.id)
            if source.confirme
            and source.type_source in {"produit", "bizdev"}
            and (produit_id is None or source.produit_id == produit_id)
            and (projet_id is None or source.projet_id == projet_id)
            and (type_source is None or source.type_source == type_source)
            and (curseur is None or source.id > curseur)
        ]
        elements = [
            TranscriptCatalogueClaude(
                source.id,
                source.type_source,
                source.produit_id,
                source.projet_id,
                source.revision,
                sum(rapport.transcript_id == source.id for rapport in self.rapports),
                any(
                    rapport.transcript_id == source.id
                    and rapport.revision == source.revision
                    for rapport in self.rapports
                ),
                source.cree_le,
            )
            for source in sources
        ]
        elements = [
            element
            for element in elements
            if statut == "tous"
            or (statut == "analyses" and element.analyse_courante)
            or (statut == "non_analyses" and not element.analyse_courante)
        ]
        page = elements[:limite]
        return page, page[-1].id if len(elements) > limite else None

    def obtenir_source(self, transcript_id: int) -> SourceTranscriptClaude | None:
        return self.sources.get(transcript_id)

    def lister_rapports(
        self, transcript_id: int, limite: int, curseur: int | None
    ) -> tuple[list[RapportClaudeMetadonnees], int | None]:
        source = self.sources.get(transcript_id)
        rapports = [
            RapportClaudeMetadonnees(
                rapport.id,
                rapport.transcript_id,
                rapport.revision,
                rapport.cree_le,
                source is not None and rapport.revision == source.revision,
            )
            for rapport in self.rapports
            if rapport.transcript_id == transcript_id
            and (curseur is None or rapport.id > curseur)
        ]
        rapports.sort(key=lambda rapport: rapport.id)
        page = rapports[:limite]
        return page, page[-1].id if len(rapports) > limite else None

    def obtenir_rapport(self, rapport_id: int) -> RapportClaude | None:
        rapport = next((r for r in self.rapports if r.id == rapport_id), None)
        if rapport is None:
            return None
        source = self.sources.get(rapport.transcript_id)
        return rapport._replace(
            courant=source is not None and rapport.revision == source.revision
        )

    def enregistrer(
        self,
        transcript_id: int,
        revision: int,
        empreinte: str,
        cle_idempotence: UUID,
        contenu: str,
    ) -> RapportClaude:
        existant = next(
            (r for r in self.rapports if r.cle_idempotence == cle_idempotence), None
        )
        if existant is not None:
            source_existante = self.sources.get(existant.transcript_id)
            if source_existante is None:
                raise SourceIntrouvable
            if not source_existante.confirme or source_existante.type_source not in {
                "produit",
                "bizdev",
            }:
                raise SourceNonEligible
            if (
                existant.transcript_id,
                existant.revision,
                existant.empreinte,
                existant.contenu,
            ) != (transcript_id, revision, empreinte, contenu):
                raise ConflitIdempotence
            return existant._replace(
                courant=existant.revision == source_existante.revision
            )
        source = self.sources.get(transcript_id)
        if source is None:
            raise SourceIntrouvable
        if not source.confirme or source.type_source not in {"produit", "bizdev"}:
            raise SourceNonEligible
        if source.revision != revision or empreinte_source(source) != empreinte:
            raise SourceModifiee
        rapport = RapportClaude(
            self._prochain_id,
            transcript_id,
            revision,
            empreinte,
            datetime.now(timezone.utc),
            True,
            contenu,
            cle_idempotence,
        )
        self.rapports.append(rapport)
        self._prochain_id += 1
        return rapport
