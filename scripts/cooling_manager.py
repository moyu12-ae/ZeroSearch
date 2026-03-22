"""
CoolingManager - 冷却管理器 (Phase 5)

管理 CAPTCHA 检测后的冷却等待和用户提示。

Features:
- 渐进式冷却时间（1分钟 → 5分钟 → 15分钟 → 60分钟）
- 清晰的错误消息生成
- 冷却状态持久化
- 会话重启时重置 CAPTCHA 计数

Usage:
    from cooling_manager import CoolingManager

    manager = CoolingManager()
    result = manager.notify_captcha()

    if result.needs_cooldown:
        print(f"请等待 {result.wait_minutes} 分钟")
        print(f"提示: {result.message}")

    # 用户解决后
    manager.confirm_resolved()
"""

import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CoolingResult:
    """冷却检测结果"""
    needs_cooldown: bool
    wait_minutes: int
    message: str
    captcha_count: int
    level: int
    user_action_required: bool

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def __str__(self) -> str:
        if self.needs_cooldown:
            return f"需要冷却 {self.wait_minutes} 分钟 (CAPTCHA #{self.captcha_count})"
        return "无需冷却"


@dataclass
class CoolingConfig:
    """冷却配置"""
    cooldown_levels: List[int] = None
    default_wait_minutes: int = 5
    max_captcha_count: int = 10

    def __post_init__(self):
        if self.cooldown_levels is None:
            self.cooldown_levels = [1, 5, 15, 30, 60]


class CoolingManager:
    """
    冷却管理器

    管理 CAPTCHA 检测后的冷却等待和用户提示。

    渐进式冷却策略:
    - 首次 CAPTCHA: 建议等待 1-5 分钟
    - 第二次 CAPTCHA: 建议等待 5-15 分钟
    - 第三次 CAPTCHA: 建议等待 15-30 分钟
    - 第四次+: 建议等待 30-60 分钟

    Usage:
        manager = CoolingManager()
        result = manager.notify_captcha()
        if result.needs_cooldown:
            print(result.message)
    """

    STATE_FILE = "cooling_state.json"

    CAPTCHA_MESSAGES = [
        "检测到 Google CAPTCHA。请在浏览器中手动解决验证。",
        "您的 IP 可能被 Google 限流。建议等待 1-5 分钟后重试。",
        "继续检测到限制。建议等待 5-15 分钟让系统冷却。",
        "频繁触发限制。建议等待 15-30 分钟。",
        "持续检测到限制。建议等待 30-60 分钟或更长时间。",
    ]

    def __init__(self, state_file: Optional[Path] = None):
        """
        初始化冷却管理器

        Args:
            state_file: 状态文件路径（可选）
        """
        self._state_file = state_file
        self._state: Dict[str, Any] = {
            "is_cooling": False,
            "cooldown_until": None,
            "captcha_count": 0,
            "last_captcha_time": None,
        }
        self._config = CoolingConfig()
        self._load_state()

    def _get_state_path(self) -> Optional[Path]:
        """获取状态文件路径"""
        if self._state_file:
            return self._state_file

        cache_dir = Path.home() / ".cache" / "zero-search"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / self.STATE_FILE

    def _load_state(self) -> None:
        """从文件加载状态"""
        state_path = self._get_state_path()
        if not state_path or not state_path.exists():
            return

        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                loaded_state = json.load(f)

                self._state["is_cooling"] = loaded_state.get("is_cooling", False)
                self._state["cooldown_until"] = loaded_state.get("cooldown_until")
                self._state["captcha_count"] = loaded_state.get("captcha_count", 0)
                self._state["last_captcha_time"] = loaded_state.get("last_captcha_time")

                self._check_cooldown_expired()

                logger.debug(f"Loaded cooling state: {self._state}")
        except Exception as e:
            logger.warning(f"Failed to load cooling state: {e}")

    def _save_state(self) -> None:
        """保存状态到文件"""
        state_path = self._get_state_path()
        if not state_path:
            return

        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved cooling state: {self._state}")
        except Exception as e:
            logger.warning(f"Failed to save cooling state: {e}")

    def _check_cooldown_expired(self) -> None:
        """检查冷却是否已过期"""
        if not self._state["is_cooling"]:
            return

        if self._state["cooldown_until"]:
            cooldown_until = datetime.fromisoformat(self._state["cooldown_until"])
            if datetime.now() >= cooldown_until:
                self._state["is_cooling"] = False
                self._state["cooldown_until"] = None
                logger.info("Cooldown period expired")

    def _get_cooldown_minutes(self, captcha_count: int) -> int:
        """根据 CAPTCHA 次数获取冷却分钟数"""
        levels = self._config.cooldown_levels

        if captcha_count <= 0:
            return levels[0] if levels else 1

        index = min(captcha_count - 1, len(levels) - 1)
        return levels[index]

    def _get_message(self, captcha_count: int, wait_minutes: int) -> str:
        """获取用户提示消息"""
        if captcha_count <= 0:
            return self.CAPTCHA_MESSAGES[0]

        index = min(captcha_count - 1, len(self.CAPTCHA_MESSAGES) - 1)
        base_message = self.CAPTCHA_MESSAGES[index]

        return f"{base_message}\n\n建议等待时间: {wait_minutes} 分钟"

    def notify_captcha(self) -> CoolingResult:
        """
        通知检测到 CAPTCHA

        Returns:
            CoolingResult 包含冷却建议和消息
        """
        self._state["captcha_count"] += 1
        self._state["last_captcha_time"] = datetime.now().isoformat()

        captcha_count = self._state["captcha_count"]
        wait_minutes = self._get_cooldown_minutes(captcha_count)
        message = self._get_message(captcha_count, wait_minutes)

        cooldown_until = datetime.now() + timedelta(minutes=wait_minutes)
        self._state["is_cooling"] = True
        self._state["cooldown_until"] = cooldown_until.isoformat()

        self._save_state()

        logger.warning(f"CAPTCHA #{captcha_count}: cooldown {wait_minutes} minutes")

        level = min(captcha_count, len(self._config.cooldown_levels))

        return CoolingResult(
            needs_cooldown=True,
            wait_minutes=wait_minutes,
            message=message,
            captcha_count=captcha_count,
            level=level,
            user_action_required=True
        )

    def check_cooling(self) -> CoolingResult:
        """
        检查当前冷却状态

        Returns:
            CoolingResult 包含当前冷却状态
        """
        self._check_cooldown_expired()

        if self._state["is_cooling"]:
            captcha_count = self._state["captcha_count"]
            wait_minutes = self._get_cooldown_minutes(captcha_count)
            message = f"仍在冷却中。CAPTCHA #{captcha_count}，建议等待 {wait_minutes} 分钟。"

            return CoolingResult(
                needs_cooldown=True,
                wait_minutes=wait_minutes,
                message=message,
                captcha_count=captcha_count,
                level=min(captcha_count, len(self._config.cooldown_levels)),
                user_action_required=True
            )

        return CoolingResult(
            needs_cooldown=False,
            wait_minutes=0,
            message="无需冷却，可以继续搜索",
            captcha_count=self._state["captcha_count"],
            level=0,
            user_action_required=False
        )

    def confirm_resolved(self) -> None:
        """
        确认 CAPTCHA 已解决（用户手动解决）

        重置 CAPTCHA 计数但保持冷却状态一段时间
        """
        self._state["captcha_count"] = 0
        self._save_state()
        logger.info("CAPTCHA resolved, count reset")

    def reset(self) -> None:
        """
        完全重置冷却状态

        包括 CAPTCHA 计数和冷却状态
        """
        self._state["is_cooling"] = False
        self._state["cooldown_until"] = None
        self._state["captcha_count"] = 0
        self._state["last_captcha_time"] = None
        self._save_state()
        logger.info("CoolingManager reset")

    def get_status(self) -> Dict[str, Any]:
        """
        获取当前状态

        Returns:
            状态字典
        """
        self._check_cooldown_expired()

        return {
            "is_cooling": self._state["is_cooling"],
            "cooldown_until": self._state["cooldown_until"],
            "captcha_count": self._state["captcha_count"],
            "last_captcha_time": self._state["last_captcha_time"],
            "wait_minutes": self._get_cooldown_minutes(self._state["captcha_count"]),
        }

    def get_cooldown_remaining(self) -> float:
        """
        获取剩余冷却时间（秒）

        Returns:
            剩余秒数，0 表示无需等待
        """
        self._check_cooldown_expired()

        if not self._state["is_cooling"] or not self._state["cooldown_until"]:
            return 0.0

        cooldown_until = datetime.fromisoformat(self._state["cooldown_until"])
        remaining = (cooldown_until - datetime.now()).total_seconds()

        return max(0.0, remaining)


def demo():
    """演示 CoolingManager 的使用"""
    print("=" * 60)
    print("CoolingManager 演示 (Phase 5)")
    print("=" * 60)

    manager = CoolingManager()

    print("\n1. 检查初始状态:")
    status = manager.get_status()
    print(f"   CAPTCHA 计数: {status['captcha_count']}")
    print(f"   正在冷却: {status['is_cooling']}")

    print("\n2. 模拟检测到 CAPTCHA:")
    result = manager.notify_captcha()
    print(f"   {result}")
    print(f"   消息: {result.message}")

    print("\n3. 再次检测到 CAPTCHA:")
    result = manager.notify_captcha()
    print(f"   {result}")

    print("\n4. 第三次检测到 CAPTCHA:")
    result = manager.notify_captcha()
    print(f"   {result}")

    print("\n5. 检查冷却状态:")
    result = manager.check_cooling()
    print(f"   {result}")

    print("\n6. 模拟用户解决 CAPTCHA:")
    manager.confirm_resolved()
    print(f"   CAPTCHA 计数已重置")

    print("\n7. 再次检查状态:")
    status = manager.get_status()
    print(f"   CAPTCHA 计数: {status['captcha_count']}")

    print("\n8. 完全重置:")
    manager.reset()
    status = manager.get_status()
    print(f"   CAPTCHA 计数: {status['captcha_count']}")
    print(f"   正在冷却: {status['is_cooling']}")

    print("\n✅ CoolingManager 演示完成!")


if __name__ == "__main__":
    demo()
