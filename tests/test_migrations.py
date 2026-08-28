from pathlib import Path

from configuration import BaseDeDonnees
from infra.postgres import migrations
from infra.postgres import execute_migrations as script_migrations


class _Curseur:
    def __init__(self, executees: set[str]):
        self._executees = executees
        self._nom: str | None = None
        self.requetes: list[tuple[str, tuple | None]] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def execute(self, requete: str, parametres: tuple | None = None):
        self.requetes.append((requete, parametres))
        if requete.startswith("SELECT 1 FROM migrations_executees"):
            self._nom = parametres[0] if parametres else None
        if requete.startswith("INSERT INTO migrations_executees") and parametres:
            self._executees.add(parametres[0])

    def fetchone(self):
        return (1,) if self._nom in self._executees else None


class _Connexion:
    def __init__(self, curseur: _Curseur):
        self._curseur = curseur

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def cursor(self):
        return self._curseur


def test_execute_migrations_execute_une_seule_fois(monkeypatch, tmp_path):
    (tmp_path / "001_premiere.sql").write_text("SELECT 'premiere';", encoding="utf-8")
    (tmp_path / "002_seconde.sql").write_text("SELECT 'seconde';", encoding="utf-8")
    executees: set[str] = set()
    curseur = _Curseur(executees)
    monkeypatch.setattr(
        migrations.psycopg2,
        "connect",
        lambda **kwargs: _Connexion(curseur),
    )
    config = BaseDeDonnees("hote", 5432, "nom", "utilisateur", "mot-de-passe")

    assert migrations.execute_migrations(config, tmp_path) == [
        "001_premiere.sql",
        "002_seconde.sql",
    ]
    assert migrations.execute_migrations(config, tmp_path) == []
    assert executees == {"001_premiere.sql", "002_seconde.sql"}
    assert (
        "SELECT pg_advisory_xact_lock(%s)",
        (migrations.VERROU_MIGRATIONS,),
    ) in curseur.requetes


def test_script_execute_les_migrations(monkeypatch):
    config = BaseDeDonnees("hote", 5432, "nom", "utilisateur", "mot-de-passe")
    appels = []
    monkeypatch.setattr(
        script_migrations,
        "charge_configuration",
        lambda: type("ConfigurationDeTest", (), {"base_de_donnees": config})(),
    )
    monkeypatch.setattr(
        script_migrations,
        "execute_migrations",
        lambda base_de_donnees: appels.append(base_de_donnees),
    )

    script_migrations.main()

    assert appels == [config]


def test_refonte_mvp_reinitialise_et_recree_le_catalogue() -> None:
    contenu = (
        Path(__file__).parents[1] / "migrations" / "015_refonte_mvp_produits.sql"
    ).read_text()

    assert "TRUNCATE analyses" in contenu
    assert "retours_bizdev" in contenu
    assert "idees_featurebase" in contenu


def test_projets_uniques_reinitialise_la_base_locale() -> None:
    contenu = (
        Path(__file__).parents[1] / "migrations" / "016_projets_uniques_reset.sql"
    ).read_text()

    assert "TRUNCATE analyses" in contenu
    assert "scans_projets" in contenu
    assert "lower(btrim(nom))" in contenu
    assert "INSERT INTO produits (nom) VALUES ('MQC'), ('MSC'), ('MSS')" in contenu
