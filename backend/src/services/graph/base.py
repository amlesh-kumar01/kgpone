from abc import ABC, abstractmethod
from typing import Any


class BaseGraphBuilder(ABC):
    """
    Abstract contract for graph construction services.
    Implementations manage course nodes, concept nodes, and
    prerequisite relationships in a graph database.
    """

    @abstractmethod
    def add_course_node(self, course_code: str, title: str, academic_year: str) -> bool:
        """Adds or updates a Course node in the graph."""
        pass

    @abstractmethod
    def add_concept_node(self, name: str, course_code: str, description: str = "") -> bool:
        """Adds or updates a Concept node and links it to its parent Course."""
        pass

    @abstractmethod
    def link_prerequisite(self, concept_name: str, prerequisite_concept_name: str) -> bool:
        """Creates a HAS_PREREQUISITE relationship between two concepts."""
        pass


class BaseGraphQuerier(ABC):
    """
    Abstract contract for graph query services.
    Implementations traverse the graph to retrieve prerequisite
    chains and concept details.
    """

    @abstractmethod
    def get_prerequisites_recursive(self, concept_name: str) -> list[dict[str, Any]]:
        """
        Recursively retrieves all prerequisites for a given concept.

        Returns a list of dicts with keys:
            - source_concept: str
            - prereq_concept: str
            - course_code: str
            - description: str
        """
        pass

    @abstractmethod
    def get_concept_details(self, concept_name: str) -> dict[str, Any]:
        """Fetches details for a single concept node."""
        pass


class BasePrerequisiteDiagnoser(ABC):
    """
    Abstract contract for prerequisite diagnosis services.
    Implementations analyze a student query against the knowledge graph
    to detect missing foundational concepts from prerequisite courses.
    """

    @abstractmethod
    def diagnose_missing_prerequisites(
        self, query: str, active_course_code: str
    ) -> dict[str, Any]:
        """
        Scans a query for mentions of known concepts, walks the graph
        backwards, and returns missing prerequisite information.

        Returns a dict with keys:
            - missing_prerequisites: list of concept names
            - has_missing_prerequisites: bool
            - graph_visualization: dict with 'nodes' and 'edges' lists
            - prerequisite_links: list of link dicts
        """
        pass
