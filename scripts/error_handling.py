"""
Error Handling - Error detection and retry mechanism
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur during search"""
    CAPTCHA = "captcha"
    NETWORK_TIMEOUT = "network_timeout"
    AI_MODE_UNAVAILABLE = "ai_mode_unavailable"
    BROWSER_ERROR = "browser_error"
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 2
    base_delay: float = 1.0
    max_delay: float = 10.0
    exponential_backoff: bool = True


@dataclass
class ErrorReport:
    """Report of an error that occurred"""
    error_type: ErrorType
    message: str
    timestamp: float
    retries_attempted: int = 0
    recovered: bool = False


@dataclass
class ErrorAccumulator:
    """Accumulates errors for reporting"""
    errors: List[ErrorReport] = field(default_factory=list)

    def add(self, error: ErrorReport):
        self.errors.append(error)

    def get_latest(self) -> Optional[ErrorReport]:
        return self.errors[-1] if self.errors else None

    def get_summary(self) -> str:
        if not self.errors:
            return "No errors"

        lines = [f"Total errors: {len(self.errors)}"]
        error_counts = {}
        for error in self.errors:
            error_counts[error.error_type] = error_counts.get(error.error_type, 0) + 1

        for error_type, count in error_counts.items():
            lines.append(f"  - {error_type.value}: {count}")

        return "\n".join(lines)


class ErrorHandler:
    """
    Handles errors and implements retry logic

    Features:
    - CAPTCHA detection and user notification
    - Network timeout retry with exponential backoff
    - AI Mode unavailability detection
    - Error accumulation and reporting
    """

    CAPTCHA_INDICATORS = [
        "captcha",
        "recaptcha",
        "Are you a robot",
        "我不是机器人",
        "I'm not a robot",
        "我不是机器人",
        "Je ne suis pas un robot",
        "Ich bin kein Roboter",
    ]

    AI_MODE_UNAVAILABLE_INDICATORS = [
        "AI Mode is not available",
        "AI Mode isn't available",
        "Mode IA n'est pas disponible",
        "Der KI-Modus ist nicht verfügbar",
        "El modo de IA no está disponible",
        "La modalità IA non è disponibile",
        "AI-modus is niet beschikbaar",
    ]

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_config = retry_config or RetryConfig()
        self.error_accumulator = ErrorAccumulator()

    def detect_error(self, html: str, error_type: Optional[ErrorType] = None) -> Optional[ErrorReport]:
        """
        Detect error from HTML content

        Args:
            html: HTML content to analyze
            error_type: Optional hint for error type

        Returns:
            ErrorReport if error detected, None otherwise
        """
        if not html:
            return None

        html_lower = html.lower()

        if error_type == ErrorType.CAPTCHA or error_type is None:
            for indicator in self.CAPTCHA_INDICATORS:
                if indicator.lower() in html_lower:
                    return ErrorReport(
                        error_type=ErrorType.CAPTCHA,
                        message=f"CAPTCHA detected: {indicator}",
                        timestamp=time.time(),
                    )

        if error_type == ErrorType.AI_MODE_UNAVAILABLE or error_type is None:
            for indicator in self.AI_MODE_UNAVAILABLE_INDICATORS:
                if indicator in html:
                    return ErrorReport(
                        error_type=ErrorType.AI_MODE_UNAVAILABLE,
                        message=f"AI Mode unavailable: {indicator}",
                        timestamp=time.time(),
                    )

        return None

    def should_retry(self, error: ErrorReport) -> bool:
        """
        Determine if error is retryable

        Args:
            error: The error that occurred

        Returns:
            True if should retry, False otherwise
        """
        retryable_types = {
            ErrorType.NETWORK_TIMEOUT,
            ErrorType.BROWSER_ERROR,
        }

        return error.error_type in retryable_types

    def calculate_delay(self, retry_count: int) -> float:
        """
        Calculate delay before retry

        Args:
            retry_count: Number of retries already attempted

        Returns:
            Delay in seconds
        """
        if self.retry_config.exponential_backoff:
            delay = self.retry_config.base_delay * (2 ** retry_count)
        else:
            delay = self.retry_config.base_delay

        return min(delay, self.retry_config.max_delay)

    def execute_with_retry(
        self,
        func: Callable[[], Any],
        error_checker: Optional[Callable[[Any], Optional[ErrorReport]]] = None,
    ) -> tuple[Any, ErrorAccumulator]:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            error_checker: Optional function to check result for errors

        Returns:
            Tuple of (result, ErrorAccumulator)
        """
        errors = ErrorAccumulator()
        last_result = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                result = func()
                last_result = result

                if error_checker and result is not None:
                    error_report = error_checker(result)
                    if error_report:
                        error_report.retries_attempted = attempt
                        errors.add(error_report)

                        if not self.should_retry(error_report):
                            break

                        if attempt < self.retry_config.max_retries:
                            delay = self.calculate_delay(attempt)
                            logger.info(f"Retrying in {delay}s (attempt {attempt + 1}/{self.retry_config.max_retries + 1})")
                            time.sleep(delay)
                            continue

                return result, errors

            except Exception as e:
                error_report = ErrorReport(
                    error_type=ErrorType.BROWSER_ERROR,
                    message=f"Exception: {str(e)}",
                    timestamp=time.time(),
                    retries_attempted=attempt,
                )
                errors.add(error_report)
                logger.error(f"Error during execution: {e}")

                if attempt < self.retry_config.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    break

        return last_result, errors

    def format_error_message(self, error: ErrorReport) -> str:
        """
        Format error for user display

        Args:
            error: Error to format

        Returns:
            Formatted error message
        """
        if error.error_type == ErrorType.CAPTCHA:
            return (
                "CAPTCHA detected. Please complete the CAPTCHA manually in the browser, "
                "then try again. Consider using a persistent profile to avoid future CAPTCHAs."
            )

        elif error.error_type == ErrorType.AI_MODE_UNAVAILABLE:
            return (
                "AI Mode is not available in your region or language. "
                "Try using a VPN or changing your browser's language settings."
            )

        elif error.error_type == ErrorType.NETWORK_TIMEOUT:
            return (
                f"Network timeout after {error.retries_attempted} retries. "
                "Please check your internet connection and try again."
            )

        elif error.error_type == ErrorType.BROWSER_ERROR:
            return f"Browser error: {error.message}"

        else:
            return f"Unknown error: {error.message}"


def main():
    """Demo usage"""
    handler = ErrorHandler(RetryConfig(max_retries=2, base_delay=0.5))

    html_with_captcha = """
    <html>
        <body>
            <div class="captcha">
                <p>Are you a robot?</p>
            </div>
        </body>
    </html>
    """

    error = handler.detect_error(html_with_captcha)
    if error:
        print(f"Detected: {error.error_type.value}")
        print(f"Message: {error.message}")
        print(f"Should retry: {handler.should_retry(error)}")
        print(f"User message: {handler.format_error_message(error)}")


if __name__ == "__main__":
    main()
