from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class DetectionContext:
    building_id: str
    thresholds: dict = field(default_factory=dict)


class AbstractDetector(ABC):
    """Abstract base class for anomaly detection strategies."""

    @abstractmethod
    async def detect(
        self, records: list, context: DetectionContext
    ) -> list[dict]:
        """
        Analyze records and return anomaly candidates.

        Each candidate is a dict with keys:
        - timestamp, anomaly_type, severity, metric_name,
          metric_value, threshold_value, description, detection_method
        """
        ...
