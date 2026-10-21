from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import struct
from threading import Lock, Thread
import time
from typing import cast

import pytest

from adaptateurs.albert import AdaptateurAlbertReel
from adaptateurs.exceptions import (
    DelaiAlbertDepasse,
    ErreurCommunicationAlbert,
    ReponseAlbertInvalide,
)
from configuration import Albert


class ServeurAlbertLocal(ThreadingHTTPServer):
    def __init__(self, scenario: str):
        self.scenario = scenario
        self.requetes = 0
        self.debut_flux = 0.0
        self.verrou = Lock()
        super().__init__(("127.0.0.1", 0), GestionnaireAlbertLocal)


class GestionnaireAlbertLocal(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _envoyer(self, evenement: dict[str, object] | str) -> None:
        donnees = evenement if isinstance(evenement, str) else json.dumps(evenement)
        charge = f"data: {donnees}\n\n".encode()
        self.wfile.write(f"{len(charge):X}\r\n".encode() + charge + b"\r\n")
        self.wfile.flush()

    def do_POST(self) -> None:
        self.rfile.read(int(self.headers["Content-Length"]))
        serveur = cast(ServeurAlbertLocal, self.server)
        with serveur.verrou:
            serveur.requetes += 1
            numero = serveur.requetes
        scenario = serveur.scenario
        serveur.debut_flux = time.monotonic()
        if scenario == "http" and numero == 1:
            self.send_response(503)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if scenario == "invalid" and numero == 1:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            self._envoyer(
                {"choices": [{"delta": {"content": "{}"}, "finish_reason": "length"}]}
            )
            self._envoyer({"choices": [], "usage": {"completion_tokens": 2}})
            self.wfile.write(b"0\r\n\r\n")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        if scenario == "active":
            while time.monotonic() < serveur.debut_flux + 1.5:
                self._envoyer({"choices": [{"delta": {}, "finish_reason": None}]})
                time.sleep(0.1)
            return
        if scenario not in {"drop_once", "drop_once_slow"} or numero == 1:
            self._envoyer(
                {
                    "choices": [
                        {
                            "delta": {"reasoning": "fragment partiel"},
                            "finish_reason": None,
                        }
                    ]
                }
            )
        if (
            scenario == "slow"
            or (scenario == "drop_once_slow" and numero == 1)
            or (scenario == "drop_once" and numero == 1)
            or scenario == "drop_twice"
        ):
            if scenario == "slow":
                time.sleep(2)
            elif scenario == "drop_once_slow":
                time.sleep(0.65)
            else:
                time.sleep(0.05)
            self.close_connection = True
            self.connection.setsockopt(
                socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0)
            )
            self.connection.close()
            return
        if scenario in {"drop_once_slow", "slow_success"}:
            time.sleep(0.65)
        self._envoyer(
            {"choices": [{"delta": {"content": "{}"}, "finish_reason": None}]}
        )
        self._envoyer(
            {
                "choices": [{"delta": {}, "finish_reason": "stop"}],
                "usage": {"completion_tokens": 4},
            }
        )
        self._envoyer("[DONE]")
        self.wfile.write(b"0\r\n\r\n")


@pytest.fixture
def serveur_albert(request: pytest.FixtureRequest):
    serveur = ServeurAlbertLocal(request.param)
    thread = Thread(target=serveur.serve_forever)
    thread.start()
    try:
        yield serveur
    finally:
        serveur.shutdown()
        thread.join()
        serveur.server_close()


def _adaptateur(
    serveur: ServeurAlbertLocal, delai: int = 10, delai_http: int = 5
) -> AdaptateurAlbertReel:
    return AdaptateurAlbertReel(
        Albert(
            url=f"http://127.0.0.1:{serveur.server_port}",
            cle_api="test",
            modele="modele-test",
            delai_transcripts=delai_http,
            delai_preparation_transcripts=delai,
        )
    )


def _completer(adaptateur: AdaptateurAlbertReel) -> str:
    return adaptateur.completer_json_raisonnement_preparation(
        [{"role": "user", "content": "test"}], "schema-test", {}, "high"
    )


@pytest.mark.parametrize("serveur_albert", ["drop_once"], indirect=True)
def test_reprend_un_flux_interrompu_et_ne_garde_pas_le_raisonnement_partiel(
    serveur_albert: ServeurAlbertLocal,
) -> None:
    adaptateur = _adaptateur(serveur_albert)

    assert _completer(adaptateur) == "{}"
    assert serveur_albert.requetes == 2
    assert adaptateur.metriques_dernier_flux["tentatives"] == 2
    assert adaptateur.metriques_dernier_flux["retry_cause_type"] == "ReadError"
    assert adaptateur.metriques_dernier_flux["raisonnement_caracteres"] == 0
    assert adaptateur.metriques_dernier_flux["contenu_caracteres"] == 2
    assert adaptateur.metriques_dernier_flux["finish_reason"] == "stop"


@pytest.mark.parametrize("serveur_albert", ["drop_once_slow"], indirect=True)
def test_reprise_recoit_un_delai_independant(
    serveur_albert: ServeurAlbertLocal,
) -> None:
    adaptateur = _adaptateur(serveur_albert, delai=1)
    debut = time.monotonic()

    assert _completer(adaptateur) == "{}"

    assert time.monotonic() - debut > 1
    assert serveur_albert.requetes == 2
    assert adaptateur.metriques_dernier_flux["tentatives"] == 2
    assert adaptateur.metriques_dernier_flux["retry_cause_type"] == "ReadError"
    assert cast(float, adaptateur.metriques_dernier_flux["duree_tentative_s"]) < 1
    assert cast(float, adaptateur.metriques_dernier_flux["duree_totale_s"]) > 1


@pytest.mark.parametrize("serveur_albert", ["drop_twice"], indirect=True)
def test_ne_fait_pas_de_troisieme_tentative_apres_une_seconde_coupure(
    serveur_albert: ServeurAlbertLocal,
) -> None:
    adaptateur = _adaptateur(serveur_albert)

    with pytest.raises(ErreurCommunicationAlbert) as erreur:
        _completer(adaptateur)

    assert type(erreur.value.__cause__).__name__ == "ReadError"
    assert serveur_albert.requetes == 2
    assert adaptateur.metriques_dernier_flux["tentatives"] == 2


@pytest.mark.parametrize("serveur_albert", ["http"], indirect=True)
def test_ne_reessaie_pas_une_erreur_http(serveur_albert: ServeurAlbertLocal) -> None:
    adaptateur = _adaptateur(serveur_albert)

    with pytest.raises(ErreurCommunicationAlbert):
        _completer(adaptateur)

    assert serveur_albert.requetes == 1
    assert adaptateur.metriques_dernier_flux["tentatives"] == 1
    assert adaptateur.metriques_dernier_flux["statut_http"] == 503


@pytest.mark.parametrize("serveur_albert", ["invalid"], indirect=True)
def test_ne_reessaie_pas_une_reponse_albert_invalide(
    serveur_albert: ServeurAlbertLocal,
) -> None:
    adaptateur = _adaptateur(serveur_albert)

    with pytest.raises(ReponseAlbertInvalide):
        _completer(adaptateur)

    assert serveur_albert.requetes == 1
    assert adaptateur.metriques_dernier_flux["tentatives"] == 1


@pytest.mark.parametrize("serveur_albert", ["slow"], indirect=True)
def test_timeout_de_tentative_interrompt_sans_reprise(
    serveur_albert: ServeurAlbertLocal,
) -> None:
    adaptateur = _adaptateur(serveur_albert, delai=1)
    debut = time.monotonic()

    with pytest.raises(DelaiAlbertDepasse) as erreur:
        _completer(adaptateur)

    assert time.monotonic() - debut < 1.6
    assert serveur_albert.requetes == 1
    assert adaptateur.metriques_dernier_flux["tentatives"] == 1
    assert adaptateur.metriques_dernier_flux["delai_tentative_s"] == 1
    assert (
        0.9
        <= cast(float, adaptateur.metriques_dernier_flux["duree_tentative_s"])
        <= 1.2
    )
    assert erreur.value.diagnostic["delai_tentative_s"] == 1
    assert 0.9 <= cast(float, erreur.value.diagnostic["duree_tentative_s"]) <= 1.2
    assert erreur.value.detail == "L'API Albert n'a pas répondu dans le délai imparti."


@pytest.mark.parametrize("serveur_albert", ["active"], indirect=True)
def test_timeout_interrompt_un_flux_sse_actif(
    serveur_albert: ServeurAlbertLocal,
) -> None:
    adaptateur = _adaptateur(serveur_albert, delai=1, delai_http=5)

    with pytest.raises(DelaiAlbertDepasse):
        _completer(adaptateur)

    assert serveur_albert.requetes == 1
    assert cast(int, adaptateur.metriques_dernier_flux["evenements"]) > 1


@pytest.mark.parametrize("serveur_albert", ["slow_success"], indirect=True)
def test_appels_independants_peuvent_depasse_le_delai_cumule(
    serveur_albert: ServeurAlbertLocal,
) -> None:
    adaptateur = _adaptateur(serveur_albert, delai=1)
    debut = time.monotonic()

    assert _completer(adaptateur) == "{}"
    assert _completer(adaptateur) == "{}"

    assert time.monotonic() - debut > 1
    assert serveur_albert.requetes == 2
    assert adaptateur.metriques_dernier_flux["tentatives"] == 1
    assert cast(float, adaptateur.metriques_dernier_flux["duree_tentative_s"]) < 1
