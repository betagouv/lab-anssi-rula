from dataclasses import dataclass

from besoins.depot import DepotBesoinsDetectes
from fonctionnalites.depot import DepotFonctionnalitesTranscripts
from fonctionnalites.service import ServiceFonctionnalites
from idees.depot import DepotIdees
from retours_bizdev.depot import DepotRetoursBizDev
from transcripts.depot import DepotTranscripts


@dataclass(frozen=True)
class DependancesBesoins:
    depot: DepotBesoinsDetectes
    depot_transcripts: DepotTranscripts
    depot_fonctionnalites: DepotFonctionnalitesTranscripts
    service_fonctionnalites: ServiceFonctionnalites
    depot_idees: DepotIdees
    depot_retours: DepotRetoursBizDev
