import time
import logging
from typing import Any, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute agent-specific domain logic."""
        pass

    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Wrap execution with telemetry and structured logging."""
        start_time = time.time()
        logger.info(f"Agent [{self.name}] starting execution...")
        try:
            result = self.run(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000.0
            logger.info(f"Agent [{self.name}] completed successfully in {duration_ms:.2f}ms.")
            result["_agent_telemetry"] = {
                "agent_name": self.name,
                "duration_ms": duration_ms,
                "status": "SUCCESS"
            }
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            logger.error(f"Agent [{self.name}] failed after {duration_ms:.2f}ms with error: {e}", exc_info=True)
            raise e
