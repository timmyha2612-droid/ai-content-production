/*
 * shotcraft: import_and_comp.jsx
 * Imports generated clips (or stills) into the open After Effects project and lays them out in shot
 * order in one comp: each clip trimmed to its shot's length, one after another, with a marker per shot.
 *
 * ExtendScript (ES3). Run it with run_jsx.sh, which sets $.global.SC_PARAMS_FILE and
 * $.global.SC_RESULT_FILE. Run by hand (File > Scripts > Run Script File) it asks for the JSON file.
 *
 * Params:
 *   comp_name "shotcraft_stringout", width 1920, height 1080, fps 30,
 *   clips [{path (absolute), shot "S010", in_s 0, duration_s (default: the rest of the clip; 3 for a still)}],
 *   sort_by_shot true, fit "fill"|"fit"|"none" (default "fill"), folder_name "shotcraft clips",
 *   save_project "/abs/path/file.aep"
 * Result JSON: {ok, script, comp, duration_s, placed: [{shot, path, start_s, duration_s}], saved, warnings, error}
 */

function scReadText(path) {
    var f = new File(path);
    f.encoding = "UTF-8";
    if (!f.exists) { throw new Error("File not found: " + path); }
    if (!f.open("r")) { throw new Error("Cannot open: " + path); }
    var s = f.read();
    f.close();
    return s.replace(/^﻿/, "");
}

function scWriteText(path, text) {
    var f = new File(path);
    f.encoding = "UTF-8";
    if (!f.open("w")) { throw new Error("Cannot write: " + path); }
    f.write(text);
    f.close();
}

function scParse(text) {
    if (typeof JSON !== "undefined" && JSON.parse) { return JSON.parse(text); }
    var probe = text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, "@")
        .replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, "]")
        .replace(/(?:^|:|,)(?:\s*\[)+/g, "");
    if (/^[\],:{}\s]*$/.test(probe)) { return eval("(" + text + ")"); }
    throw new Error("The parameter file is not valid JSON.");
}

function scQuote(s) {
    var out = "\"";
    for (var i = 0; i < s.length; i++) {
        var c = s.charAt(i), code = s.charCodeAt(i);
        if (c === "\"" || c === "\\") { out += "\\" + c; }
        else if (c === "\n") { out += "\\n"; }
        else if (c === "\r") { out += "\\r"; }
        else if (c === "\t") { out += "\\t"; }
        else if (code < 32) { out += "\\u" + ("0000" + code.toString(16)).slice(-4); }
        else { out += c; }
    }
    return out + "\"";
}

function scStringify(v) {
    var i, parts, k;
    if (v === null || v === undefined) { return "null"; }
    if (typeof v === "boolean") { return v ? "true" : "false"; }
    if (typeof v === "number") { return isFinite(v) ? String(v) : "null"; }
    if (typeof v === "string") { return scQuote(v); }
    if (v instanceof Array) {
        parts = [];
        for (i = 0; i < v.length; i++) { parts.push(scStringify(v[i])); }
        return "[" + parts.join(",") + "]";
    }
    parts = [];
    for (k in v) {
        if (v.hasOwnProperty(k) && typeof v[k] !== "function") { parts.push(scQuote(k) + ":" + scStringify(v[k])); }
    }
    return "{" + parts.join(",") + "}";
}

function scParams() {
    var p = $.global.SC_PARAMS_FILE;
    if (!p) {
        var f = File.openDialog("Choose the shotcraft JSON parameter file");
        if (!f) { throw new Error("No parameter file given."); }
        p = f.fsName;
    }
    return scParse(scReadText(p));
}

function scFinish(result) {
    var s = scStringify(result);
    var r = $.global.SC_RESULT_FILE;
    if (r) { scWriteText(r, s); }
    return s;
}

function scNum(v, d) { return (typeof v === "number" && isFinite(v)) ? v : d; }

function scColor(v, d) {
    if (!(v instanceof Array) || v.length < 3) { return d; }
    var big = (v[0] > 1 || v[1] > 1 || v[2] > 1);
    return [big ? v[0] / 255 : v[0], big ? v[1] / 255 : v[1], big ? v[2] / 255 : v[2]];
}

function scEnsureParent(f) {
    if (f.parent && !f.parent.exists) { f.parent.create(); }
}

function scSortByShot(list) {
    var out = list.slice(0);
    out.sort(function (a, b) {
        var x = String(a.shot || ""), y = String(b.shot || "");
        return x < y ? -1 : (x > y ? 1 : 0);
    });
    return out;
}

(function () {
    var result = { ok: false, script: "import_and_comp", warnings: [], placed: [] };
    var undo = false, quiet = false;
    try {
        var P = scParams();
        if (!(P.clips instanceof Array) || P.clips.length === 0) { throw new Error("The parameter file needs clips."); }
        app.beginSuppressDialogs(); quiet = true;
        if (!app.project) { app.newProject(); }
        app.beginUndoGroup("shotcraft: import and comp"); undo = true;

        var W = Math.round(scNum(P.width, 1920)), H = Math.round(scNum(P.height, 1080)), FPS = scNum(P.fps, 30);
        var fit = P.fit || "fill";
        var clips = (P.sort_by_shot === false) ? P.clips : scSortByShot(P.clips);
        var folder = app.project.items.addFolder(P.folder_name || "shotcraft clips");

        var plan = [], total = 0, i;
        for (i = 0; i < clips.length; i++) {
            var c = clips[i];
            var f = new File(c.path);
            if (!f.exists) { result.warnings.push("Missing file, skipped: " + c.path); continue; }
            var io = new ImportOptions(f);
            if (!io.canImportAs(ImportAsType.FOOTAGE)) { result.warnings.push("Cannot import as footage: " + c.path); continue; }
            io.importAs = ImportAsType.FOOTAGE;
            var item = app.project.importFile(io);
            item.parentFolder = folder;
            var still = false;
            try { still = item.mainSource.isStill; } catch (eS) { still = false; }
            var inS = scNum(c.in_s, 0);
            var dur = scNum(c.duration_s, still ? 3 : item.duration - inS);
            if (!still && inS + dur > item.duration + 0.001) {
                result.warnings.push((c.shot || c.path) + ": clip is shorter than in_s + duration_s; trimmed to " +
                    (item.duration - inS).toFixed(2) + " s.");
                dur = item.duration - inS;
            }
            if (dur <= 0) { result.warnings.push((c.shot || c.path) + ": nothing left after in_s; skipped."); continue; }
            plan.push({ item: item, shot: c.shot || item.name, path: c.path, in_s: inS, dur: dur, still: still });
            total += dur;
        }
        if (plan.length === 0 || total <= 0) { throw new Error("No clip could be placed."); }

        var comp = app.project.items.addComp(P.comp_name || "shotcraft_stringout", W, H, 1.0, total, FPS);
        result.comp = comp.name;
        result.duration_s = total;

        var cursor = 0;
        for (i = 0; i < plan.length; i++) {
            var p = plan[i];
            var layer = comp.layers.add(p.item);
            layer.moveToEnd();
            layer.name = p.shot;
            layer.startTime = cursor - p.in_s;
            layer.outPoint = cursor + p.dur;
            layer.inPoint = cursor;
            if (fit !== "none" && p.item.width && p.item.height) {
                var sw = p.item.width * (p.item.pixelAspect || 1), sh = p.item.height;
                var s = (fit === "fit") ? Math.min(W / sw, H / sh) : Math.max(W / sw, H / sh);
                layer.property("ADBE Transform Group").property("ADBE Scale").setValue([s * 100, s * 100]);
                if (Math.abs(sw / sh - W / H) > 0.01) {
                    result.warnings.push(p.shot + ": aspect differs from the comp; " + fit + " applied.");
                }
            }
            var mv = new MarkerValue(p.shot);
            try { comp.markerProperty.setValueAtTime(cursor, mv); }
            catch (eM) { layer.property("ADBE Marker").setValueAtTime(cursor, mv); }
            result.placed.push({ shot: p.shot, path: p.path, start_s: cursor, duration_s: p.dur });
            cursor += p.dur;
        }

        try { comp.openInViewer(); } catch (eView) { /* no viewer in some modes */ }

        if (P.save_project) {
            var pf = new File(P.save_project);
            scEnsureParent(pf);
            app.project.save(pf);
            result.saved = pf.fsName;
        }
        result.ok = true;
    } catch (e) {
        result.error = String(e) + (e.line ? " (line " + e.line + ")" : "");
    }
    if (undo) { app.endUndoGroup(); }
    if (quiet) { try { app.endSuppressDialogs(false); } catch (e3) { /* ignore */ } }
    return scFinish(result);
})();
