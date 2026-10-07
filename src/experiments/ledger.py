"""
src/experiments/ledger.py - Immutable Experiment Ledger & Multiple-Testing Audit Store.
Records every strategy variation, parameter combination, training/validation split,
and performance metric to allow rigorous Deflated Sharpe and PBO calculations.
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from src.contracts import ExperimentRecord


class ExperimentLedger:
    """SQLite-backed immutable quantitative experiment store."""

    def __init__(self, db_path: str = "data/experiments/experiment_ledger.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    strategy TEXT NOT NULL,
                    parameter_hash TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    feature_hash TEXT NOT NULL,
                    training_period TEXT NOT NULL,
                    validation_period TEXT NOT NULL,
                    oos_period TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    parent_experiment TEXT
                )
            """)
            conn.commit()

    @staticmethod
    def hash_dict(d: Dict[str, Any]) -> str:
        serialized = json.dumps(d, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def record_experiment(
        self,
        strategy: str,
        parameters: Dict[str, Any],
        training_period: str,
        validation_period: str,
        oos_period: str,
        metrics: Dict[str, float],
        parent_experiment: Optional[str] = None
    ) -> ExperimentRecord:
        param_hash = self.hash_dict(parameters)
        feature_hash = hashlib.sha256(f"{strategy}_{training_period}".encode("utf-8")).hexdigest()
        created_at = datetime.now(timezone.utc)
        experiment_id = f"EXP-{param_hash[:8]}-{int(created_at.timestamp())}"

        rec = ExperimentRecord(
            experiment_id=experiment_id,
            strategy=strategy,
            parameter_hash=param_hash,
            parameters=parameters,
            feature_hash=feature_hash,
            training_period=training_period,
            validation_period=validation_period,
            oos_period=oos_period,
            metrics=metrics,
            created_at_utc=created_at,
            parent_experiment=parent_experiment
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO experiments (
                    experiment_id, strategy, parameter_hash, parameters_json,
                    feature_hash, training_period, validation_period, oos_period,
                    metrics_json, created_at_utc, parent_experiment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rec.experiment_id,
                rec.strategy,
                rec.parameter_hash,
                json.dumps(rec.parameters),
                rec.feature_hash,
                rec.training_period,
                rec.validation_period,
                rec.oos_period,
                json.dumps(rec.metrics),
                rec.created_at_utc.isoformat(),
                rec.parent_experiment
            ))
            conn.commit()

        return rec

    def get_all_sharpes(self, strategy: Optional[str] = None) -> List[float]:
        """Retrieves historical Sharpe ratios across all tested variants for DSR multiple-testing."""
        with sqlite3.connect(self.db_path) as conn:
            if strategy:
                cur = conn.execute("SELECT metrics_json FROM experiments WHERE strategy = ?", (strategy,))
            else:
                cur = conn.execute("SELECT metrics_json FROM experiments")
            rows = cur.fetchall()

        sharpes = []
        for r in rows:
            m = json.loads(r[0])
            if "sharpe" in m:
                sharpes.append(float(m["sharpe"]))
            elif "oos_sharpe" in m:
                sharpes.append(float(m["oos_sharpe"]))
        return sharpes
