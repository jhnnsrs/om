from arkitekt.actors.actify import define
from mikro import Representation
from yaml import dump, Dumper
import yaml


def hallo(nana: Representation) -> Representation:
    """Hallo

    generates hallo

    Args:
        nana (Representation): [description]

    Returns:
        Representation: [description]
    """
    print("nenewnew")


x = define(hallo)
with open(".port/definition.yaml", "w") as f:
    yaml.dump(x.dict(as_input=True), f)
