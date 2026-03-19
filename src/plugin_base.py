"""
DevicePlugin 抽象基類 — 所有設備插件的介面定義
"""

from abc import ABC, abstractmethod
from typing import Any, Callable


class DevicePlugin(ABC):
    """設備插件抽象基類，支援 Pull（主動讀取）和 Push（被動接收）兩種模式"""

    name: str = "base"
    protocol: str = "unknown"

    # --- 連線管理 ---

    @abstractmethod
    async def connect(self, config: dict) -> bool:
        """連線到設備或 broker"""

    async def disconnect(self) -> None:
        """斷開連線，清理資源"""

    # --- Pull 模式 ---

    @abstractmethod
    async def read(self, device_id: str, params: dict | None = None) -> dict:
        """主動讀取設備數據"""

    # --- Push 模式 ---

    async def start_listening(self, callback: Callable) -> None:
        """啟動監聽，收到數據時呼叫 callback(device_id, data)
        不支援 push 的 plugin 不需要覆寫"""

    async def stop_listening(self) -> None:
        """停止監聽"""

    # --- 下行控制 ---

    @abstractmethod
    async def write(self, device_id: str, params: dict) -> dict:
        """控制設備"""

    # --- 設備發現 ---

    async def discover(self) -> list[dict]:
        """自動發現設備（可選）"""
        return []
