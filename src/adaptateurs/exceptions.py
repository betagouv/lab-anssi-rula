class ErreurAlbert(Exception):
    statut_http = 503
    detail_par_defaut = "Une erreur est survenue avec l'API Albert."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail_par_defaut
        super().__init__(self.detail)


class ErreurCommunicationAlbert(ErreurAlbert):
    detail_par_defaut = (
        "L'API Albert est indisponible. Réessayez dans quelques instants."
    )


class DelaiAlbertDepasse(ErreurCommunicationAlbert):
    detail_par_defaut = "L'API Albert n'a pas répondu dans le délai prévu. Réessayez dans quelques instants."


class ErreurHTTPAlbert(ErreurCommunicationAlbert):
    detail_par_defaut = (
        "L'API Albert a refusé la requête. Réessayez dans quelques instants."
    )


class ReponseAlbertInvalide(ErreurAlbert):
    statut_http = 502
    detail_par_defaut = "L'API Albert a renvoyé une réponse invalide."
