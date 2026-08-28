from datetime import datetime

from projets.analyse import ETAPES, BlocPrompt, DepotAnalyse, EtapeAnalyse


class DepotAnalyseMemoire(DepotAnalyse):
    def __init__(self, produits: dict[int, list[BlocPrompt]] | None = None) -> None:
        self.produits = produits or {}
        self.blocs: dict[int, list[BlocPrompt]] = {}
        self.etapes: dict[tuple[int, str], EtapeAnalyse] = {}

    def lister_blocs_produit(self, produit_id: int) -> list[BlocPrompt]:
        return list(self.produits.get(produit_id, []))

    def lister_blocs_projet(self, projet_id: int) -> list[BlocPrompt]:
        return list(self.blocs.get(projet_id, []))

    def enregistrer_configuration(
        self, projet_id: int, blocs: list[BlocPrompt]
    ) -> list[BlocPrompt]:
        if not self.blocs.get(projet_id):
            self.blocs[projet_id] = list(blocs)
        else:
            self.blocs[projet_id] = list(blocs)
        return list(self.blocs[projet_id])

    def initialiser_etapes(self, projet_id: int) -> list[EtapeAnalyse]:
        maintenant = datetime.now()
        for cle, libelle, ordre in ETAPES:
            self.etapes.setdefault(
                (projet_id, cle),
                EtapeAnalyse(
                    projet_id,
                    cle,
                    libelle,
                    ordre,
                    "",
                    None,
                    None,
                    "a_faire",
                    maintenant,
                    maintenant,
                ),
            )
        return self.lister_etapes(projet_id)

    def lister_etapes(self, projet_id: int) -> list[EtapeAnalyse]:
        return sorted(
            (etape for (id_projet, _), etape in self.etapes.items() if id_projet == projet_id),
            key=lambda etape: etape.ordre,
        )

    def obtenir_etape(self, projet_id: int, cle: str) -> EtapeAnalyse | None:
        return self.etapes.get((projet_id, cle))

    def enregistrer_etape(
        self, projet_id: int, cle: str, prompt: str, brouillon: str
    ) -> EtapeAnalyse:
        etape = self.etapes[(projet_id, cle)]
        resultat = etape._replace(
            prompt=prompt,
            brouillon=brouillon,
            valide=None,
            statut="brouillon",
            modifie_le=datetime.now(),
        )
        self.etapes[(projet_id, cle)] = resultat
        return resultat

    def modifier_etape(self, projet_id: int, cle: str, brouillon: str) -> EtapeAnalyse | None:
        etape = self.obtenir_etape(projet_id, cle)
        if not etape:
            return None
        resultat = etape._replace(
            brouillon=brouillon,
            valide=None,
            statut="brouillon",
            modifie_le=datetime.now(),
        )
        self.etapes[(projet_id, cle)] = resultat
        return resultat

    def valider_etape(self, projet_id: int, cle: str) -> EtapeAnalyse | None:
        etape = self.obtenir_etape(projet_id, cle)
        if not etape or etape.brouillon is None:
            return None
        resultat = etape._replace(
            valide=etape.brouillon,
            statut="validee",
            modifie_le=datetime.now(),
        )
        self.etapes[(projet_id, cle)] = resultat
        return resultat

    def invalider_etapes_suivantes(self, projet_id: int, ordre: int) -> None:
        for etape in self.lister_etapes(projet_id):
            if etape.ordre > ordre:
                self.etapes[(projet_id, etape.cle)] = etape._replace(
                    prompt="",
                    brouillon=None,
                    valide=None,
                    statut="a_faire",
                    modifie_le=datetime.now(),
                )
