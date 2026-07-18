import os

from main import parse
from schema.compose import Application, Build, Dependency, Port, Service

CWD = os.path.join(os.path.dirname(__file__), "", "..")


def test_parse():
    actual = parse(
        os.path.join(CWD, "examples", "flask", "compose.yml"),
    )

    expected = Application(
        services={
            "backend": Service(
                build=Build(context="backend"),
                ports=[
                    Port(target=80, published=80),
                    Port(target=9229, published=9229),
                    Port(target=9230, published=9230),
                ],
                environment={
                    "DATABASE_DB": "example",
                    "DATABASE_HOST": "db",
                    "DATABASE_PASSWORD": "/run/secrets/db-password",
                    "DATABASE_USER": "root",
                    "NODE_ENV": "development",
                },
                depends_on={
                    "db": Dependency(condition="service_started", required=True)
                },
            ),
            "db": Service(
                image="mariadb:10.6.4-focal",
                environment={
                    "MYSQL_DATABASE": "example",
                    "MYSQL_ROOT_PASSWORD_FILE": "/run/secrets/db-password",
                },
            ),
            "frontend": Service(
                build=Build(context="frontend"),
                ports=[Port(target=3000, published=3000)],
                depends_on={
                    "backend": Dependency(condition="service_started", required=True)
                },
            ),
        }
    )
    assert actual == expected
