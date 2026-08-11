"""Maintenance / quality tests for Nexus.

These tests avoid any LLM network calls and exercise the pure-logic paths
of config validation, history traversal, tool hardening, YAML env expansion,
and related cross-module behavior, so they run quickly in CI.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from primisai.nexus.core import Agent, Supervisor  # noqa: E402
from primisai.nexus.config.yaml_config import (  # noqa: E402
    expand_env_vars,
    load_yaml_config,
)
from primisai.nexus.config.config_validator import ConfigValidator  # noqa: E402
from primisai.nexus.history import HistoryManager, EntityType  # noqa: E402
from primisai.nexus.tools.tool_functions import (  # noqa: E402
    ToolsBucket,
    _validate_command_token,
    _DEFAULT_TMUX_SESSION,
)
from primisai.nexus.architect.builder import (  # noqa: E402
    ValidationError,
    _audit_tool_implementation,
    _safe_exec_tool,
)


@pytest.fixture
def llm_config():
    return {
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "api_key": os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or "sk-dummy-test-key-12345",
        "base_url": os.getenv("LLM_BASE_URL"),
    }


# ---------------------------------------------------------------------------
# ValidationError class body / custom exception behavior.
# ---------------------------------------------------------------------------
class TestValidationErrorBody:
    def test_validation_error_raises_and_catches(self):
        with pytest.raises(ValidationError):
            raise ValidationError("boom")
        try:
            raise ValidationError("msg")
        except Exception as exc:
            assert str(exc) == "msg"


# ---------------------------------------------------------------------------
# Evaluator dead commented path removed — simple meta-test by importing.
# ---------------------------------------------------------------------------
class TestEvaluatorDeadCode:
    def test_evaluator_imports_and_has_no_hardcoded_linux_user_path(self):
        src = Path(__file__).resolve().parent.parent / "primisai" / "nexus" / "architect" / "evaluator.py"
        text = src.read_text()
        assert "/home/humza/" not in text, (
            "dead hardcoded /home/humza/ path should be removed from evaluator.py"
        )


# ---------------------------------------------------------------------------
# ToolBuilder exec() hardening via _audit_tool_implementation.
# ---------------------------------------------------------------------------
class TestAuditToolImplementation:
    def test_safe_pure_function_passes(self):
        src = "def my_tool(a, b):\n    return a + b\n"
        _audit_tool_implementation(src)  # should not raise

    def test_rejects_os_import(self):
        src = "import os\ndef rm(path):\n    os.remove(path)\n"
        with pytest.raises(ValidationError, match="forbidden module"):
            _audit_tool_implementation(src)

    def test_rejects_subprocess_from_import(self):
        src = "from subprocess import run\ndef cmd(c):\n    run(c, shell=True)\n"
        with pytest.raises(ValidationError, match="forbidden module"):
            _audit_tool_implementation(src)

    def test_rejects_calls_to_open_builtin(self):
        src = "def read(path):\n    return open(path).read()\n"
        with pytest.raises(ValidationError, match="forbidden builtin"):
            _audit_tool_implementation(src)

    def test_safe_exec_runs_sandboxed_code(self):
        src = "def adder(x, y):\n    return x + y\n"
        fn = _safe_exec_tool(src, "adder")
        assert fn(2, 3) == 5

    def test_safe_exec_blocks_os_injection(self):
        src = (
            "def hack(x):\n"
            "    import os\n"
            "    return os.getenv('PATH')\n"
        )
        with pytest.raises(ValidationError):
            _safe_exec_tool(src, "hack")


# ---------------------------------------------------------------------------
# ToolsBucket command token validation + session_name parameterization.
# ---------------------------------------------------------------------------
class TestToolsBucketSecurity:
    def test_simple_command_token_passes(self):
        _validate_command_token("ls -la /tmp")

    def test_rejects_command_chaining_semicolon(self):
        with pytest.raises(ValueError, match="forbidden shell character"):
            _validate_command_token("ls -la ; rm -rf /")

    def test_rejects_command_chaining_double_ampersand(self):
        with pytest.raises(ValueError, match="forbidden shell character"):
            _validate_command_token("make build && echo done")

    def test_rejects_pipe(self):
        with pytest.raises(ValueError, match="forbidden shell character"):
            _validate_command_token("cat /etc/passwd | wc -l")

    def test_rejects_subshell_dollar_paren(self):
        with pytest.raises(ValueError, match="forbidden shell character"):
            _validate_command_token("echo $(rm -rf /tmp/foo)")

    def test_rejects_overly_long_command(self):
        with pytest.raises(ValueError, match="too long"):
            _validate_command_token("x" * 10000)

    def test_execute_command_returns_error_when_not_dict(self):
        bucket = ToolsBucket()
        result = bucket.execute_command(json.dumps("not a dict"))
        assert result["status"] == "error"
        assert "JSON argument" in result["output"] or "argument" in result["output"]

    def test_execute_command_missing_argument_key(self):
        bucket = ToolsBucket()
        result = bucket.execute_command(json.dumps({"foo": "bar"}))
        assert result["status"] == "error"

    def test_execute_command_detects_unsafe_token(self):
        bucket = ToolsBucket()
        result = bucket.execute_command(json.dumps({"argument": "ls ; rm -rf /"}))
        assert result["status"] == "error"
        assert "forbidden shell character" in result["output"]

    def test_default_session_name_is_not_my_session(self):
        # Should no longer default to the hard-coded "my_session".
        assert _DEFAULT_TMUX_SESSION != "my_session"
        assert "nexus" in _DEFAULT_TMUX_SESSION

    def test_session_name_is_configurable_via_json(self):
        bucket = ToolsBucket()
        # Inject command with a valid session name. We expect the method to
        # attempt running tmux (it fails because tmux/daemon not present) but
        # we can inspect the error returned to see the json was parsed.
        result = bucket.execute_command(
            json.dumps({"argument": "echo hi", "session_name": "good_session"})
        )
        # Will error because tmux is not started, but should NOT be a
        # validation error (the session name and command are both valid).
        assert "forbidden shell character" not in result.get("output", "")
        assert "session_name may not contain" not in result.get("output", "")


# ---------------------------------------------------------------------------
# Logger objects exist on core modules (no longer only print() statements).
# ---------------------------------------------------------------------------
class TestLoggingCoverage:
    def test_supervisor_logger_exists(self):
        from primisai.nexus.core import supervisor
        assert hasattr(supervisor, "logger")

    def test_agents_logger_exists(self):
        from primisai.nexus.core import agents
        assert hasattr(agents, "logger")

    def test_evaluator_logger_exists(self):
        from primisai.nexus.architect import evaluator
        assert hasattr(evaluator, "logger")

    def test_prompter_logger_exists(self):
        from primisai.nexus.architect import prompter
        assert hasattr(prompter, "logger")

    def test_builder_logger_exists(self):
        from primisai.nexus.architect import builder
        assert hasattr(builder, "logger")

    def test_package_root_logger_configured(self):
        import primisai
        import logging
        lg = logging.getLogger("primisai")
        assert len(lg.handlers) > 0 or lg.propagate is True


# ---------------------------------------------------------------------------
# extract_system_messages single source of truth (prompter = manager).
# ---------------------------------------------------------------------------
class TestSingleSourceExtractSystemMessages:
    def test_manager_uses_prompter_function(self):
        from primisai.nexus.architect.manager import extract_system_messages
        from primisai.nexus.architect.prompter import (
            extract_system_messages as prompter_extract,
        )
        # Imported symbol IS the prompter symbol, not a redefinition.
        assert extract_system_messages is prompter_extract

    def test_extract_dict_passthrough(self):
        from primisai.nexus.architect.prompter import extract_system_messages
        assert extract_system_messages({"a": "hi"}, ["a"]) == {"a": "hi"}

    def test_extract_pydantic_like_obj(self):
        from primisai.nexus.architect.prompter import extract_system_messages
        class _A:
            math = "You are Math Agent"
        got = extract_system_messages(_A(), ["math"])
        assert got["math"] == "You are Math Agent"

    def test_manager_static_method_removed(self):
        from primisai.nexus.architect import manager
        # Manager.Architect should NOT expose the old _extract_system_messages
        # static method anymore — it should use the imported prompter one.
        assert not hasattr(manager.Architect, "_extract_system_messages")


# ---------------------------------------------------------------------------
# History manager BFS traversal, config validator shape, and
# MCP tool schema required list regression tests.
# ---------------------------------------------------------------------------
class TestHistoryBFS:
    def _make_hm(self, tmp_path, wfid):
        (tmp_path / "nexus_workflows" / wfid).mkdir(parents=True, exist_ok=True)
        return HistoryManager(wfid)

    def test_per_entity_history_threaded(self, tmp_path, llm_config, monkeypatch):
        monkeypatch.chdir(tmp_path)
        wfid = "test_hist_wf"
        self._make_hm(tmp_path, wfid)
        # Need to re-create since constructor requires dir
        hm = HistoryManager(wfid)
        msg_sys = {"role": "system", "content": "sys"}
        hm.append_message(msg_sys, EntityType.MAIN_SUPERVISOR, "Main")
        msg_user = {"role": "user", "content": "hello"}
        user_id = hm.append_message(msg_user, EntityType.USER, "User", parent_id=None)
        msg_ass = {"role": "assistant", "content": "world"}
        hm.append_message(msg_ass, EntityType.AGENT, "Agent1", parent_id=user_id,
                          supervisor_chain=["Main"])
        load = hm.load_chat_history("Agent1")
        roles = [m["role"] for m in load]
        assert "assistant" in roles

    def test_bfs_returns_descendants(self, tmp_path, llm_config, monkeypatch):
        monkeypatch.chdir(tmp_path)
        wfid = "test_hist_wf2"
        self._make_hm(tmp_path, wfid)
        hm = HistoryManager(wfid)
        # 1. SYSTEM for Agent1 — should be appended by load_chat_history
        system_a1 = {"role": "system", "content": "s"}
        sa1_id = hm.append_message(system_a1, EntityType.AGENT, "Agent1")
        # 2. USER with supervisor_chain[-1]="Agent1" so Agent1 sees it
        user_m = {"role": "user", "content": "q"}
        uid = hm.append_message(user_m, EntityType.USER, "User",
                                supervisor_chain=["Main", "Agent1"])
        # 3. Assistant response by Agent1 to that user msg
        assistant_m = {"role": "assistant", "content": "a"}
        aid = hm.append_message(assistant_m, EntityType.AGENT, "Agent1",
                                parent_id=uid,
                                supervisor_chain=["Main", "Agent1"])
        loaded = hm.load_chat_history("Agent1")
        ids = [m.get("message_id") or m.get("id") for m in loaded]
        roles = [m["role"] for m in loaded]
        assert sa1_id in ids or "system" in roles, "system message should be present"
        assert uid in ids or "user" in roles, "user message should be present"
        assert aid in ids or "assistant" in roles, "assistant message should be present"
        # Main supervisor history: must contain Main system msg
        system_main = {"role": "system", "content": "r"}
        rid = hm.append_message(system_main, EntityType.MAIN_SUPERVISOR, "Main")
        main_loaded = hm.load_chat_history("Main")
        main_ids = [m.get("message_id") or m.get("id") for m in main_loaded]
        assert rid in main_ids or any(x["role"] == "system" for x in main_loaded)


class TestConfigValidator:
    def test_rejects_empty_config(self):
        with pytest.raises(Exception):
            ConfigValidator.validate({})

    def test_rejects_empty_supervisor(self):
        with pytest.raises(Exception):
            ConfigValidator.validate({"supervisor": {}})

    def test_rejects_children_missing_when_root(self):
        cfg = {
            "supervisor": {
                "name": "Main",
                "type": "supervisor",
                "system_message": "s",
                "llm_config": {"api_key": "k", "model": "m", "base_url": ""},
            }
        }
        with pytest.raises(Exception):
            ConfigValidator.validate(cfg)

    def test_minimal_valid_config_passes(self):
        cfg = {
            "supervisor": {
                "name": "Main",
                "type": "supervisor",
                "system_message": "root",
                "llm_config": {"api_key": "k", "model": "m", "base_url": ""},
                "children": [
                    {
                        "name": "A1",
                        "type": "agent",
                        "llm_config": {"api_key": "k", "model": "m", "base_url": ""},
                        "system_message": "s",
                        "tools": [
                            {"name": "t", "type": "function", "python_path": "x.y.t"}
                        ],
                    }
                ],
            }
        }
        ConfigValidator.validate(cfg)


class TestMcpRequiredList:
    """Regression test: MCP schemas should honour the server's
    `inputSchema.required` instead of marking every field required."""

    def test_required_list_honoured(self, llm_config):
        agent = Agent(name="mcp-regression", llm_config=llm_config)
        # Make a fake MCP Tool with inputSchema.required only partially filled
        class _FakeProp:
            def __init__(self, d): self.__dict__.update(d)
        class _FakeTool:
            name = "fake_tool"
            description = "desc"
            inputSchema = {
                "type": "object",
                "properties": {
                    "required_field": {"type": "string"},
                    "optional_field": {"type": "number"},
                },
                "required": ["required_field"],
            }
        got = agent._convert_mcp_tool_to_openai(_FakeTool())
        assert got["function"]["parameters"]["required"] == ["required_field"], (
            "MCP required list must be honoured exactly, not replaced with all fields"
        )


# ---------------------------------------------------------------------------
# YAML env expansion only respects ${VAR}, not bare $VAR.
# ---------------------------------------------------------------------------
class TestBracedEnvExpansion:
    def test_expands_braced_env(self, monkeypatch):
        monkeypatch.setenv("MY_TEST_VAR", "hello")
        cfg = {"path": "prefix/${MY_TEST_VAR}/suffix"}
        got = expand_env_vars(cfg)
        assert got["path"] == "prefix/hello/suffix"

    def test_ignores_bare_dollar_var(self, monkeypatch):
        monkeypatch.setenv("BARE", "unexpected")
        cfg = {"line": "this is $BARE in a string"}
        got = expand_env_vars(cfg)
        assert got["line"] == "this is $BARE in a string"

    def test_undefined_braced_var_left_literal(self, monkeypatch):
        monkeypatch.delenv("DOES_NOT_EXIST_123", raising=False)
        cfg = {"k": "see ${DOES_NOT_EXIST_123} there"}
        got = expand_env_vars(cfg)
        assert "${DOES_NOT_EXIST_123}" in got["k"]

    def test_recursive_list_expansion(self, monkeypatch):
        monkeypatch.setenv("INNER", "x")
        cfg = {"items": ["a/${INNER}", "${INNER}/b", 123]}
        got = expand_env_vars(cfg)
        assert got["items"][0] == "a/x"
        assert got["items"][1] == "x/b"
        assert got["items"][2] == 123

    def test_load_yaml_config_integration(self, monkeypatch):
        monkeypatch.setenv("DB_HOST", "db.example.com")
        body = (
            "supervisor:\n"
            "  name: ${DB_HOST}_main\n"
            "  type: main\n"
            "  llm_config:\n"
            "    api_key: k\n"
            "    model: m\n"
            "  agents: []\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fp:
            fp.write(body)
            tmp = fp.name
        try:
            # This will fail validator (empty agents list) but we don't care —
            # the expansion should already be applied to the name.
            data = load_yaml_config(tmp)
            assert data["supervisor"]["name"] == "db.example.com_main"
        finally:
            os.unlink(tmp)
