"""Run the audit agent: the agent loop and number checker in agent/, with the Mirage tools."""

from pathlib import Path

from agent import tools
from agent.loop import run_agent

PROMPT_VERSION = "audit_v1"
SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md").read_text()


def run_audit(question: str, model=None, setting: str | None = None) -> dict:
    result = run_agent(question, model=model, setting=setting, toolset=tools.AuditToolset(), system_prompt=SYSTEM_PROMPT,
                       prompt_version=PROMPT_VERSION)
    result["proposals"] = [row for t in result["tool_calls"] if t["tool"] == "propose_action"
                           for row in t["output"].get("rows", [])]
    return result
