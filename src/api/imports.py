from fastapi import HTTPException

from validation_transcript.service import ServiceValidationTranscript


def verifier_import(
    contenu: str, confirmation: bool, validation: ServiceValidationTranscript
) -> None:
    if not confirmation:
        raise HTTPException(status_code=422, detail="Confirmation obligatoire")
    if not validation.valider(contenu).valide:
        raise HTTPException(status_code=422, detail="Contenu non conforme")
