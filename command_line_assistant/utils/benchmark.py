"""Module that holds the benchmark functions and metrics"""

import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class TimingLogger:
    """Specialized logger class for timing function execution.

    This class provides detailed timing information for function calls, including:
    - Function name and arguments
    - Monotonic time (wall clock time)
    - Performance counter time (CPU time)
    - Custom timing messages

    Example:
        >>> # Global filtered params
        >>> timing = TimingLogger(filtered_params=['password', 'secret'])
        >>>
        >>> # Additional per-function filtered params
        >>> @timing.timeit(filtered_params=['extra_sensitive'])
        >>> def my_function(arg1, password, extra_sensitive):
        >>>     # Function code here
        >>>     pass
    """

    def __init__(self, filtered_params: Optional[list[str]] = None):
        """Initialize TimingLogger with optional filtered parameters.

        Arguments:
            filtered_params (Optional[list[str]], optional): List of parameter names to be redacted in logs
        """
        self.filtered_params = filtered_params or []

    def _sanitize_value(
        self,
        key: str,
        value: Any,
        additional_filtered_params: Optional[list[str]] = None,
    ) -> str:
        """Sanitize values based on filtered parameters.

        Arguments:
            key (str): Parameter name
            value (Any): Parameter value
            additional_filtered_params (Optional[list[str]], optional): Additional parameters to filter

        Returns:
            str: Original value as string or "redacted" if parameter should be filtered
        """
        all_filtered_params = set(self.filtered_params)
        if additional_filtered_params:
            all_filtered_params.update(additional_filtered_params)

        if key in all_filtered_params:
            return "redacted"

        # Handle different types of values
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        elif value is None:
            return "None"
        else:
            # For objects, return their class name instead of the full repr
            return f"<{value.__class__.__name__}>"

    def _log_timing(
        self,
        func_name: str,
        args: tuple,
        kwargs: dict,
        duration: float,
        cpu_time: float,
        filtered_params: Optional[list[str]] = None,
        message: Optional[str] = None,
    ) -> None:
        """Internal method to log timing information.

        Arguments:
            func_name (str): Name of the function being timed
            args (tuple): Positional arguments passed to the function
            kwargs (dict): Keyword arguments passed to the function
            duration (float): Wall clock duration in milliseconds
            cpu_time (float): CPU time duration in milliseconds
            filtered_params (Optional[list[str]], optional): Additional parameters to filter
            message (Optional[str]): Optional custom message to include in log
        """
        timing_data = {
            "type": "timing_info",
            "function": func_name,
            "args": [
                self._sanitize_value(f"arg_{i}", arg, filtered_params)
                for i, arg in enumerate(args)
            ],
            "kwargs": {
                k: self._sanitize_value(k, v, filtered_params)
                for k, v in kwargs.items()
            },
            "timing": {
                "duration_ms": round(duration, 4),
                "duration_sec": round(duration / 1000, 4),
                "cpu_time_ms": round(cpu_time, 4),
                "cpu_time_sec": round(cpu_time / 1000, 4),
            },
        }

        if message:
            timing_data["message"] = message

        logger.debug(json.dumps(timing_data))

    def timeit(
        self,
        func: Optional[Callable] = None,
        *,
        filtered_params: Optional[list[str]] = None,
    ) -> Callable:
        """Decorator to time function execution.

        Note:
            Can be used with or without parameters:
            @timing.timeit
            def func1(): ...

            @timing.timeit(filtered_params=['sensitive'])
            def func2(): ...

        Arguments:
            func (Optional[Callable]): The function to be timed
            filtered_params (Optional[list[str]], optional): Additional parameters to filter for this specific function

        Returns:
            Callable: The wrapped function
        """

        def decorator(func: Callable) -> Callable:
            """Decorator internal function that receives the outer function"""

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                """Wrapper function to handle the outer real function"""
                time_start = time.monotonic_ns()
                perf_start = time.perf_counter_ns()

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    time_end = time.monotonic_ns()
                    perf_end = time.perf_counter_ns()

                    duration = (time_end - time_start) / 1e6  # Convert to milliseconds
                    cpu_time = (perf_end - perf_start) / 1e6  # Convert to milliseconds

                    self._log_timing(
                        func_name=func.__name__,
                        args=args,
                        kwargs=kwargs,
                        duration=duration,
                        cpu_time=cpu_time,
                        filtered_params=filtered_params,
                    )

            return wrapper

        # Handle both @timeit and @timeit(filtered_params=[...]) cases
        if func is None:
            return decorator
        return decorator(func)
