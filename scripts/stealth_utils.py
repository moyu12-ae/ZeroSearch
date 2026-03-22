"""
Stealth Utils - Human Behavior Simulation
Simulates realistic human browsing behavior

Features:
- Random delays between actions
- Human-like typing speed
- Realistic mouse movements
- Random scroll behavior
"""

import random
import time
from typing import Optional, Callable

try:
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class HumanBehavior:
    """
    Simulates human browsing behavior to avoid bot detection.
    """

    TYPING_SPEED_MIN = 0.05
    TYPING_SPEED_MAX = 0.2

    CLICK_DELAY_MIN = 0.1
    CLICK_DELAY_MAX = 0.5

    SCROLL_PAUSE_MIN = 0.5
    SCROLL_PAUSE_MAX = 2.0

    MOUSE_MOVE_DURATION = 0.3

    def __init__(self, seed: Optional[int] = None):
        """Initialize with optional random seed for reproducibility"""
        self._random = random.Random(seed)

    def random_delay(self, min_seconds: float = 0.1, max_seconds: float = 0.5) -> float:
        """
        Add a random delay.

        Args:
            min_seconds: Minimum delay
            max_seconds: Maximum delay

        Returns:
            Actual delay in seconds
        """
        delay = self._random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        return delay

    def human_delay(self) -> float:
        """Add a realistic human-like delay (0.5-2 seconds)"""
        return self.random_delay(0.5, 2.0)

    def fast_delay(self) -> float:
        """Add a fast delay (0.1-0.3 seconds)"""
        return self.random_delay(0.1, 0.3)

    def typing_delay(self) -> float:
        """Simulate realistic typing speed (50-200ms per character)"""
        return self.random_delay(self.TYPING_SPEED_MIN, self.TYPING_SPEED_MAX)

    def click_delay(self) -> float:
        """Delay between clicks (100-500ms)"""
        return self.random_delay(self.CLICK_DELAY_MIN, self.CLICK_DELAY_MAX)


class StealthBrowser:
    """
    Browser automation with human-like behavior.

    Works with agent-browser CLI commands or Selenium WebDriver.
    """

    def __init__(self, random_seed: Optional[int] = None):
        self.human = HumanBehavior(seed=random_seed)
        self._action_count = 0

    def human_open(self, command_func: Callable) -> None:
        """
        Open URL with human-like behavior.

        Args:
            command_func: Function that executes browser command
        """
        self.human.human_delay()
        self._action_count += 1
        command_func()
        self.human.fast_delay()

    def human_click(self, selector: str, command_func: Callable) -> None:
        """
        Click element with human-like delay.

        Args:
            selector: CSS selector for element
            command_func: Function that executes click
        """
        self.human.human_delay()
        self._action_count += 1
        command_func(selector)
        self.human.click_delay()

    def human_type(self, text: str, input_func: Callable[[str], None]) -> None:
        """
        Type text with human-like speed.

        Args:
            text: Text to type
            input_func: Function that types text
        """
        for char in text:
            input_func(char)
            self.human.typing_delay()
        self._action_count += 1

    def human_scroll(self, scroll_func: Callable) -> None:
        """
        Scroll with random pauses.

        Args:
            scroll_func: Function that performs scroll
        """
        self.human.human_delay()
        self._action_count += 1
        scroll_func()
        self.human.random_delay(
            self.human.SCROLL_PAUSE_MIN,
            self.human.SCROLL_PAUSE_MAX
        )

    def get_action_count(self) -> int:
        """Get number of actions performed"""
        return self._action_count

    def reset_action_count(self) -> None:
        """Reset action counter"""
        self._action_count = 0


def human_typing_simulation(text: str, typing_func: Callable[[str], None]) -> float:
    """
    Simulate human typing speed.

    Args:
        text: Text to type
        typing_func: Function that types a single character

    Returns:
        Total time taken
    """
    start = time.time()

    for char in text:
        typing_func(char)
        delay = random.uniform(0.05, 0.2)
        time.sleep(delay)

    return time.time() - start


def random_mouse_move(from_x: int, from_y: int, to_x: int, to_y: int) -> list:
    """
    Generate random mouse movement path.

    Args:
        from_x, from_y: Starting coordinates
        to_x, to_y: Ending coordinates

    Returns:
        List of (x, y) waypoints
    """
    waypoints = []

    dx = to_x - from_x
    dy = to_y - from_y

    num_steps = random.randint(5, 15)

    for i in range(num_steps + 1):
        t = i / num_steps

        noise_x = random.gauss(0, 5)
        noise_y = random.gauss(0, 5)

        x = int(from_x + dx * t + noise_x)
        y = int(from_y + dy * t + noise_y)

        waypoints.append((x, y))

    return waypoints


def random_scroll_pattern(driver) -> None:
    """
    Perform random scroll behavior.

    Args:
        driver: Selenium WebDriver instance
    """
    scroll_amount = random.randint(200, 600)
    direction = random.choice(['up', 'down', 'page_down', 'page_up'])

    if direction == 'up':
        driver.execute_script(f"window.scrollBy(0, -{scroll_amount})")
    elif direction == 'down':
        driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
    elif direction == 'page_down':
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
    else:
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_UP)

    time.sleep(random.uniform(0.3, 1.0))


def demo():
    """Demo usage"""
    print("=" * 60)
    print("Stealth Utils Demo")
    print("=" * 60)

    human = HumanBehavior(seed=42)

    print("\n1. Random delays:")
    for i in range(3):
        delay = human.random_delay(0.5, 1.5)
        print(f"   Delay {i+1}: {delay:.3f}s")

    print("\n2. Typing simulation:")
    test_text = "Hello, World!"
    print(f"   Typing: '{test_text}'")

    typed = []
    def type_char(c):
        typed.append(c)
        print(f"   typed: {''.join(typed)}", end='\r', flush=True)

    start = time.time()
    for char in test_text:
        type_char(char)
        human.typing_delay()
    print()
    elapsed = time.time() - start
    print(f"   Total time: {elapsed:.2f}s")

    print("\n3. Mouse movement path:")
    path = random_mouse_move(0, 0, 500, 300)
    print(f"   Generated {len(path)} waypoints")
    print(f"   Start: {path[0]}")
    print(f"   End: {path[-1]}")

    print("\n✅ Stealth Utils demo complete!")


if __name__ == "__main__":
    demo()
