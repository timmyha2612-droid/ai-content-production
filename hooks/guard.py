#!/usr/bin/env python3
"""shotcraft PreToolUse guard (SPEC section 7).

Reads the hook JSON on stdin: {"session_id", "tool_name", "tool_input": {"command" | "file_path" | ...}, "cwd"}.
Exit 2 with a reason on stderr blocks the call. Exit 0 lets it through.

Rules:
  1. Raw Higgsfield generation from Bash is always blocked, project or not (pure string matching, no
     project lookup): `higgsfield generate create ...`, `higgsfield generate <anything but
     cost|list|get|status|wait>`, `higgsfield upscale ...`, `higgsfield soul-id create ...`, plus
     `higgsfield product-photoshoot <job>` and `higgsfield marketing-studio ... generate`. It finds the call
     inside pipelines, &&, ;, subshells, $(...), backticks, env prefixes, sudo/env/time/timeout wrappers,
     `npx @higgsfield/cli`, `bash -c "..."`, eval, and python/node one-liners or heredocs.
     Reads pass: model list/get, generate cost/list/get/status/wait, account, auth status, --help.
  2. Higgsfield MCP tools whose name holds generate, create, upscale, edit, train or upload are blocked while
     a project is active. With no active project they pass with a note on stderr.
  3. project.json (of a shotcraft project), .shotcraft/stages.json and anything under .shotcraft/qa/ change
     only through sc.py: Write/Edit/MultiEdit/NotebookEdit are blocked, and so are the shell writes the guard
     can see (> >> redirects, tee, sed -i, perl -i, rm, mv, cp/install/ln/rsync destinations, dd of=,
     truncate, sponge, and python/node one-liners that open them for writing).
  4. Write/Edit into a stage folder of the active project is blocked until that stage is open
     (stages.path_writable holds the whole rule; 00_inputs/ and .shotcraft/lessons.md are always allowed).
Fail open: with no active project rules 2 and 4 pass, and any internal error prints a note and exits 0.
"""
import json
import os
import re
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(PLUGIN_ROOT, "scripts")
SC = os.path.join(SCRIPTS, "sc.py")

FILE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
MCP_HIGGSFIELD = re.compile(r"^mcp__.*[Hh]iggsfield.*")
MCP_WRITE_WORDS = ("generate", "create", "upscale", "edit", "train", "upload")

# higgsfield generate <sub>: these subcommands only read
GEN_READS = {"cost", "list", "get", "status", "wait"}
# product-photoshoot <sub> words that only read
GENERIC_READS = {"list", "get", "status", "wait", "cost", "show", "describe", "info", "fetch", "modes",
                 "presets", "help"}
# global flags that take a value (so the value is not read as a subcommand)
VALUE_FLAGS = {"--wait-timeout", "--wait-interval", "--profile", "--workspace", "--output", "-o"}

WRAPPERS = {"sudo", "doas", "env", "time", "nohup", "exec", "command", "builtin", "nice", "ionice", "stdbuf",
            "caffeinate", "unbuffer", "xargs", "watch", "timeout", "gtimeout", "then", "do", "else", "elif",
            "if", "while", "until", "!", "{", "}", "noglob", "chronic", "script"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish", "ash"}
INTERPRETERS = re.compile(r"^(python[\d.]*|pypy[\d.]*|node|nodejs|deno|bun|perl|ruby|php|osascript)$")
NPX_LIKE = {"npx", "bunx", "pnpx"}
NPM_LIKE = {("npm", "exec"), ("npm", "x"), ("pnpm", "dlx"), ("pnpm", "exec"), ("yarn", "dlx"), ("yarn", "exec"),
            ("bun", "x")}

REDIRECTS = {">", ">>", ">|", "&>", "&>>", "<>", ">&"}
SEPARATORS = {";", "&", "&&", "|", "||", "|&", "(", ")", ";;", "\n"}

HF_WORD = re.compile(r"(?<![\w.-])(?:higgsfield|higgsfield-cli|@higgsfield/cli(?:@[\w.^~-]+)?)(?![\w/-])")
PROTECTED_TEXT = re.compile(r"\.shotcraft/(?:stages\.json|qa\b)|(?<![\w.-])project\.json")
CODE_WRITE = re.compile(
    r"open\s*\([^)]*?['\"][rwab+xt]*[wax+][rwab+xt]*['\"]|write_text|write_bytes|json\.dump\s*\(|\.write\s*\(|"
    r"shutil\.(?:copy\w*|move|rmtree)|os\.(?:remove|unlink|rename|replace|truncate)|\.unlink\s*\(|"
    r"\.rename\s*\(|\.replace\s*\(\s*['\"/\w]|writeFile|appendFile|fs\.(?:rm|unlink|rename|copyFile)|"
    r"File\.(?:write|open)|>>?\s*['\"]")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][\w-]*)\1")

GEN_HELP = ("Raw Higgsfield generation is blocked. shotcraft runs every generation through its own command, so "
            "the stage, budget and rights checks apply:\n"
            "  python3 \"%s\" gen estimate <card> --tier board|draft|final|upscale\n"
            "  python3 \"%s\" gen submit <card> --tier <tier> [--user-said \"...\"]\n"
            "Reads are fine: higgsfield model list/get, generate cost/list/get/status/wait, account, auth status, "
            "--help." % (SC, SC))
PROTECTED_HELP = ("%s changes only through sc.py (sc.py stage ..., sc.py qa record ..., sc.py asset ..., "
                  "sc.py gen ...). Do not edit it by hand.")


class Block(Exception):
    """A rule said no. The message goes back to Claude."""


def note(msg):
    try:
        sys.stderr.write("shotcraft guard: %s\n" % msg)
    except Exception:
        pass


# ------------------------------------------------------------------ raw generation (string matching only)

def _positionals(args):
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        if a.startswith("-"):
            if a in VALUE_FLAGS:
                skip = True
            continue
        out.append(a)
    return out


def hf_decision(args):
    """args = the words after `higgsfield`. Returns a block reason, or None when the call only reads."""
    words = [a.strip("'\",[]") for a in args]
    words = [w for w in words if w]
    if any(w in ("--help", "-h", "help") for w in words):
        return None
    pos = [p.lower() for p in _positionals(words)]
    if not pos:
        return None
    sub = pos[0]
    nxt = pos[1] if len(pos) > 1 else None
    if sub == "generate":
        if nxt is None or nxt in GEN_READS:
            return None
        return "higgsfield generate %s" % nxt
    if sub == "upscale":
        return "higgsfield upscale"
    if sub == "soul-id" and nxt in ("create", "train"):
        return "higgsfield soul-id %s" % nxt
    if sub == "product-photoshoot" and nxt is not None and nxt not in GENERIC_READS:
        return "higgsfield product-photoshoot %s" % nxt
    if sub == "marketing-studio" and "generate" in pos[1:]:
        return "higgsfield marketing-studio ... generate"
    return None


def _is_hf_command(word):
    w = word.strip("'\"")
    base = w.rsplit("/", 1)[-1]
    if base in ("higgsfield", "higgsfield-cli"):
        return True
    return bool(re.match(r"^@higgsfield/cli(@[\w.^~-]+)?$", w))


def loose_gen_scan(text):
    """Find `higgsfield <words>` anywhere in free text (python lists, os.system strings, heredoc bodies)."""
    for m in HF_WORD.finditer(text or ""):
        tail = text[m.end():m.end() + 160]
        tail = re.split(r"[;&|\n)`]", tail, 1)[0]
        words = re.findall(r"--?[\w-]+(?:=\S+)?|[A-Za-z][\w-]*", tail)
        why = hf_decision(words)
        if why:
            return why
    return None


# ------------------------------------------------------------------ shell parsing

def strip_heredocs(cmd):
    """Returns (command without heredoc bodies, [(marker line, body)])."""
    lines = (cmd or "").split("\n")
    out, bodies, i = [], [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        marks = [m.group(2) for m in HEREDOC.finditer(line)]
        i += 1
        for term in marks:
            body = []
            while i < len(lines) and lines[i].strip() != term:
                body.append(lines[i])
                i += 1
            i += 1  # the terminator line
            bodies.append((line, "\n".join(body)))
    return "\n".join(out), bodies


def tokenize(cmd):
    """shlex words with shell punctuation split out. Newlines and backticks become separators.
    Raises ValueError on unbalanced quotes."""
    text = cmd.replace("\\\n", " ").replace("\n", " ; ").replace("`", " ( ")
    lex = shlex.shlex(text, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def segments(tokens):
    """Split tokens into simple commands. Redirect operators stay inside their segment."""
    segs, cur = [], []
    for t in tokens:
        if t in SEPARATORS or t == "$":
            if cur:
                segs.append(cur)
            cur = []
            continue
        if t.endswith("$") and t != "$" and not t.startswith("$"):
            # 'x$' before '(' from 'x$(...)': keep the word, the '(' splits next
            t = t[:-1]
            if t:
                cur.append(t)
            continue
        cur.append(t)
    if cur:
        segs.append(cur)
    return segs


_NUMERIC = re.compile(r"^\d+(\.\d+)?[smhd]?$")
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def unwrap(words):
    """Drop env assignments and wrapper commands. Returns (words, is_higgsfield)."""
    w = list(words)
    for _ in range(12):
        while w and _ASSIGN.match(w[0]):
            w.pop(0)
        if not w:
            return w, False
        head = w[0].rsplit("/", 1)[-1]
        if head in WRAPPERS:
            w.pop(0)
            while w and (w[0].startswith("-") or _ASSIGN.match(w[0]) or _NUMERIC.match(w[0])):
                opt = w.pop(0)
                if head in ("sudo", "doas") and opt in ("-u", "-g", "-C", "-D"):
                    if w:
                        w.pop(0)
            continue
        if head in NPX_LIKE or (len(w) > 1 and (head, w[1]) in NPM_LIKE):
            w.pop(0)
            if head not in NPX_LIKE:
                w.pop(0)
            while w and (w[0].startswith("-")):
                opt = w.pop(0)
                if opt in ("-p", "--package", "-c", "--call") and w:
                    val = w.pop(0)
                    if _is_hf_command(val):
                        while w and w[0].startswith("-"):
                            w.pop(0)
                        if w and _is_hf_command(w[0]):
                            w.pop(0)
                        return w, True
                    if opt in ("-c", "--call"):
                        return ["__code__", val], False
                elif opt.startswith("--package="):
                    if _is_hf_command(opt.split("=", 1)[1]):
                        if w and _is_hf_command(w[0]):
                            w.pop(0)
                        return w, True
            if w and w[0] == "--":
                w.pop(0)
            continue
        break
    if w and _is_hf_command(w[0]):
        return w[1:], True
    return w, False


def shell_code(words):
    """For `bash -c CODE` / `eval ...`: the code string, else None."""
    if not words:
        return None
    head = words[0].rsplit("/", 1)[-1]
    if head == "eval":
        return " ".join(words[1:])
    if head in SHELLS:
        for i, a in enumerate(words[1:], 1):
            if re.match(r"^-[a-zA-Z]*c[a-zA-Z]*$", a) and i + 1 < len(words):
                return words[i + 1]
    return None


def interpreter_code(words):
    """For `python3 -c CODE` / `node -e CODE` / `perl -e CODE`: the code string, else None."""
    if not words:
        return None
    head = words[0].rsplit("/", 1)[-1]
    if not INTERPRETERS.match(head):
        return None
    for i, a in enumerate(words[1:], 1):
        if a in ("-c", "-e", "--eval", "-p", "--print", "-E", "-x") or re.match(r"^-[a-zA-Z]*[ce]$", a):
            if i + 1 < len(words):
                return words[i + 1]
    return None


def inner_substitutions(word):
    out = re.findall(r"\$\(([^()]*(?:\([^()]*\)[^()]*)*)\)", word)
    out += re.findall(r"`([^`]*)`", word)
    return out


# ------------------------------------------------------------------ protected files

def _active_manifest(ctx):
    proj = ctx.get("active")
    return os.path.join(proj, "project.json") if proj else None


def protected_target(target, cwd, ctx, deleting=False):
    """A reason when the path is a shotcraft record that only sc.py may change, else None."""
    t = (target or "").strip().strip("'\"")
    if not t or t in ("-", "/dev/null", "/dev/stdout", "/dev/stderr") or re.match(r"^&?\d+$", t):
        return None
    norm = t.replace("\\", "/")
    if re.search(r"(^|/)\.shotcraft/stages\.json$", norm) or re.search(r"(^|/)\.shotcraft/qa(/|$)", norm):
        return PROTECTED_HELP % ".shotcraft/stages.json and .shotcraft/qa/"
    unresolved = "$" in norm or "*" in norm or "{" in norm
    full = None
    if not unresolved:
        full = os.path.normpath(os.path.join(cwd or os.getcwd(), os.path.expanduser(t)))
        if os.path.isdir(full) and os.path.basename(full) == ".shotcraft" and deleting:
            return PROTECTED_HELP % "The project's .shotcraft folder"
        n2 = full.replace("\\", "/")
        if re.search(r"/\.shotcraft/stages\.json$", n2) or re.search(r"/\.shotcraft/qa(/|$)", n2):
            return PROTECTED_HELP % ".shotcraft/stages.json and .shotcraft/qa/"
    if os.path.basename(norm.rstrip("/")) == "project.json" or norm.endswith("project.json"):
        if unresolved:
            if ctx.get("active"):
                return PROTECTED_HELP % "project.json"
            return None
        if os.path.isdir(os.path.join(os.path.dirname(full), ".shotcraft")):
            return PROTECTED_HELP % "project.json"
        am = _active_manifest(ctx)
        if am and os.path.normcase(os.path.realpath(full)) == os.path.normcase(os.path.realpath(am)):
            return PROTECTED_HELP % "project.json"
    return None


def code_write_scan(code, ctx):
    """Interpreter code (python -c, node -e, heredoc body) that writes a protected record."""
    if not code or not PROTECTED_TEXT.search(code):
        return None
    clean = re.sub(r"sys\.(stdout|stderr)\.write\s*\(", "print(", code)
    if not CODE_WRITE.search(clean):
        return None
    if re.search(r"\.shotcraft/(stages\.json|qa\b)", code):
        return PROTECTED_HELP % ".shotcraft/stages.json and .shotcraft/qa/"
    if ctx.get("active") or ctx.get("cwd_in_project"):
        return PROTECTED_HELP % "project.json"
    return None


def segment_write_targets(words):
    """(target, deleting) pairs this simple command writes, from redirects and known writers."""
    targets = []
    i = 0
    plain = []
    while i < len(words):
        w = words[i]
        if w in REDIRECTS:
            if i + 1 < len(words):
                targets.append((words[i + 1], False))
            i += 2
            continue
        m = re.match(r"^(\d*)(>>?|>\|)(.+)$", w)
        if m:
            targets.append((m.group(3), False))
            i += 1
            continue
        plain.append(w)
        i += 1
    w, _ = unwrap(plain)
    if not w:
        return targets
    head = w[0].rsplit("/", 1)[-1]
    args = w[1:]
    pos = [a for a in args if not a.startswith("-")]
    if head in ("tee", "sponge"):
        targets += [(a, False) for a in pos]
    elif head in ("sed", "gsed", "perl", "ruby"):
        if any(a == "--in-place" or a.startswith("--in-place=") or re.match(r"^-[a-zA-Z]*i", a) for a in args):
            targets += [(a, False) for a in pos]
    elif head in ("rm", "unlink", "shred", "truncate", "srm", "trash"):
        targets += [(a, True) for a in pos]
    elif head == "mv":
        targets += [(a, True) for a in pos]
    elif head in ("cp", "install", "ln", "rsync", "ditto"):
        if len(pos) >= 2:
            dest = pos[-1]
            targets.append((dest, False))
            for src in pos[:-1]:
                targets.append((os.path.join(dest, os.path.basename(src.rstrip("/"))), False))
    elif head == "dd":
        targets += [(a[3:], False) for a in args if a.startswith("of=")]
    return targets


# ------------------------------------------------------------------ Bash

def scan_shell(cmd, cwd, ctx, depth=0):
    """Raise Block when the command generates raw or writes a protected record."""
    if depth > 5 or not cmd:
        return
    body_cmd, bodies = strip_heredocs(cmd)
    for marker_line, body in bodies:
        mw = re.findall(r"[\w./@-]+", marker_line)
        heads = {x.rsplit("/", 1)[-1] for x in mw}
        if heads & SHELLS or any(INTERPRETERS.match(h) for h in heads):
            why = loose_gen_scan(body)
            if why:
                raise Block("%s\n(found: %s)" % (GEN_HELP, why))
            if heads & SHELLS:
                scan_shell(body, cwd, ctx, depth + 1)
            else:
                r = code_write_scan(body, ctx)
                if r:
                    raise Block(r)
    for inner in inner_substitutions(body_cmd):
        scan_shell(inner, cwd, ctx, depth + 1)
    try:
        tokens = tokenize(body_cmd)
    except ValueError:
        why = loose_gen_scan(body_cmd)
        if why:
            raise Block("%s\n(found: %s)" % (GEN_HELP, why))
        r = loose_write_scan(body_cmd, cwd, ctx)
        if r:
            raise Block(r)
        return
    here = cwd
    for seg in segments(tokens):
        words, is_hf = unwrap(list(seg))
        if is_hf:
            # drop redirects from the higgsfield args
            args, skip = [], False
            for a in words:
                if skip:
                    skip = False
                    continue
                if a in REDIRECTS:
                    skip = True
                    continue
                args.append(a)
            why = hf_decision(args)
            if why:
                raise Block("%s\n(found: %s)" % (GEN_HELP, why))
        if words and words[0] == "__code__":
            code = words[1]
        else:
            code = interpreter_code(words)
        if code:
            why = loose_gen_scan(code)
            if why:
                raise Block("%s\n(found: %s)" % (GEN_HELP, why))
            r = code_write_scan(code, ctx)
            if r:
                raise Block(r)
        sc = shell_code(words)
        if sc:
            scan_shell(sc, here, ctx, depth + 1)
        for target, deleting in segment_write_targets(seg):
            r = protected_target(target, here, ctx, deleting)
            if r:
                raise Block(r)
        if words and words[0] == "cd" and len(words) > 1 and "$" not in words[1]:
            here = os.path.normpath(os.path.join(here or os.getcwd(), os.path.expanduser(words[1])))


def loose_write_scan(text, cwd, ctx):
    """When the command can't be parsed: redirects or tee aimed at a protected record."""
    for m in re.finditer(r"(?:>>?|>\||\btee\b(?:\s+-\w+)*)\s*['\"]?([^\s;&|'\"<>]+)", text or ""):
        r = protected_target(m.group(1), cwd, ctx)
        if r:
            return r
    return code_write_scan(text, ctx)


# ------------------------------------------------------------------ project lookups (may fail open)

def load_core():
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)
    from shotcraft import paths, project, stages  # noqa: F401
    return paths, project, stages


def active_project(session_id):
    try:
        _, project, _ = load_core()
        return project.active_project(session_id or None)
    except Exception as exc:
        note("could not look up the active project (%s: %s)" % (type(exc).__name__, exc))
        return None


def check_bash(data, ctx):
    tin = data.get("tool_input") or {}
    cmd = tin.get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        return
    cwd = data.get("cwd") or os.getcwd()
    try:
        scan_shell(cmd, cwd, ctx)
    except Block:
        raise
    except Exception as exc:
        # parsing broke: the generation rule still holds by plain string matching
        why = loose_gen_scan(cmd)
        if why:
            raise Block("%s\n(found: %s)" % (GEN_HELP, why))
        note("could not read this command (%s); letting it through" % type(exc).__name__)


def check_file(data, ctx):
    tin = data.get("tool_input") or {}
    path = tin.get("file_path") or tin.get("notebook_path") or tin.get("path")
    if not isinstance(path, str) or not path:
        return
    cwd = data.get("cwd") or os.getcwd()
    full = os.path.normpath(os.path.join(cwd, os.path.expanduser(path)))
    r = protected_target(full, cwd, ctx)
    if r:
        raise Block(r)
    proj = ctx.get("active")
    if not proj:
        return
    try:
        paths, _, stages = load_core()
        rel = paths.rel_to(proj, full)
        if rel is None:
            return
        ok, reason = stages.path_writable(proj, rel)
    except Exception as exc:
        note("could not check the stage for %s (%s: %s); letting it through" % (path, type(exc).__name__, exc))
        return
    if not ok:
        raise Block("shotcraft: %s is in a stage folder that is not open. %s" % (rel, reason))


def mcp_is_write(tool_name):
    action = tool_name.split("__", 2)[-1] if tool_name.count("__") >= 2 else tool_name
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", action).lower()
    for tok in re.split(r"[^a-z0-9]+", spaced):
        if tok in MCP_WRITE_WORDS:
            return True
    return False


def check_mcp(data, ctx):
    name = data.get("tool_name") or ""
    if not mcp_is_write(name):
        return
    if ctx.get("active"):
        raise Block("Higgsfield MCP tools that generate, create, upscale, edit, train or upload are blocked while "
                    "a shotcraft project is active, so the stage, budget and rights checks apply. Use:\n"
                    "  python3 \"%s\" gen estimate|submit <card> --tier <tier>" % SC)
    note("no shotcraft project is active, so %s passes. Inside a project, use sc.py gen instead." % name)


def decide(data):
    tool = data.get("tool_name") or ""
    ctx = {}

    def fill_ctx():
        ctx["active"] = active_project(data.get("session_id"))
        cwd = data.get("cwd")
        ctx["cwd_in_project"] = bool(cwd) and _cwd_in_project(cwd)

    if tool == "Bash":
        # the generation rule first, with no project lookup
        tin = data.get("tool_input") or {}
        cmd = tin.get("command") if isinstance(tin, dict) else None
        if isinstance(cmd, str) and PROTECTED_TEXT.search(cmd):
            fill_ctx()
        check_bash(data, ctx)
    elif tool in FILE_TOOLS:
        fill_ctx()
        check_file(data, ctx)
    elif MCP_HIGGSFIELD.match(tool):
        if mcp_is_write(tool):
            fill_ctx()
        check_mcp(data, ctx)


def _cwd_in_project(cwd):
    try:
        _, project, _ = load_core()
        return bool(project.find_project_root(cwd))
    except Exception:
        return False


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        return 0
    try:
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            return 0
        if not isinstance(data.get("tool_input"), dict):
            data["tool_input"] = {}
    except Exception:
        note("could not read the hook input; letting the call through")
        return 0
    try:
        decide(data)
    except Block as b:
        sys.stderr.write(str(b).rstrip() + "\n")
        return 2
    except Exception as exc:
        note("internal error (%s: %s); letting the call through" % (type(exc).__name__, exc))
        return 0
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except BaseException:
        code = 0
    sys.exit(code)
