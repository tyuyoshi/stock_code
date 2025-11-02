#!/usr/bin/env python3
"""
Database Migration Runner

This script provides utilities for running database migrations in different environments.
Supports both development and production deployment patterns.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
import argparse
from dotenv import load_dotenv


def setup_environment():
    """Load environment variables and setup paths."""
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    load_dotenv()


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if result.returncode != 0 and check:
        print(f"Error: {result.stderr}")
        sys.exit(result.returncode)
    
    if result.stdout:
        print(result.stdout)
    
    return result


def check_database_connection():
    """Verify database is accessible."""
    print("Checking database connection...")
    
    # Use Python to test connection
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.sql import text
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            print("Error: DATABASE_URL not set")
            sys.exit(1)
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)


def get_current_revision() -> Optional[str]:
    """Get current database revision."""
    result = run_command(["alembic", "current"], check=False)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if '(head)' in line or line.strip():
                return line.split()[0] if line.split() else None
    return None


def run_migrations(mode: str = "upgrade", target: str = "head", sql_only: bool = False):
    """
    Run database migrations.
    
    Args:
        mode: Migration mode ('upgrade', 'downgrade', 'stamp')
        target: Target revision (default 'head' for latest)
        sql_only: Generate SQL without executing (offline mode)
    """
    check_database_connection()
    
    print(f"\n{'='*60}")
    print(f"Migration Mode: {mode}")
    print(f"Target: {target}")
    print(f"SQL Only: {sql_only}")
    print(f"{'='*60}\n")
    
    # Get current revision
    current = get_current_revision()
    if current:
        print(f"Current revision: {current}")
    else:
        print("No current revision (fresh database)")
    
    # Build command
    cmd = ["alembic", mode, target]
    if sql_only:
        cmd.append("--sql")
    
    # Run migration
    result = run_command(cmd)
    
    # Verify new revision
    if not sql_only and mode in ["upgrade", "downgrade"]:
        new_revision = get_current_revision()
        print(f"\n✓ Migration complete. New revision: {new_revision}")


def generate_migration(message: str, autogenerate: bool = True):
    """
    Generate a new migration.
    
    Args:
        message: Migration message
        autogenerate: Use autogenerate to detect model changes
    """
    check_database_connection()
    
    print(f"\n{'='*60}")
    print(f"Generating Migration: {message}")
    print(f"Autogenerate: {autogenerate}")
    print(f"{'='*60}\n")
    
    cmd = ["alembic", "revision", "-m", message]
    if autogenerate:
        cmd.insert(2, "--autogenerate")
    
    result = run_command(cmd)
    print("\n✓ Migration generated successfully")


def show_history():
    """Show migration history."""
    print("\n=== Migration History ===\n")
    run_command(["alembic", "history", "--verbose"])


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database")
    upgrade_parser.add_argument(
        "target", nargs="?", default="head", help="Target revision (default: head)"
    )
    upgrade_parser.add_argument(
        "--sql", action="store_true", help="Generate SQL only (offline mode)"
    )
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument(
        "target", help="Target revision (e.g., -1, revision_id)"
    )
    downgrade_parser.add_argument(
        "--sql", action="store_true", help="Generate SQL only (offline mode)"
    )
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate new migration")
    generate_parser.add_argument("message", help="Migration message")
    generate_parser.add_argument(
        "--empty", action="store_true", help="Create empty migration (no autogenerate)"
    )
    
    # Current command
    subparsers.add_parser("current", help="Show current revision")
    
    # History command
    subparsers.add_parser("history", help="Show migration history")
    
    # Check command
    subparsers.add_parser("check", help="Check database connection")
    
    # Stamp command (for existing databases)
    stamp_parser = subparsers.add_parser(
        "stamp", help="Stamp database with revision (for existing databases)"
    )
    stamp_parser.add_argument("revision", help="Revision to stamp")
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    # Execute command
    if args.command == "upgrade":
        run_migrations("upgrade", args.target, args.sql)
    elif args.command == "downgrade":
        run_migrations("downgrade", args.target, args.sql)
    elif args.command == "generate":
        generate_migration(args.message, not args.empty)
    elif args.command == "current":
        revision = get_current_revision()
        print(f"Current revision: {revision or 'None (fresh database)'}")
    elif args.command == "history":
        show_history()
    elif args.command == "check":
        check_database_connection()
        print("✓ Database connection successful")
    elif args.command == "stamp":
        run_command(["alembic", "stamp", args.revision])
        print(f"✓ Database stamped with revision: {args.revision}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()