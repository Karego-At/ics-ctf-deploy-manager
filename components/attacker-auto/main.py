import os, sys
from  src.config_loader import load_config
path = os.getcwd()
from src.scenarios import start_scenario
from src.constants import INTERFACE
config_path = "./config/config.yaml"



def main():
    cfg = load_config(config_path)
    start_scenario(cfg=cfg.scenario)
    INTERFACE = cfg.options.get("interface")
    # input()
    import time

    time.sleep(1000000000)
    while True:
        print("hello")


if __name__ == "__main__":
    sys.exit(main())