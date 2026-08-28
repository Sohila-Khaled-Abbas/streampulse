"""CLI Automation Script: Programmatically configure, test, and run the Airbyte ELT Connection.

Usage:
    python scripts/run_airbyte_connection.py
    python scripts/run_airbyte_connection.py --sync-now --wait
    python scripts/run_airbyte_connection.py --test
"""

import argparse
import os
import sys

# Ensure root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.load.airbyte_client import AirbyteClient, airbyte_client
from src.utils.logger import logger


def run_airbyte_automation(
    host: str | None = None,
    port: int | None = None,
    sync_now: bool = True,
    wait_for_completion: bool = True,
    timeout: int = 180,
    source_file: str = "data/processed/netflix_catalog_enriched_master.csv",
    use_fallback: bool = True,
) -> int:
    """Execute complete Airbyte connection lifecycle via code."""
    logger.info(
        "================================================================================"
    )
    logger.info("[AIRBYTE] STREAMPULSE AIRBYTE CONNECTION ORCHESTRATOR")
    logger.info(
        "================================================================================"
    )

    client = AirbyteClient(host=host, port=port) if (host or port) else airbyte_client

    # 1. Health check
    logger.info(f"Checking Airbyte Server health at {client.host}:{client.port}...")
    health = client.check_health()

    if not health.get("available"):
        logger.warning(
            f"[AIRBYTE OFFLINE] Airbyte API is not responding at {client.host}:{client.port}.\n"
            f"Note: If running in Docker, start Airbyte using:\n"
            f"  docker compose -f docker/docker-compose.airbyte.yml up -d\n"
        )
        if use_fallback:
            logger.info("Engaging Direct PostgreSQL Staging Sync Fallback...")
            fallback_res = client.run_direct_sync(source_csv_path=source_file)
            if fallback_res.get("success"):
                logger.info(
                    f"[SUCCESS] Synced {fallback_res.get('records_synced')} titles via staging fallback engine."
                )
                return 0
            else:
                logger.error(
                    f"[ERROR] Direct staging sync failed: {fallback_res.get('error')}"
                )
                return 1
        return 1

    # 2. Workspace setup
    logger.info("Step 1/4: Discovering/Provisioning Workspace...")
    workspace_id = client.get_or_create_workspace(workspace_name="StreamPulse")
    if not workspace_id:
        logger.error("Failed to obtain Airbyte workspace ID.")
        if use_fallback:
            return _execute_fallback(client, source_file)
        return 1
    logger.info(f"[OK] Workspace ID: {workspace_id}")

    # 3. Source setup
    logger.info("Step 2/4: Discovering/Provisioning File (CSV) Source...")
    source_id = client.get_or_create_source(
        workspace_id=workspace_id,
        source_name="StreamPulse_Daily_2026_Catalog",
        file_path=source_file,
    )
    if not source_id:
        logger.error("Failed to obtain Airbyte source ID.")
        if use_fallback:
            return _execute_fallback(client, source_file)
        return 1
    logger.info(f"[OK] Source ID: {source_id}")

    # 4. Destination setup
    logger.info("Step 3/4: Discovering/Provisioning PostgreSQL Destination...")
    dest_id = client.get_or_create_destination(
        workspace_id=workspace_id,
        dest_name="StreamPulse_PostgreSQL_Warehouse",
        db_host="host.docker.internal",
        db_port=5432,
        db_name="streampulse",
        db_user="postgres",
        db_password="postgres",
        default_schema="staging",
    )
    if not dest_id:
        logger.error("Failed to obtain Airbyte destination ID.")
        if use_fallback:
            return _execute_fallback(client, source_file)
        return 1
    logger.info(f"[OK] Destination ID: {dest_id}")

    # 5. Connection setup
    logger.info("Step 4/4: Discovering/Provisioning Replication Connection...")
    conn_id = client.get_or_create_connection(
        workspace_id=workspace_id,
        source_id=source_id,
        destination_id=dest_id,
        connection_name="Daily_2026_Catalog_to_Staging",
    )
    if not conn_id:
        logger.error("Failed to obtain Airbyte connection ID.")
        if use_fallback:
            return _execute_fallback(client, source_file)
        return 1
    logger.info(f"[OK] Connection ID: {conn_id}")

    # 6. Trigger Replication
    if sync_now:
        logger.info(f"Triggering sync on connection {conn_id}...")
        if wait_for_completion:
            res = client.sync_and_wait(connection_id=conn_id, timeout_seconds=timeout)
            if res.get("success"):
                logger.info(
                    "[SUCCESS] Airbyte replication cycle completed successfully via code!"
                )
                return 0
            else:
                logger.warning(
                    f"[REPLICATION NOTICE] Airbyte container sync issue: {res}"
                )
                if use_fallback:
                    return _execute_fallback(client, source_file)
                return 1
        else:
            res = client.trigger_sync(connection_id=conn_id)
            if res.get("success"):
                logger.info(
                    f"[OK] Airbyte sync triggered (Job ID: {res.get('job_id')}). Running in background."
                )
                return 0
            else:
                logger.error(f"[ERROR] Failed to trigger sync: {res}")
                if use_fallback:
                    return _execute_fallback(client, source_file)
                return 1

    logger.info(
        "[SUCCESS] Airbyte setup completed. Connection is ready for automated syncs."
    )
    return 0


def _execute_fallback(client: AirbyteClient, source_file: str) -> int:
    """Execute direct PostgreSQL staging sync fallback engine."""
    logger.info("Engaging Direct PostgreSQL Staging Sync Fallback...")
    fallback_res = client.run_direct_sync(source_csv_path=source_file)
    if fallback_res.get("success"):
        logger.info(
            f"[SUCCESS] Synced {fallback_res.get('records_synced')} titles via staging fallback engine."
        )
        return 0
    else:
        logger.error(f"[ERROR] Direct staging sync failed: {fallback_res.get('error')}")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Programmatically run Airbyte ELT Connection"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Airbyte server host (default: localhost)",
    )
    parser.add_argument(
        "--port", type=int, default=None, help="Airbyte server port (default: 8000)"
    )
    parser.add_argument(
        "--sync-now", action="store_true", default=True, help="Trigger immediate sync"
    )
    parser.add_argument(
        "--no-wait", action="store_true", help="Do not wait for sync completion"
    )
    parser.add_argument(
        "--timeout", type=int, default=180, help="Sync timeout in seconds"
    )
    parser.add_argument(
        "--source-file",
        type=str,
        default="data/processed/netflix_catalog_enriched_master.csv",
        help="Source CSV file path",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode (health check + direct sync validation)",
    )

    args = parser.parse_args()

    exit_code = run_airbyte_automation(
        host=args.host,
        port=args.port,
        sync_now=args.sync_now,
        wait_for_completion=not args.no_wait,
        timeout=args.timeout,
        source_file=args.source_file,
        use_fallback=True,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
