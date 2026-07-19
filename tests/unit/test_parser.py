import os

from compiler.parser import parse
from models.compose import Application

CWD = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def test_parse():
    actual = parse(
        os.path.join(CWD, "examples", "flask", "compose.yml"),
    )

    assert isinstance(actual, Application)
    assert "backend" in actual.services
    assert "db" in actual.services
    assert "frontend" in actual.services

    backend = actual.services["backend"]
    assert backend.build.context == "backend"
    assert any(p.target == 80 for p in backend.ports)
    assert backend.environment["DATABASE_HOST"] == "db"

    db = actual.services["db"]
    assert db.image == "mariadb:10.6.4-focal"
    assert db.environment["MYSQL_DATABASE"] == "example"
