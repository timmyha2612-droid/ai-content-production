#!/usr/bin/env bash
# shotcraft: run an ExtendScript (.jsx) file in After Effects on macOS, with a JSON parameter file.
#
# Usage:
#   run_jsx.sh --list                              list the installed After Effects versions (newest first)
#   run_jsx.sh [--app "Adobe After Effects 2026"] SCRIPT.jsx [PARAMS.json]
#
# It writes a small wrapper script that sets $.global.SC_PARAMS_FILE and $.global.SC_RESULT_FILE, then runs
# SCRIPT.jsx with $.evalFile, through JavaScript for Automation:
#   osascript -l JavaScript ... Application("<AE app>").doscriptfile("<wrapper>")
# (AppleScript's DoScriptFile broke on AE 2024 with macOS Sonoma; the JXA form works.)
# It prints the script's JSON result.
#
# The After Effects version: --app, else $SC_AE_APP, else the newest one found in /Applications.
#
# Exit codes: 0 ok, 1 the script failed or returned ok:false, 2 bad usage, 3 no After Effects found,
#             4 not macOS, 5 macOS refused permission (Automation).
#
# Needs, once, set by the user (never scripted):
#   - System Settings > Privacy & Security > Automation: allow this terminal app to control After Effects.
#   - After Effects > Settings > Scripting & Expressions: "Allow Scripts to Write Files and Access Network".

set -u

usage() {
    sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'
}

APP="${SC_AE_APP:-}"
LIST=0
while [ $# -gt 0 ]; do
    case "$1" in
        --list) LIST=1; shift ;;
        --app)
            [ $# -ge 2 ] || { echo "--app needs a name, e.g. \"Adobe After Effects 2026\"" >&2; exit 2; }
            APP="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        --) shift; break ;;
        -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
        *) break ;;
    esac
done

if [ "$(uname -s)" != "Darwin" ]; then
    echo "This runner works on macOS only. On Windows run: AfterFX.com -r <wrapper.jsx> (see ae-route.md)." >&2
    echo "On Linux there is no After Effects: use the code route (HyperFrames)." >&2
    exit 4
fi

# Installed versions, newest first: "<year>\t<app name>". Betas sort last.
find_versions() {
    local dir app name year
    for dir in /Applications/Adobe\ After\ Effects*; do
        [ -d "$dir" ] || continue
        for app in "$dir"/Adobe\ After\ Effects*.app; do
            [ -d "$app" ] || continue
            name="$(basename "$app" .app)"
            year="$(printf '%s' "$name" | sed -n 's/.*\([12][0-9][0-9][0-9]\).*/\1/p')"
            [ -n "$year" ] || year=0
            printf '%s\t%s\n' "$year" "$name"
        done
    done | sort -t "$(printf '\t')" -k1,1nr -k2,2
}

if [ "$LIST" -eq 1 ]; then
    found="$(find_versions)"
    if [ -z "$found" ]; then
        echo "No After Effects found in /Applications." >&2
        exit 3
    fi
    printf '%s\n' "$found" | cut -f2
    exit 0
fi

[ $# -ge 1 ] || { usage >&2; exit 2; }
SCRIPT="$1"
PARAMS="${2:-}"

abspath() {
    local d
    d="$(cd "$(dirname "$1")" 2>/dev/null && pwd)" || return 1
    printf '%s/%s' "$d" "$(basename "$1")"
}

[ -f "$SCRIPT" ] || { echo "Script not found: $SCRIPT" >&2; exit 2; }
SCRIPT="$(abspath "$SCRIPT")"
if [ -n "$PARAMS" ]; then
    [ -f "$PARAMS" ] || { echo "Parameter file not found: $PARAMS" >&2; exit 2; }
    PARAMS="$(abspath "$PARAMS")"
fi

if [ -z "$APP" ]; then
    APP="$(find_versions | head -n 1 | cut -f2)"
fi
if [ -z "$APP" ]; then
    echo "No After Effects found in /Applications. Name one with --app or SC_AE_APP." >&2
    exit 3
fi

TMP="$(mktemp -d "${TMPDIR:-/tmp}/shotcraft-ae.XXXXXX")" || { echo "Cannot make a temp folder." >&2; exit 1; }
trap 'rm -rf "$TMP"' EXIT
WRAPPER="$TMP/run.jsx"
RESULT="$TMP/result.json"

# Escape a path for a double-quoted JavaScript string.
js_str() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

{
    if [ -n "$PARAMS" ]; then
        printf '$.global.SC_PARAMS_FILE = "%s";\n' "$(js_str "$PARAMS")"
    else
        printf '$.global.SC_PARAMS_FILE = null;\n'
    fi
    printf '$.global.SC_RESULT_FILE = "%s";\n' "$(js_str "$RESULT")"
    printf '$.evalFile(new File("%s"));\n' "$(js_str "$SCRIPT")"
} > "$WRAPPER"

ERR="$TMP/osascript.err"
osascript -l JavaScript - "$APP" "$WRAPPER" > "$TMP/osascript.out" 2> "$ERR" <<'JXA'
function run(argv) {
    var ae = Application(argv[0]);
    try {
        ae.doscriptfile(argv[1]);
    } catch (e) {
        ae.doscriptfile(Path(argv[1]));
    }
    return "done";
}
JXA
rc=$?

if [ $rc -ne 0 ]; then
    if grep -q -- "-1743" "$ERR"; then
        echo "macOS refused permission to control $APP." >&2
        echo "Ask the user to allow it: System Settings > Privacy & Security > Automation." >&2
        exit 5
    fi
    if grep -q -- "-1712" "$ERR"; then
        echo "osascript stopped waiting (Apple event timed out). After Effects may still be working;" >&2
        echo "check AE for a dialog or a running render, then check the output files." >&2
        exit 1
    fi
    echo "osascript failed running $SCRIPT in $APP:" >&2
    cat "$ERR" >&2
    echo "If AE shows a dialog, ask the user to close it and try again." >&2
    exit 1
fi

if [ ! -s "$RESULT" ]; then
    echo "The script wrote no result. In After Effects, check Settings > Scripting & Expressions >" >&2
    echo "\"Allow Scripts to Write Files and Access Network\", and look for an open dialog." >&2
    exit 1
fi

cat "$RESULT"
echo
if grep -q '"ok":true' "$RESULT"; then
    exit 0
fi
exit 1
