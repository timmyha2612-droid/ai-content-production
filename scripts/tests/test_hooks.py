"""Hook tests: guard.py decisions (hook JSON on stdin), session_start.py and prompt_nudge.py run quietly."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
ROOT = os.path.dirname(SCRIPTS)
HOOKS = os.path.join(ROOT, "hooks")
GUARD = os.path.join(HOOKS, "guard.py")
SESSION_START = os.path.join(HOOKS, "session_start.py")
NUDGE = os.path.join(HOOKS, "prompt_nudge.py")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from shotcraft import project, stages  # noqa: E402

SID = "test-session-1"


class HookBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-hooks-")
        self.home = os.path.join(self.tmp, "home")
        self.root = os.path.join(self.tmp, "projects")
        os.makedirs(self.home)
        self.env = dict(os.environ)
        self.env["SHOTCRAFT_HOME"] = self.home
        self.env.pop("CLAUDE_SESSION_ID", None)
        self.env.pop("CLAUDE_CODE_SESSION_ID", None)
        self.env.pop("CLAUDE_ENV_FILE", None)
        self.env.pop("SHOTCRAFT_PLUGIN_ROOT", None)
        self._old_home = os.environ.get("SHOTCRAFT_HOME")
        self._old_sid = os.environ.pop("CLAUDE_SESSION_ID", None)
        self._old_csid = os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        os.environ["SHOTCRAFT_HOME"] = self.home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("SHOTCRAFT_HOME", None)
        else:
            os.environ["SHOTCRAFT_HOME"] = self._old_home
        if self._old_sid is not None:
            os.environ["CLAUDE_SESSION_ID"] = self._old_sid
        if self._old_csid is not None:
            os.environ["CLAUDE_CODE_SESSION_ID"] = self._old_csid
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make_project(self, track="full", activate=True):
        proj = project.init_project("Dawn Reel", track, root=self.root)
        if activate:
            project.open_project(proj, SID)
        else:
            for f in (os.path.join(self.home, "active.json"),):
                if os.path.exists(f):
                    os.remove(f)
            sess = os.path.join(self.home, "sessions")
            shutil.rmtree(sess, ignore_errors=True)
        return proj

    def force(self, proj, **statuses):
        st = stages.load_state(proj)
        for k, v in statuses.items():
            st["stages"][k]["status"] = v
        stages.save_state(proj, st)

    def run_hook(self, script, payload, env=None):
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        p = subprocess.run([sys.executable, script], input=raw, capture_output=True, text=True,
                           env=env or self.env, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def guard(self, tool, tool_input, cwd=None):
        payload = {"session_id": SID, "hook_event_name": "PreToolUse", "tool_name": tool,
                   "tool_input": tool_input, "cwd": cwd or self.tmp}
        return self.run_hook(GUARD, payload)

    def bash(self, cmd, cwd=None):
        return self.guard("Bash", {"command": cmd}, cwd)


class GuardGenerationTests(HookBase):
    BLOCKED = [
        "higgsfield generate create nano_banana_2 --prompt 'a beach' --wait",
        "higgsfield --json generate create seedance_2_5 --prompt x",
        "higgsfield generate workflow reframe --video a.mp4",
        "higgsfield upscale --image a.png",
        "higgsfield soul-id create --name Ava --image a.jpg",
        "cd /tmp && higgsfield generate create x --prompt y",
        "ls; higgsfield generate create x",
        "true || (higgsfield upscale a.png)",
        "echo $(higgsfield generate create x --prompt y)",
        "echo \"`higgsfield generate create x`\"",
        "FOO=1 BAR=2 higgsfield generate create x",
        "sudo -u me env A=1 timeout 30 higgsfield generate create x",
        "npx -y @higgsfield/cli generate create x",
        "npx @higgsfield/cli@1.2.0 upscale a.png",
        "npm exec -- @higgsfield/cli generate create x",
        "/usr/local/bin/higgsfield generate create x",
        "bash -lc 'higgsfield generate create x'",
        "eval higgsfield generate create x",
        "cat list.txt | xargs -n1 higgsfield generate create",
        "python3 -c \"import subprocess; subprocess.run(['higgsfield', 'generate', 'create', 'x'])\"",
        "python3 - <<'EOF'\nimport os  # it's fine\nos.system('higgsfield generate create x')\nEOF",
        "higgsfield marketing-studio dtc-ads generate --product p1",
        "echo 'unbalanced; higgsfield generate create x",
    ]
    ALLOWED = [
        "higgsfield generate cost seedance_2_5 --duration 5 --resolution 720p",
        "higgsfield generate cost workflow reframe --duration 7.1",
        "higgsfield generate list --json | jq '.[0]'",
        "higgsfield generate get abc123 --json",
        "higgsfield generate status abc123",
        "higgsfield generate wait abc123",
        "higgsfield model list --json",
        "higgsfield model get seedance_2_5 --json",
        "higgsfield account status --json",
        "higgsfield auth status",
        "higgsfield generate create --help",
        "higgsfield soul-id list",
        "higgsfield --help",
        "grep -rn \"higgsfield generate create\" docs/",
        "git commit -m 'route higgsfield generate create through sc.py'",
        "python3 scripts/sc.py gen submit 05_prompts/S010.md --tier draft --user-said 'go'",
        "ls -la && echo done",
    ]

    def test_raw_generation_blocked_without_project(self):
        for cmd in self.BLOCKED:
            code, _, err = self.bash(cmd)
            self.assertEqual(code, 2, "should block: %r (stderr: %s)" % (cmd, err))
            self.assertIn("sc.py", err)

    def test_reads_and_other_commands_pass(self):
        for cmd in self.ALLOWED:
            code, _, err = self.bash(cmd)
            self.assertEqual(code, 0, "should allow: %r (stderr: %s)" % (cmd, err))

    def test_raw_generation_blocked_with_project(self):
        self.make_project()
        code, _, err = self.bash("higgsfield generate create nano_banana_2 --prompt x")
        self.assertEqual(code, 2)
        self.assertIn("gen submit", err)


class GuardFileTests(HookBase):
    def test_write_project_json_blocked(self):
        proj = self.make_project()
        code, _, err = self.guard("Write", {"file_path": os.path.join(proj, "project.json"), "content": "{}"})
        self.assertEqual(code, 2)
        self.assertIn("sc.py", err)
        code, _, _ = self.guard("Edit", {"file_path": os.path.join(proj, "project.json"),
                                         "old_string": "a", "new_string": "b"})
        self.assertEqual(code, 2)

    def test_project_json_blocked_even_when_not_active(self):
        proj = self.make_project(activate=False)
        code, _, _ = self.guard("Write", {"file_path": os.path.join(proj, "project.json"), "content": "{}"})
        self.assertEqual(code, 2)

    def test_stages_and_qa_blocked(self):
        proj = self.make_project()
        for rel in (".shotcraft/stages.json", ".shotcraft/qa/intake/round-1.json"):
            code, _, _ = self.guard("Write", {"file_path": os.path.join(proj, rel), "content": "{}"})
            self.assertEqual(code, 2, rel)

    def test_stage_folder_before_and_after_open(self):
        proj = self.make_project()
        target = os.path.join(proj, "02_concept", "concepts.md")
        code, _, err = self.guard("Write", {"file_path": target, "content": "x"})
        self.assertEqual(code, 2)
        self.assertIn("stage start concept", err)
        self.force(proj, intake="done", research="done", concept="open")
        code, _, err = self.guard("Write", {"file_path": target, "content": "x"})
        self.assertEqual(code, 0, err)
        self.force(proj, concept="done")
        code, _, err = self.guard("Write", {"file_path": target, "content": "x"})
        self.assertEqual(code, 2)
        self.assertIn("reopen", err)

    def test_relative_path_uses_cwd(self):
        proj = self.make_project()
        code, _, _ = self.guard("Write", {"file_path": "03_script/script.md", "content": "x"}, cwd=proj)
        self.assertEqual(code, 2)
        self.force(proj, intake="done", research="done", concept="done", script="open")
        code, _, err = self.guard("Write", {"file_path": "03_script/script.md", "content": "x"}, cwd=proj)
        self.assertEqual(code, 0, err)
        code, _, _ = self.guard("Write", {"file_path": "03_script/shotlist.md", "content": "x"}, cwd=proj)
        self.assertEqual(code, 2)

    def test_inputs_and_lessons_always_allowed(self):
        proj = self.make_project()
        for rel in ("00_inputs/blender/render-01.png", ".shotcraft/lessons.md"):
            code, _, err = self.guard("Write", {"file_path": os.path.join(proj, rel), "content": "x"})
            self.assertEqual(code, 0, "%s: %s" % (rel, err))

    def test_outside_project_allowed(self):
        self.make_project()
        code, _, err = self.guard("Write", {"file_path": os.path.join(self.tmp, "notes.md"), "content": "x"})
        self.assertEqual(code, 0, err)

    def test_no_active_project_allows_stage_folders(self):
        proj = self.make_project(activate=False)
        code, _, err = self.guard("Write", {"file_path": os.path.join(proj, "02_concept", "c.md"), "content": "x"})
        self.assertEqual(code, 0, err)
        code, _, err = self.guard("NotebookEdit", {"notebook_path": os.path.join(self.tmp, "a.ipynb")})
        self.assertEqual(code, 0, err)

    def test_other_project_json_not_blocked(self):
        self.make_project()
        other = os.path.join(self.tmp, "webapp")
        os.makedirs(other)
        code, _, err = self.guard("Write", {"file_path": os.path.join(other, "project.json"), "content": "{}"})
        self.assertEqual(code, 0, err)

    def test_refine_track_prompts_folder(self):
        proj = self.make_project(track="refine")
        target = os.path.join(proj, "05_prompts", "S010.md")
        code, _, _ = self.guard("Write", {"file_path": target, "content": "x"})
        self.assertEqual(code, 2)
        self.force(proj, refine="open")
        code, _, err = self.guard("Write", {"file_path": target, "content": "x"})
        self.assertEqual(code, 0, err)


class GuardShellWriteTests(HookBase):
    def test_shell_writes_to_records_blocked(self):
        proj = self.make_project()
        blocked = [
            "echo '{}' > project.json",
            "jq '.budget.credits=900' project.json > /tmp/x && mv /tmp/x project.json",
            "echo x >> .shotcraft/qa/intake/round-1.json",
            "cat notes | tee -a .shotcraft/stages.json",
            "sed -i 's/open/done/' .shotcraft/stages.json",
            "rm -f .shotcraft/qa/drafts/round-2.json",
            "cp /tmp/stages.json .shotcraft/stages.json",
            "python3 -c \"import json; json.dump({}, open('.shotcraft/stages.json', 'w'))\"",
            "cat > %s/.shotcraft/qa/x.json <<'EOF'\n{\"verdict\": \"PASS\"}\nEOF" % proj,
        ]
        for cmd in blocked:
            code, _, err = self.bash(cmd, cwd=proj)
            self.assertEqual(code, 2, "should block: %r (%s)" % (cmd, err))
        allowed = [
            "cat project.json",
            "jq . project.json",
            "python3 -c \"import json; print(json.load(open('project.json'))['name'])\"",
            "echo note >> .shotcraft/lessons.md",
            "ls .shotcraft/qa",
            "echo x > 02_concept/concepts.md",
        ]
        for cmd in allowed:
            code, _, err = self.bash(cmd, cwd=proj)
            self.assertEqual(code, 0, "should allow: %r (%s)" % (cmd, err))

    def test_cd_into_project_then_write(self):
        proj = self.make_project()
        code, _, _ = self.bash("cd %s && echo '{}' > project.json" % proj, cwd=self.tmp)
        self.assertEqual(code, 2)


class GuardMcpTests(HookBase):
    def test_mcp_generate_blocked_when_project_active(self):
        self.make_project()
        for name in ("mcp__higgsfield__generate_image", "mcp__claude_ai_Higgsfield__upscaleVideo",
                     "mcp__higgsfield__soul_id_train", "mcp__higgsfield__upload_file"):
            code, _, err = self.guard(name, {"prompt": "x"})
            self.assertEqual(code, 2, name)
            self.assertIn("sc.py", err)
        for name in ("mcp__higgsfield__list_models", "mcp__higgsfield__get_generation_status",
                     "mcp__higgsfield__get_cost"):
            code, _, err = self.guard(name, {})
            self.assertEqual(code, 0, "%s: %s" % (name, err))

    def test_mcp_generate_passes_with_note_without_project(self):
        code, _, err = self.guard("mcp__higgsfield__generate_image", {"prompt": "x"})
        self.assertEqual(code, 0)
        self.assertIn("no shotcraft project", err)


class GuardRobustnessTests(HookBase):
    def test_malformed_input_passes(self):
        for raw in ("", "not json", "[1, 2]", "{\"tool_name\": \"Bash\", \"tool_input\": \"oops\"}",
                    "{\"tool_name\": \"Write\"}", "{\"tool_name\": \"Bash\", \"tool_input\": {\"command\": 5}}"):
            code, _, _ = self.run_hook(GUARD, raw)
            self.assertEqual(code, 0, raw)

    def test_other_tools_pass(self):
        self.make_project()
        code, _, _ = self.guard("Read", {"file_path": "/etc/hosts"})
        self.assertEqual(code, 0)

    def test_broken_stage_state_fails_open(self):
        proj = self.make_project()
        with open(os.path.join(proj, ".shotcraft", "stages.json"), "w") as fh:
            fh.write("{broken")
        code, _, err = self.guard("Write", {"file_path": os.path.join(proj, "02_concept", "c.md"), "content": "x"})
        self.assertEqual(code, 0, err)


class SessionStartTests(HookBase):
    def no_higgsfield_env(self):
        env = dict(self.env)
        bindir = os.path.join(self.tmp, "bin")
        os.makedirs(bindir, exist_ok=True)
        env["PATH"] = bindir
        return env

    def test_silent_without_higgsfield_or_project(self):
        code, out, err = self.run_hook(SESSION_START, {"session_id": SID, "source": "startup"},
                                       env=self.no_higgsfield_env())
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertNotIn("Traceback", out)
        self.assertNotIn("active project", out)

    def test_bad_input_is_silent(self):
        code, out, err = self.run_hook(SESSION_START, "garbage", env=self.no_higgsfield_env())
        self.assertEqual(code, 0)
        self.assertEqual(err, "")

    def test_reports_active_project_and_scout(self):
        proj = self.make_project()
        self.force(proj, intake="open")
        os.makedirs(os.path.join(self.home, "scout"))
        with open(os.path.join(self.home, "scout", "last.json"), "w") as fh:
            json.dump({"timestamp": "2026-11-20T08:00:00+00:00", "new": ["a", "b"], "removed": [], "changed": []},
                      fh)
        code, out, err = self.run_hook(SESSION_START, {"session_id": SID}, env=self.no_higgsfield_env())
        self.assertEqual(code, 0, err)
        self.assertIn("Dawn Reel", out)
        self.assertIn("intake", out)
        self.assertIn("2 new Higgsfield models since 2026-11-20", out)
        self.assertIn("run model-scout", out)


class PromptNudgeTests(HookBase):
    def test_silent_without_project(self):
        code, out, err = self.run_hook(NUDGE, {"session_id": SID, "prompt": "hi"})
        self.assertEqual((code, out, err), (0, "", ""))

    def test_nudge_with_project(self):
        self.make_project()
        code, out, _ = self.run_hook(NUDGE, {"session_id": SID, "prompt": "no, warmer light"})
        self.assertEqual(code, 0)
        self.assertIn("lessons add", out)
        self.assertLess(len(out.strip()), 200)

    def test_bad_input(self):
        code, _, _ = self.run_hook(NUDGE, "{{{")
        self.assertEqual(code, 0)


class HooksJsonTests(unittest.TestCase):
    def test_hooks_json_shape(self):
        with open(os.path.join(HOOKS, "hooks.json")) as fh:
            data = json.load(fh)
        pre = data["hooks"]["PreToolUse"]
        matchers = {h["matcher"] for h in pre}
        self.assertEqual(matchers, {"Bash", "Write|Edit|MultiEdit|NotebookEdit", "mcp__.*[Hh]iggsfield.*"})
        for h in pre:
            self.assertIn("hooks/guard.py", h["hooks"][0]["command"])
            self.assertIn("${CLAUDE_PLUGIN_ROOT}", h["hooks"][0]["command"])
        self.assertIn("session_start.py", data["hooks"]["SessionStart"][0]["hooks"][0]["command"])
        self.assertIn("prompt_nudge.py", data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"])


if __name__ == "__main__":
    unittest.main()
