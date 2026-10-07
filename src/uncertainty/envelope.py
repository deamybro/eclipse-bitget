"""
src/uncertainty/envelope.py - Edge Envelope Construction & Signal Eligibility Gate.
Enforces that only signals exceeding empirical uncertainty + execution costs
receive capital eligibility.
"""

from src.contracts import EdgeEnvelope, DataQuality
from src.uncertainty.conformal import SequentialConformalCalibrator


class EdgeEnvelopeWrapper:
    """Wraps raw model alpha point estimates into calibrated uncertainty envelopes."""

    def __init__(self, coverage_target: float = 0.90):
        self.calibrators: dict[str, SequentialConformalCalibrator] = {}
        self.coverage_target = coverage_target

    def get_or_create_calibrator(self, key: str) -> SequentialConformalCalibrator:
        if key not in self.calibrators:
            self.calibrators[key] = SequentialConformalCalibrator(coverage_target=self.coverage_target)
        return self.calibrators[key]

    def build_envelope(
        self,
        key: str,
        point_edge: float,
        latest_realized_error: float | None = None
    ) -> EdgeEnvelope:
        calibrator = self.get_or_create_calibrator(key)
        if latest_realized_error is not None:
            calibrator.update(latest_realized_error)

        lower, upper, width, is_calibrated = calibrator.compute_interval(point_edge)

        return EdgeEnvelope(
            point_edge=point_edge,
            lower_edge=lower,
            upper_edge=upper,
            interval_width=width,
            coverage_target=self.coverage_target,
            calibration_sample_count=len(calibrator.past_errors),
            quality=DataQuality.DERIVED if is_calibrated else DataQuality.MODELLED
        )
