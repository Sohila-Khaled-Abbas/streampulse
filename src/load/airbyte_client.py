"""Airbyte Programmatic Automation Client & Replication Orchestrator.

Provides an interface to manage and trigger Airbyte (v0.50+) ELT connections
via the REST API, with automated health checks, source/destination provisioning,
sync triggering, job monitoring, and fallback execution.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.auth import HTTPBasicAuth

from src.utils.config import settings
from src.utils.db import db_manager
from src.utils.logger import logger


class AirbyteClient:
    """Automates Airbyte configuration, connection setup, and sync execution via REST API."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 15,
    ) -> None:
        self.host = host or settings.airbyte_host
        self.port = port or settings.airbyte_port
        self.username = username or settings.airbyte_username
        self.password = password or settings.airbyte_password
        self.timeout = timeout

        self.base_url = f"http://{self.host}:{self.port}/api/v1"
        self.public_url = f"http://{self.host}:{self.port}/api/public/v1"
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # -------------------------------------------------------------------------
    # 1. Health & Readiness Checks
    # -------------------------------------------------------------------------
    def check_health(self) -> Dict[str, Any]:
        """Check if Airbyte API and server containers are online and responding."""
        endpoints = [
            f"{self.base_url}/health",
            f"http://{self.host}:{self.port}/api/v1/health",
            f"http://{self.host}:{self.port}/health",
        ]
        for url in endpoints:
            try:
                resp = requests.get(url, auth=self.auth, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json() if resp.text else {}
                    logger.info(f"Airbyte Health Check OK at {url} (status={resp.status_code})")
                    return {"available": True, "status_code": resp.status_code, "data": data, "url": url}
            except Exception as err:
                logger.debug(f"Health check attempt on {url} failed: {err}")

        logger.warning(f"Airbyte server is currently unreachable at {self.host}:{self.port}")
        return {"available": False, "status_code": None, "data": None, "url": self.base_url}

    # -------------------------------------------------------------------------
    # 2. Workspace Management
    # -------------------------------------------------------------------------
    def get_or_create_workspace(self, workspace_name: str = "StreamPulse") -> Optional[str]:
        """Fetch existing workspace ID or create a new workspace."""
        try:
            resp = requests.post(
                f"{self.base_url}/workspaces/list",
                auth=self.auth,
                headers=self.headers,
                json={},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                workspaces = resp.json().get("workspaces", [])
                if workspaces:
                    # Return first existing or matching workspace
                    for ws in workspaces:
                        if ws.get("name") == workspace_name:
                            return ws.get("workspaceId")
                    return workspaces[0].get("workspaceId")

            # Create if none exists
            create_resp = requests.post(
                f"{self.base_url}/workspaces/create",
                auth=self.auth,
                headers=self.headers,
                json={"name": workspace_name, "email": "admin@streampulse.io"},
                timeout=self.timeout,
            )
            if create_resp.status_code in (200, 201):
                ws_id = create_resp.json().get("workspaceId")
                logger.info(f"Created Airbyte workspace: {workspace_name} (ID: {ws_id})")
                return ws_id
        except Exception as err:
            logger.error(f"Error querying/creating Airbyte workspace: {err}")
        return None

    # -------------------------------------------------------------------------
    # 3. Source Provisioning
    # -------------------------------------------------------------------------
    def get_or_create_source(
        self,
        workspace_id: str,
        source_name: str = "StreamPulse_Daily_2026_Catalog",
        file_path: str = "data/processed/netflix_catalog_enriched_master.csv",
    ) -> Optional[str]:
        """Find or create File (CSV) source in Airbyte."""
        try:
            # 1. List existing sources
            resp = requests.post(
                f"{self.base_url}/sources/list",
                auth=self.auth,
                headers=self.headers,
                json={"workspaceId": workspace_id},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                for src in resp.json().get("sources", []):
                    if src.get("name") == source_name:
                        logger.info(f"Found existing Airbyte source '{source_name}' (ID: {src.get('sourceId')})")
                        return src.get("sourceId")

            # 2. Lookup File source definition ID
            def_resp = requests.post(
                f"{self.base_url}/source_definitions/list",
                auth=self.auth,
                headers=self.headers,
                json={},
                timeout=self.timeout,
            )
            file_def_id = None
            if def_resp.status_code == 200:
                for definition in def_resp.json().get("sourceDefinitions", []):
                    if "file" in definition.get("name", "").lower():
                        file_def_id = definition.get("sourceDefinitionId")
                        break

            if not file_def_id:
                file_def_id = "778daa7c-bee5-4ab6-8acb-80058b76be0d"  # Standard Airbyte File Source ID

            # 3. Create Source
            abs_path = os.path.abspath(file_path)
            payload = {
                "workspaceId": workspace_id,
                "name": source_name,
                "sourceDefinitionId": file_def_id,
                "connectionConfiguration": {
                    "url": abs_path,
                    "format": "csv",
                    "provider": {
                        "storage": "local"
                    },
                    "reader_options": json.dumps({"encoding": "utf-8"}),
                },
            }
            create_resp = requests.post(
                f"{self.base_url}/sources/create",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            if create_resp.status_code in (200, 201):
                src_id = create_resp.json().get("sourceId")
                logger.info(f"Created Airbyte source '{source_name}' (ID: {src_id})")
                return src_id
        except Exception as err:
            logger.error(f"Error configuring Airbyte source: {err}")
        return None

    # -------------------------------------------------------------------------
    # 4. Destination Provisioning
    # -------------------------------------------------------------------------
    def get_or_create_destination(
        self,
        workspace_id: str,
        dest_name: str = "StreamPulse_PostgreSQL_Warehouse",
        db_host: str = "host.docker.internal",
        db_port: int = 5432,
        db_name: str = "streampulse",
        db_user: str = "postgres",
        db_password: str = "postgres",
        default_schema: str = "staging",
    ) -> Optional[str]:
        """Find or create PostgreSQL destination in Airbyte."""
        try:
            # 1. List existing destinations
            resp = requests.post(
                f"{self.base_url}/destinations/list",
                auth=self.auth,
                headers=self.headers,
                json={"workspaceId": workspace_id},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                for dest in resp.json().get("destinations", []):
                    if dest.get("name") == dest_name:
                        logger.info(f"Found existing Airbyte destination '{dest_name}' (ID: {dest.get('destinationId')})")
                        return dest.get("destinationId")

            # 2. Lookup Postgres destination definition ID
            def_resp = requests.post(
                f"{self.base_url}/destination_definitions/list",
                auth=self.auth,
                headers=self.headers,
                json={},
                timeout=self.timeout,
            )
            pg_def_id = None
            if def_resp.status_code == 200:
                for definition in def_resp.json().get("destinationDefinitions", []):
                    if "postgres" in definition.get("name", "").lower():
                        pg_def_id = definition.get("destinationDefinitionId")
                        break

            if not pg_def_id:
                pg_def_id = "25c5221d-dce2-4163-ade9-739ef790f503"  # Standard Airbyte Postgres Destination ID

            # 3. Create Destination
            payload = {
                "workspaceId": workspace_id,
                "name": dest_name,
                "destinationDefinitionId": pg_def_id,
                "connectionConfiguration": {
                    "host": db_host,
                    "port": db_port,
                    "database": db_name,
                    "username": db_user,
                    "password": db_password,
                    "schema": default_schema,
                    "ssl_mode": {"mode": "disable"},
                },
            }
            create_resp = requests.post(
                f"{self.base_url}/destinations/create",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            if create_resp.status_code in (200, 201):
                dest_id = create_resp.json().get("destinationId")
                logger.info(f"Created Airbyte destination '{dest_name}' (ID: {dest_id})")
                return dest_id
        except Exception as err:
            logger.error(f"Error configuring Airbyte destination: {err}")
        return None

    # -------------------------------------------------------------------------
    # 5. Connection Setup & Replication
    # -------------------------------------------------------------------------
    def get_or_create_connection(
        self,
        workspace_id: str,
        source_id: str,
        destination_id: str,
        connection_name: str = "Daily_2026_Catalog_to_Staging",
    ) -> Optional[str]:
        """Find or create replication connection between source and destination."""
        try:
            # 1. List connections
            resp = requests.post(
                f"{self.base_url}/connections/list",
                auth=self.auth,
                headers=self.headers,
                json={"workspaceId": workspace_id},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                for conn in resp.json().get("connections", []):
                    if conn.get("name") == connection_name:
                        logger.info(f"Found existing connection '{connection_name}' (ID: {conn.get('connectionId')})")
                        return conn.get("connectionId")

            # 2. Discover Catalog from Source
            cat_resp = requests.post(
                f"{self.base_url}/sources/discover_schema",
                auth=self.auth,
                headers=self.headers,
                json={"sourceId": source_id},
                timeout=self.timeout,
            )
            sync_catalog = cat_resp.json().get("catalog") if cat_resp.status_code == 200 else None

            # 3. Create Connection
            payload = {
                "name": connection_name,
                "sourceId": source_id,
                "destinationId": destination_id,
                "status": "active",
                "prefix": "stg_",
                "namespaceDefinition": "destination",
            }
            if sync_catalog:
                payload["syncCatalog"] = sync_catalog

            create_resp = requests.post(
                f"{self.base_url}/connections/create",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            if create_resp.status_code in (200, 201):
                conn_id = create_resp.json().get("connectionId")
                logger.info(f"Created Airbyte connection '{connection_name}' (ID: {conn_id})")
                return conn_id
        except Exception as err:
            logger.error(f"Error creating Airbyte connection: {err}")
        return None

    # -------------------------------------------------------------------------
    # 6. Trigger Sync & Monitor
    # -------------------------------------------------------------------------
    def trigger_sync(self, connection_id: str) -> Dict[str, Any]:
        """Trigger an immediate sync on an existing connection."""
        try:
            resp = requests.post(
                f"{self.base_url}/connections/sync",
                auth=self.auth,
                headers=self.headers,
                json={"connectionId": connection_id},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                job_data = resp.json().get("job", {})
                job_id = job_data.get("id")
                logger.info(f"Successfully triggered Airbyte sync for connection {connection_id} (Job ID: {job_id})")
                return {"success": True, "job_id": job_id, "job_data": job_data}
            else:
                logger.error(f"Failed to trigger sync: {resp.status_code} - {resp.text}")
                return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as err:
            logger.error(f"Exception triggering Airbyte sync: {err}")
            return {"success": False, "error": str(err)}

    def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """Poll the execution status of a sync job."""
        try:
            resp = requests.post(
                f"{self.base_url}/jobs/get",
                auth=self.auth,
                headers=self.headers,
                json={"id": job_id},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                job = resp.json().get("job", {})
                return {
                    "status": job.get("status"),  # 'running', 'succeeded', 'failed', 'cancelled'
                    "records_synced": job.get("recordsSynced", 0),
                    "bytes_synced": job.get("bytesSynced", 0),
                    "created_at": job.get("createdAt"),
                    "updated_at": job.get("updatedAt"),
                }
        except Exception as err:
            logger.error(f"Error fetching job status: {err}")
        return {"status": "unknown"}

    def sync_and_wait(
        self,
        connection_id: str,
        timeout_seconds: int = 180,
        poll_interval: int = 4,
    ) -> Dict[str, Any]:
        """Trigger replication sync and block until completion or timeout."""
        trigger_res = self.trigger_sync(connection_id)
        if not trigger_res.get("success"):
            return trigger_res

        job_id = trigger_res.get("job_id")
        if not job_id:
            return {"success": False, "error": "No Job ID returned from trigger."}

        logger.info(f"Monitoring Airbyte Sync Job #{job_id} (Timeout: {timeout_seconds}s)...")
        elapsed = 0
        while elapsed < timeout_seconds:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_info = self.get_job_status(job_id)
            current_status = status_info.get("status")
            logger.info(f" - [Airbyte Job #{job_id}] Status: {current_status} ({elapsed}s elapsed)")

            if current_status == "succeeded":
                logger.info(f"[SUCCESS] Airbyte Sync Job #{job_id} completed successfully!")
                return {"success": True, "job_id": job_id, "details": status_info}
            elif current_status in ("failed", "cancelled"):
                logger.error(f"[FAILED] Airbyte Sync Job #{job_id} failed with status: {current_status}")
                return {"success": False, "job_id": job_id, "status": current_status, "details": status_info}

        logger.warning(f"Sync Job #{job_id} timed out after {timeout_seconds} seconds.")
        return {"success": False, "job_id": job_id, "status": "timeout"}

    # -------------------------------------------------------------------------
    # 7. Direct Sync Fallback (PostgreSQL Staging Sync)
    # -------------------------------------------------------------------------
    def run_direct_sync(
        self,
        source_csv_path: str = "data/processed/netflix_catalog_enriched_master.csv",
    ) -> Dict[str, Any]:
        """Direct ELT replication fallback syncing CSV records into staging.stg_netflix_titles.

        Used when Airbyte container is initializing or for automated testing.
        """
        logger.info(f"[FALLBACK SYNC] Executing direct database replication from {source_csv_path}...")
        if not os.path.exists(source_csv_path):
            logger.warning(f"Source file {source_csv_path} does not exist.")
            return {"success": False, "error": "File not found"}

        if not db_manager.test_connection():
            logger.warning("PostgreSQL database offline; direct sync skipped.")
            return {"success": False, "error": "Database offline"}

        import pandas as pd
        df = pd.read_csv(source_csv_path)
        logger.info(f"Loaded {len(df)} records from {source_csv_path} for staging sync.")

        raw_conn = db_manager.engine.raw_connection()
        synced_count = 0
        try:
            with raw_conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS staging.stg_netflix_titles (
                        netflix_id VARCHAR(50) PRIMARY KEY,
                        title VARCHAR(500) NOT NULL,
                        title_type VARCHAR(50),
                        synopsis TEXT,
                        release_year INT,
                        date_added VARCHAR(100),
                        runtime_seconds VARCHAR(50),
                        maturity_rating VARCHAR(50),
                        raw_json JSONB,
                        extracted_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                for _, row in df.iterrows():
                    nid = str(row.get("netflix_id", ""))
                    title = str(row.get("title", ""))
                    m_type = str(row.get("media_type", "movie"))
                    year = int(row.get("release_year", 2026)) if pd.notnull(row.get("release_year")) else 2026
                    rating = str(row.get("maturity_rating", "TV-MA"))
                    synopsis = str(row.get("synopsis", ""))
                    runtime = str(row.get("runtime_minutes", "90"))
                    date_added = str(row.get("date_added", "2026-01-01"))

                    raw_json = json.dumps({
                        "sync_engine": "Airbyte_ELT_Pipeline",
                        "title": title,
                        "source": row.get("source", "master_catalog"),
                        "vote_average": float(row.get("vote_average", 7.5)) if pd.notnull(row.get("vote_average")) else 7.5,
                        "popularity": float(row.get("popularity", 50.0)) if pd.notnull(row.get("popularity")) else 50.0,
                    })

                    cursor.execute("""
                        INSERT INTO staging.stg_netflix_titles (
                            netflix_id, title, title_type, synopsis, release_year,
                            date_added, runtime_seconds, maturity_rating, raw_json
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (netflix_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            date_added = EXCLUDED.date_added,
                            runtime_seconds = EXCLUDED.runtime_seconds,
                            maturity_rating = EXCLUDED.maturity_rating,
                            raw_json = EXCLUDED.raw_json;
                    """, (nid, title, m_type, synopsis, year, date_added, runtime, rating, raw_json))
                    synced_count += 1

                raw_conn.commit()
            logger.info(f"[SUCCESS] Direct staging sync loaded {synced_count} records into staging.stg_netflix_titles.")
            return {"success": True, "records_synced": synced_count, "engine": "Direct_Postgres_Staging"}
        finally:
            raw_conn.close()


airbyte_client = AirbyteClient()
