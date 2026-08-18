from configuration import charge_configuration
from infra.postgres.migrations import execute_migrations


def main() -> None:
    execute_migrations(charge_configuration().base_de_donnees)


if __name__ == "__main__":  # pragma: no cover
    main()
