from app.detection.base import AbstractDetector, DetectionContext


class MLDetector(AbstractDetector):
    """
    ML-based anomaly detection placeholder.
    Will be implemented with time-series anomaly detection models.
    """

    async def detect(
        self, records: list, context: DetectionContext
    ) -> list[dict]:
        raise NotImplementedError(
            "ML-based anomaly detection is not yet implemented. "
            "Use ThresholdDetector as the default strategy."
        )
