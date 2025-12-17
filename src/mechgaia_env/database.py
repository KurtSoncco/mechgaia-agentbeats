"""Database models and operations for MechGAIA benchmark."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.mechgaia_env.config import config


class BenchmarkDatabase:
    """SQLite database for storing tasks, instances, and evaluations."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or config.database_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                level TEXT NOT NULL CHECK(level IN ('A', 'B', 'C')),
                topic TEXT NOT NULL,
                schema_type TEXT NOT NULL,
                schema_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Task instances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_instances (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                parameters TEXT NOT NULL,
                gold_answer TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)

        # Evaluations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id TEXT PRIMARY KEY,
                task_instance_id TEXT NOT NULL,
                model_name TEXT NOT NULL,
                response TEXT NOT NULL,
                scores TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_instance_id) REFERENCES task_instances(id)
            )
        """)

        # Results table (aggregated)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                model_name TEXT NOT NULL,
                mean_score REAL NOT NULL,
                ci_lower REAL,
                ci_upper REAL,
                n_samples INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)

        conn.commit()
        conn.close()

    def add_task(
        self,
        task_id: str,
        level: str,
        topic: str,
        schema_type: str,
        schema_data: Dict[str, Any],
    ):
        """Add a task to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Ensure schema_data is JSON string
        if isinstance(schema_data, dict):
            schema_data_str = json.dumps(schema_data)
        else:
            schema_data_str = str(schema_data)

        cursor.execute(
            """
            INSERT OR REPLACE INTO tasks (id, level, topic, schema_type, schema_data)
            VALUES (?, ?, ?, ?, ?)
        """,
            (task_id, level, topic, schema_type, schema_data_str),
        )

        conn.commit()
        conn.close()

    def add_task_instance(
        self,
        instance_id: str,
        task_id: str,
        parameters: Dict[str, Any],
        gold_answer: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a task instance to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO task_instances 
            (id, task_id, parameters, gold_answer, metadata)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                instance_id,
                task_id,
                json.dumps(parameters),
                json.dumps(gold_answer),
                json.dumps(metadata or {}),
            ),
        )

        conn.commit()
        conn.close()

    def add_evaluation(
        self,
        eval_id: str,
        task_instance_id: str,
        model_name: str,
        response: Dict[str, Any],
        scores: Dict[str, float],
    ):
        """Add an evaluation result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO evaluations 
            (id, task_instance_id, model_name, response, scores)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                eval_id,
                task_instance_id,
                model_name,
                json.dumps(response),
                json.dumps(scores),
            ),
        )

        conn.commit()
        conn.close()

    def get_tasks_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Get all tasks for a given level."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM tasks WHERE level = ?
        """,
            (level,),
        )

        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            r = dict(row)
            # Parse schema_data if it's a JSON string
            if "schema_data" in r and isinstance(r["schema_data"], str):
                try:
                    r["schema_data"] = json.loads(r["schema_data"])
                except:
                    pass  # Keep as string if not valid JSON
            result.append(r)

        return result

    def get_task_instances(self, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get task instances, optionally filtered by task_id."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if task_id:
            cursor.execute(
                """
                SELECT ti.*, t.level 
                FROM task_instances ti
                JOIN tasks t ON ti.task_id = t.id
                WHERE ti.task_id = ?
            """,
                (task_id,),
            )
        else:
            cursor.execute("""
                SELECT ti.*, t.level 
                FROM task_instances ti
                JOIN tasks t ON ti.task_id = t.id
            """)

        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            r = dict(row)
            r["parameters"] = json.loads(r["parameters"])
            r["gold_answer"] = json.loads(r["gold_answer"])
            r["metadata"] = json.loads(r["metadata"])
            result.append(r)

        return result

    def get_evaluations(
        self, task_instance_id: Optional[str] = None, model_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get evaluations, optionally filtered."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions = []
        params = []

        if task_instance_id:
            conditions.append("task_instance_id = ?")
            params.append(task_instance_id)

        if model_name:
            conditions.append("model_name = ?")
            params.append(model_name)

        query = "SELECT * FROM evaluations"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            r = dict(row)
            r["response"] = json.loads(r["response"])
            r["scores"] = json.loads(r["scores"])
            result.append(r)

        return result

    def update_result(
        self,
        result_id: str,
        task_id: str,
        model_name: str,
        mean_score: float,
        ci_lower: float,
        ci_upper: float,
        n_samples: int,
    ):
        """Update aggregated result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO results 
            (id, task_id, model_name, mean_score, ci_lower, ci_upper, n_samples)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (result_id, task_id, model_name, mean_score, ci_lower, ci_upper, n_samples),
        )

        conn.commit()
        conn.close()
