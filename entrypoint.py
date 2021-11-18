from arkitekt.actors.actify import define
from mikro import Representation
from yaml import dump, Dumper
import yaml


def hallok(nana: Representation) -> Representation:
    """Knacko

    generates hallo

    Args:
        nana (Representation): [description]

    Returns:
        Representation: [description]
    """
    print("nenewnew")


x = define(hallok)
with open(".port/definition.yaml", "w") as f:
    yaml.dump(x.dict(as_input=True), f)
