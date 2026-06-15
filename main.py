import os, sys, signal, threading, logging
from src.config.loader import get_infrastructure, get_challenge
from src.model.components.components import Component
from src.model.manager import Manager

path = os.getcwd()
infra_path      = "./config/infrastructure.yaml"
setups_path     = "./config/challenge.yaml"
components_path = os.path.join(path, "components")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

_shutdown = threading.Event()


def _on_signal(signum, _frame):
    name = signal.Signals(signum).name
    if _shutdown.is_set():
        logger.warning("Second %s received — forcing immediate exit.", name)
        os._exit(130)
    logger.info("Received %s — graceful shutdown (press again to force).", name)
    _shutdown.set()


def main() -> int:
    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    infra = get_infrastructure(infra_path, components_path)
    challenge = get_challenge(setups_path)

    components = [Component(c) for c in infra.components]
    manager = Manager(components=components, devices=infra.devices)

    try:
        manager.setup(challenge.setups)
        if not _shutdown.is_set():
            manager.start()
            logger.info("All setups running. Waiting for shutdown signal...")
            while not _shutdown.wait(timeout=1.0):
                pass
    except Exception:
        logger.exception("Fatal error — tearing down.")
        return 1
    finally:
        logger.info("Shutting down: destroying networks and containers...")
        try:
            manager.destroy()
        except Exception:
            logger.exception("Errors occurred during cleanup.")
    return 0


if __name__ == "__main__":
    sys.exit(main())