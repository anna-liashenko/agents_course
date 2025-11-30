"""
Observability utilities for Pedagogue AI.
Provides structured logging and tracing for agent interactions.
"""

import logging
import structlog
from datetime import datetime
from typing import Any, Dict, Optional
import json


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically module name)
        
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


class AgentTracer:
    """Traces agent-to-agent calls and tool usage."""
    
    def __init__(self):
        self.logger = get_logger("agent_tracer")
        self.traces: list[Dict[str, Any]] = []
    
    def trace_agent_call(
        self, 
        agent_name: str, 
        action: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Trace an agent action.
        
        Args:
            agent_name: Name of the agent
            action: Action being performed
            details: Additional details about the action
        """
        trace_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "details": details or {}
        }
        self.traces.append(trace_entry)
        
        self.logger.info(
            "agent_action",
            agent=agent_name,
            action=action,
            **trace_entry["details"]
        )
    
    def trace_tool_call(
        self,
        agent_name: str,
        tool_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Trace a tool invocation.
        
        Args:
            agent_name: Name of the agent using the tool
            tool_name: Name of the tool being used
            inputs: Tool input parameters
            outputs: Tool output/results
        """
        trace_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "tool": tool_name,
            "inputs": inputs or {},
            "outputs": outputs or {}
        }
        self.traces.append(trace_entry)
        
        self.logger.info(
            "tool_invocation",
            agent=agent_name,
            tool=tool_name,
            inputs=inputs,
            has_output=outputs is not None
        )
    
    def get_traces(self) -> list[Dict[str, Any]]:
        """Get all traces."""
        return self.traces
    
    def export_traces(self, filepath: str) -> None:
        """Export traces to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.traces, f, indent=2, ensure_ascii=False)
        self.logger.info("traces_exported", filepath=filepath, count=len(self.traces))


# Global tracer instance
tracer = AgentTracer()
