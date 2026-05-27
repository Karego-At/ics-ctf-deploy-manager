import os, sys
from src.config.loader import get_infrastructure, get_challenge
from src.model.components import Component
from src.model.manager import Manager

path = os.getcwd()
infra_path      = "./config/infrastructure.yaml"
setups_path     = "./config/challenge.yaml"
components_path = os.path.join(path, "components")


def main():
    infra  = get_infrastructure(infra_path, components_path)
    challenge = get_challenge(setups_path)
    
    # setups = get_challenge(setups_path, infra) 

    components = [Component(c) for c in infra.components]
    manager = Manager(components=components, devices=infra.devices)

    manager.setup(challenge.setups)
    manager.start()
    input()
    manager.destroy()


if __name__ == "__main__":
    sys.exit(main())