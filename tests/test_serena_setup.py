import json
import os
from pathlib import Path

import yaml

from uncoded.serena_setup import (
    SERENA_ALLOWED_TOOLS,
    SERENA_VERSION,
    setup,
)

REPO_ROOT = Path(__file__).parent.parent

# Tools Serena exposes that we strip from the project. Kept in the test
# module (not the source) so the test asserts the contract independently
# of the constant it's validating: a typo or silent removal in
# SERENA_PROJECT_YML shows up here.
EXPECTED_EXCLUDED_TOOLS = {
    "execute_shell_command",
    "list_memories",
    "read_memory",
    "write_memory",
    "edit_memory",
    "delete_memory",
    "rename_memory",
    "onboarding",
    "check_onboarding_performed",
    "open_dashboard",
}

# Full argv that ``uncoded setup`` should write into the Serena entry of
# ``.mcp.json``. Kept in the test module (not the source) so the test
# asserts the contract independently of the constant it's validating: a
# typo, drop, or re-order in MCP_SERVER_SERENA["args"] shows up here.
# Order is significant — these are CLI args, and ``--from <pkg>`` /
# ``--open-web-dashboard false`` are paired tokens.
EXPECTED_MCP_ARGS = [
    "--from",
    f"serena-agent=={SERENA_VERSION}",
    "serena",
    "start-mcp-server",
    "--context",
    "claude-code",
    "--transport",
    "stdio",
    "--project-from-cwd",
    "--open-web-dashboard",
    "false",
]


class TestSetup:
    def _run(self, tmp_path, name="my-app"):
        (tmp_path / "pyproject.toml").write_text(f'[project]\nname = "{name}"\n')
        os.chdir(tmp_path)
        return setup()

    def test_creates_all_three_files(self, tmp_path):
        assert self._run(tmp_path) == 0
        assert (tmp_path / ".mcp.json").exists()
        assert (tmp_path / ".serena" / "project.yml").exists()
        assert (tmp_path / ".claude" / "settings.json").exists()

    def test_mcp_json_is_valid_and_pins_version(self, tmp_path):
        self._run(tmp_path)
        data = json.loads((tmp_path / ".mcp.json").read_text())
        serena = data["mcpServers"]["serena"]
        assert serena["command"] == "uvx"
        assert serena["args"] == EXPECTED_MCP_ARGS

    def test_serena_project_yml_uses_ty_and_ignores_uncoded(self, tmp_path):
        self._run(tmp_path, name="my-app")
        data = yaml.safe_load((tmp_path / ".serena" / "project.yml").read_text())
        assert data["project_name"] == "my-app"
        assert data["languages"] == ["python_ty"]
        assert ".uncoded" in data["ignored_paths"]
        assert set(data["excluded_tools"]) == EXPECTED_EXCLUDED_TOOLS
        assert "initial_instructions" not in data["excluded_tools"]

    def test_claude_settings_enables_serena_and_allowlists_tools(self, tmp_path):
        self._run(tmp_path)
        data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
        assert data["enabledMcpjsonServers"] == ["serena"]
        assert set(data["permissions"]["allow"]) == set(SERENA_ALLOWED_TOOLS)
        assert "mcp__serena__initial_instructions" in data["permissions"]["allow"]

    def test_idempotent(self, tmp_path):
        self._run(tmp_path)
        first_mcp = (tmp_path / ".mcp.json").read_text()
        first_serena = (tmp_path / ".serena" / "project.yml").read_text()
        first_claude = (tmp_path / ".claude" / "settings.json").read_text()
        self._run(tmp_path)
        assert (tmp_path / ".mcp.json").read_text() == first_mcp
        assert (tmp_path / ".serena" / "project.yml").read_text() == first_serena
        assert (tmp_path / ".claude" / "settings.json").read_text() == first_claude

    def test_merges_into_existing_mcp_json(self, tmp_path):
        mcp_path = tmp_path / ".mcp.json"
        mcp_path.write_text(
            json.dumps({"mcpServers": {"other": {"command": "other-cmd", "args": []}}})
        )
        self._run(tmp_path)
        data = json.loads(mcp_path.read_text())
        assert "other" in data["mcpServers"]
        assert "serena" in data["mcpServers"]

    def test_refreshes_stale_serena_entry_in_mcp_json(self, tmp_path):
        mcp_path = tmp_path / ".mcp.json"
        stale = {
            "mcpServers": {
                "serena": {
                    "command": "uvx",
                    "args": ["--from", "serena-agent==0.0.1", "serena"],
                }
            }
        }
        mcp_path.write_text(json.dumps(stale))
        self._run(tmp_path)
        args = json.loads(mcp_path.read_text())["mcpServers"]["serena"]["args"]
        assert f"serena-agent=={SERENA_VERSION}" in args
        assert "serena-agent==0.0.1" not in args

    def test_merges_into_existing_claude_settings(self, tmp_path):
        claude_path = tmp_path / ".claude" / "settings.json"
        claude_path.parent.mkdir()
        claude_path.write_text(
            json.dumps(
                {
                    "enabledMcpjsonServers": ["other"],
                    "permissions": {"allow": ["Bash(ls:*)"]},
                }
            )
        )
        self._run(tmp_path)
        data = json.loads(claude_path.read_text())
        assert set(data["enabledMcpjsonServers"]) == {"other", "serena"}
        assert "Bash(ls:*)" in data["permissions"]["allow"]
        for tool in SERENA_ALLOWED_TOOLS:
            assert tool in data["permissions"]["allow"]

    def test_does_not_overwrite_existing_serena_project_yml(self, tmp_path):
        serena_path = tmp_path / ".serena" / "project.yml"
        serena_path.parent.mkdir()
        original = 'project_name: "custom"\nlanguages: ["python"]\n'
        serena_path.write_text(original)
        self._run(tmp_path)
        assert serena_path.read_text() == original

    def test_does_not_duplicate_on_second_merge(self, tmp_path):
        self._run(tmp_path)
        self._run(tmp_path)
        mcp = json.loads((tmp_path / ".mcp.json").read_text())
        assert list(mcp["mcpServers"].keys()) == ["serena"]
        claude = json.loads((tmp_path / ".claude" / "settings.json").read_text())
        assert claude["enabledMcpjsonServers"].count("serena") == 1
        for tool in SERENA_ALLOWED_TOOLS:
            assert claude["permissions"]["allow"].count(tool) == 1

    def test_setup_uses_cwd_name_when_no_pyproject(self, tmp_path):
        os.chdir(tmp_path)
        setup()
        data = yaml.safe_load((tmp_path / ".serena" / "project.yml").read_text())
        assert data["project_name"] == tmp_path.name


class TestRepoDogfooding:
    """Catch drift between ``uncoded setup``'s templates and this repo's own config.

    uncoded's own LSP setup is generated by ``uncoded setup``. These tests
    assert the invariants the templates are supposed to produce, so a
    change to a template constant (``SERENA_VERSION``, ``SERENA_ALLOWED_TOOLS``,
    etc.) that isn't followed by re-running ``uncoded setup`` against
    this repo fails loudly instead of silently drifting.
    """

    def test_repo_mcp_json_pins_same_serena_version(self):
        mcp = json.loads((REPO_ROOT / ".mcp.json").read_text())
        args = mcp["mcpServers"]["serena"]["args"]
        assert f"serena-agent=={SERENA_VERSION}" in args

    def test_repo_claude_settings_allowlists_every_serena_tool(self):
        settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())
        missing = set(SERENA_ALLOWED_TOOLS) - set(settings["permissions"]["allow"])
        assert not missing, (
            f"repo's .claude/settings.json is missing allowlist entries "
            f"that `uncoded setup` would write: {sorted(missing)}"
        )

    def test_repo_serena_project_yml_matches_template_contract(self):
        data = yaml.safe_load((REPO_ROOT / ".serena" / "project.yml").read_text())
        assert data["languages"] == ["python_ty"]
        assert ".uncoded" in data["ignored_paths"]
        assert set(data["excluded_tools"]) == EXPECTED_EXCLUDED_TOOLS
