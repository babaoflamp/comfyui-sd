"""
Enhanced logging system for ComfyUI

Provides structured logging with multiple handlers and formatters.
Supports file rotation, JSON output, and performance metrics.

Usage:
    from app.enhanced_logger import setup_enhanced_logger

    logger = setup_enhanced_logger(
        name="comfyui",
        level=logging.INFO,
        log_file="/var/log/comfyui/app.log"
    )

    logger.info("Server started", extra={
        "module": "server",
        "port": 8188,
        "mode": "production"
    })
"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import traceback


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""

        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)

        # Add exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for development"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""

        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"

        # Format message
        message = super().format(record)

        # Add extra fields
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            extra_str = " ".join(
                f"{k}={v}" for k, v in record.extra.items()
            )
            message += f" [{extra_str}]"

        return message


class PerformanceFilter(logging.Filter):
    """Filter for performance metrics"""

    def __init__(self):
        super().__init__()
        self.request_times = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Add timing information to logs"""

        if hasattr(record, "duration_ms"):
            # Highlight slow requests
            if record.duration_ms > 1000:
                if not hasattr(record, "extra"):
                    record.extra = {}
                record.extra["slow"] = True

        return True


def setup_enhanced_logger(
    name: str = "comfyui",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_output: bool = False,
    use_colors: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup enhanced logging system

    Args:
        name: Logger name
        level: Logging level
        log_file: Path to log file (None for console only)
        json_output: Use JSON formatter
        use_colors: Use colored console output
        max_bytes: Max log file size before rotation
        backup_count: Number of backup log files to keep

    Returns:
        Configured logger instance
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if json_output:
        console_formatter = JSONFormatter()
    elif use_colors:
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)

        if json_output:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                fmt='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Add performance filter
    perf_filter = PerformanceFilter()
    logger.addFilter(perf_filter)

    return logger


class LogContext:
    """Context manager for structured logging"""

    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        """
        Initialize log context

        Args:
            logger: Logger instance
            operation: Operation name
            **kwargs: Additional context
        """
        self.logger = logger
        self.operation = operation
        self.context = {
            "operation": operation,
            **kwargs
        }
        self.start_time = datetime.utcnow()

    def __enter__(self):
        self.logger.info(
            f"Starting {self.operation}",
            extra=self.context
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()

        if exc_type:
            self.logger.error(
                f"Failed {self.operation}: {exc_val}",
                extra={
                    **self.context,
                    "error_type": exc_type.__name__,
                    "duration_sec": duration
                },
                exc_info=(exc_type, exc_val, exc_tb)
            )
        else:
            self.logger.info(
                f"Completed {self.operation}",
                extra={
                    **self.context,
                    "duration_sec": duration
                }
            )


class MetricsLogger:
    """Logger for performance metrics"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics = {}

    def record_metric(self, name: str, value: float, unit: str = ""):
        """Record a metric"""
        self.metrics[name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.utcnow().isoformat()
        }

    def log_metrics(self):
        """Log all recorded metrics"""
        self.logger.info(
            "Performance metrics",
            extra={"metrics": self.metrics}
        )
        self.metrics.clear()

    def record_execution_time(self, operation: str, duration_ms: float):
        """Record operation execution time"""
        self.record_metric(f"{operation}_time", duration_ms, "ms")
        if duration_ms > 1000:
            self.logger.warning(
                f"Slow operation: {operation}",
                extra={
                    "operation": operation,
                    "duration_ms": duration_ms
                }
            )


# Example usage
if __name__ == "__main__":
    # Setup logger
    logger = setup_enhanced_logger(
        name="comfyui",
        level=logging.DEBUG,
        log_file="/tmp/comfyui.log",
        json_output=False,
        use_colors=True
    )

    # Basic logging
    logger.info("Application started")
    logger.debug("Debug message", extra={"user": "test", "action": "login"})

    # Context logging
    with LogContext(logger, "workflow_execution", workflow_id="abc123"):
        logger.info("Loading model...")
        logger.info("Model loaded successfully")

    # Metrics logging
    metrics = MetricsLogger(logger)
    metrics.record_execution_time("inference", 1234.5)
    metrics.record_metric("memory_usage", 5678.9, "MB")
    metrics.log_metrics()

    # Error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.exception("An error occurred")
