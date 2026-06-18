import logging
from neo4j import GraphDatabase
from src.config.settings import Settings

logger = logging.getLogger("neo4j_config")

_driver = None
_has_failed = False

def get_neo4j_driver():
    """Initializes and returns the Neo4j driver singleton."""
    global _driver, _has_failed
    if _has_failed:
        return None
    if _driver is None:
        try:
            _driver = GraphDatabase.driver(
                Settings.NEO4J_URI,
                auth=(Settings.NEO4J_USER, Settings.NEO4J_PASSWORD),
                connection_timeout=3.0
            )
            # Verify connectivity
            _driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {Settings.NEO4J_URI}")
        except Exception as e:
            logger.warning(f"Failed to connect to Neo4j at {Settings.NEO4J_URI}: {e}. Repo will fall back to offline mode.")
            _driver = None
            _has_failed = True
    return _driver
