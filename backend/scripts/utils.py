"""
Shared utilities for data initialization scripts.

This module provides common functionality for all initialization scripts including
progress tracking, error handling, retry logic, and data validation.
"""

import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from tqdm import tqdm

# Type variable for generic retry function
T = TypeVar("T")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data_initialization.log"),
    ],
)

logger = logging.getLogger(__name__)


class DataLoadError(Exception):
    """Custom exception for data loading errors."""

    pass


class ProgressTracker:
    """Track progress of data loading operations with visual feedback."""

    def __init__(self, total: int, desc: str):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items to process
            desc: Description of the operation
        """
        self.pbar = tqdm(total=total, desc=desc, unit="items")
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()

    def update(self, n: int = 1, success: bool = True):
        """
        Update progress.

        Args:
            n: Number of items processed
            success: Whether the operation was successful
        """
        self.pbar.update(n)
        if success:
            self.success_count += n
        else:
            self.error_count += n

    def close(self):
        """Close progress bar and log summary."""
        self.pbar.close()
        elapsed = time.time() - self.start_time
        logger.info(
            f"Completed: {self.success_count} successful, "
            f"{self.error_count} errors, "
            f"{elapsed:.2f}s elapsed"
        )


def retry_on_error(
    func: Callable[..., T],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[..., Optional[T]]:
    """
    Decorator to retry a function on error with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch

    Returns:
        Wrapped function that retries on error
    """

    def wrapper(*args, **kwargs) -> Optional[T]:
        current_delay = delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed after {max_retries} attempts: {func.__name__} - {str(e)}"
                    )
                    return None
                else:
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
        return None

    return wrapper


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Yields:
        SQLAlchemy database session

    Raises:
        DataLoadError: If database connection fails
    """
    from core.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise DataLoadError(f"Database transaction failed: {str(e)}")
    finally:
        session.close()


def batch_insert(
    session: Session,
    model_class: Any,
    data_list: List[Dict[str, Any]],
    batch_size: int = 100,
) -> int:
    """
    Bulk insert data with batching for performance.

    Args:
        session: SQLAlchemy session
        model_class: SQLAlchemy model class
        data_list: List of dictionaries containing model data
        batch_size: Number of records to insert per batch

    Returns:
        Number of records successfully inserted

    Raises:
        DataLoadError: If insertion fails
    """
    total_inserted = 0

    try:
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i : i + batch_size]
            objects = [model_class(**data) for data in batch]
            session.bulk_save_objects(objects)
            session.commit()
            total_inserted += len(batch)
            logger.debug(f"Inserted batch {i // batch_size + 1}: {len(batch)} records")

        logger.info(f"Successfully inserted {total_inserted} records")
        return total_inserted

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Batch insert failed: {str(e)}")
        raise DataLoadError(f"Failed to insert data: {str(e)}")


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate that all required fields are present and not None.

    Args:
        data: Dictionary containing data to validate
        required_fields: List of required field names

    Returns:
        True if all required fields are present, False otherwise
    """
    for field in required_fields:
        if field not in data or data[field] is None:
            logger.warning(f"Missing required field: {field}")
            return False
    return True


def check_duplicate(
    session: Session, model_class: Any, unique_field: str, value: Any
) -> bool:
    """
    Check if a record with the given unique field value already exists.

    Args:
        session: SQLAlchemy session
        model_class: SQLAlchemy model class
        unique_field: Name of the unique field to check
        value: Value to check for

    Returns:
        True if duplicate exists, False otherwise
    """
    exists = (
        session.query(model_class)
        .filter(getattr(model_class, unique_field) == value)
        .first()
    )
    return exists is not None


def log_data_quality_report(
    total: int,
    success: int,
    errors: int,
    duplicates: int = 0,
    validation_failures: int = 0,
):
    """
    Log a comprehensive data quality report.

    Args:
        total: Total number of records processed
        success: Number of successful insertions
        errors: Number of errors
        duplicates: Number of duplicate records skipped
        validation_failures: Number of validation failures
    """
    logger.info("=" * 60)
    logger.info("DATA QUALITY REPORT")
    logger.info("=" * 60)
    logger.info(f"Total records processed: {total}")
    logger.info(f"Successful insertions: {success}")
    logger.info(f"Errors: {errors}")
    logger.info(f"Duplicates skipped: {duplicates}")
    logger.info(f"Validation failures: {validation_failures}")
    logger.info(f"Success rate: {(success / total * 100) if total > 0 else 0:.2f}%")
    logger.info("=" * 60)


def format_date_range(start_date: datetime, end_date: datetime) -> str:
    """
    Format a date range for display.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Formatted date range string
    """
    return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float, returning default if conversion fails.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int, returning default if conversion fails.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default
