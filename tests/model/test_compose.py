import os


from schema.compose import parse, Service, Build, Port, Application

CWD = os.path.join(os.path.dirname(__file__), "..", "..")


def test_parse():
    dc = parse(
        os.path.join(CWD, "examples", "flask", "compose.yml"),
    )

    assert dc == Application(
        services=[
            Service(
                name="backend",
                build=Build(context="backend"),
                ports=[
                    Port(target=80, published=80),
                    Port(target=9229, published=9229),
                    Port(target=9230, published=9230),
                ],
            ),
            Service(name="db", build=None, ports=None),
            Service(
                name="frontend",
                build=Build(context="frontend"),
                ports=[Port(target=3000, published=3000)],
            ),
        ]
    )
