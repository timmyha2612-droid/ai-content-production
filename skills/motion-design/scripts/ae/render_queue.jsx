/*
 * shotcraft: render_queue.jsx
 * Adds comps from the open After Effects project to the render queue with a render settings template and an
 * output module template, writing into one folder. Optionally renders right away (prefer aerender for long
 * renders: osascript stops waiting after about 2 minutes, though After Effects keeps rendering).
 *
 * ExtendScript (ES3). Run it with run_jsx.sh, which sets $.global.SC_PARAMS_FILE and
 * $.global.SC_RESULT_FILE. Run by hand (File > Scripts > Run Script File) it asks for the JSON file.
 *
 * Params:
 *   comps ["M010_lower-third", ...] (comp names), output_dir "/abs/path/07_mograph/renders",
 *   output_template "High Quality with Alpha", render_template "Best Settings",
 *   render_now false, save_project "/abs/path/file.aep"
 * Result JSON: {ok, script, queued: [{comp, file, render_template, output_template}], rendered,
 *               available_output_templates, available_render_templates, saved, warnings, error}
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

function scHas(list, name) {
    if (!list) { return false; }
    for (var i = 0; i < list.length; i++) { if (list[i] === name) { return true; } }
    return false;
}

function scList(list) {
    var out = [];
    if (list) { for (var i = 0; i < list.length; i++) { out.push(String(list[i])); } }
    return out;
}

function scFindComp(name) {
    for (var i = 1; i <= app.project.numItems; i++) {
        var it = app.project.item(i);
        if (it instanceof CompItem && it.name === name) { return it; }
    }
    return null;
}

function scSafeName(s) { return String(s).replace(/[\\\/:\*\?"<>\|]/g, "_"); }

(function () {
    var result = { ok: false, script: "render_queue", warnings: [], queued: [], rendered: false };
    var quiet = false;
    try {
        var P = scParams();
        if (!(P.comps instanceof Array) || P.comps.length === 0) { throw new Error("The parameter file needs comps."); }
        if (!P.output_dir) { throw new Error("The parameter file needs output_dir."); }
        if (!app.project) { throw new Error("No project is open in After Effects."); }
        app.beginSuppressDialogs(); quiet = true;

        var outDir = new Folder(P.output_dir);
        if (!outDir.exists) { outDir.create(); }

        for (var i = 0; i < P.comps.length; i++) {
            var comp = scFindComp(P.comps[i]);
            if (!comp) { result.warnings.push("No comp named " + P.comps[i] + "; skipped."); continue; }
            var rqi = app.project.renderQueue.items.add(comp);
            var rTpl = null, oTpl = null;
            if (P.render_template) {
                if (scHas(rqi.templates, P.render_template)) { rqi.applyTemplate(P.render_template); rTpl = P.render_template; }
                else {
                    result.warnings.push("Render settings template not found: " + P.render_template);
                    result.available_render_templates = scList(rqi.templates);
                }
            }
            var om = rqi.outputModule(1);
            if (P.output_template) {
                if (scHas(om.templates, P.output_template)) { om.applyTemplate(P.output_template); oTpl = P.output_template; }
                else {
                    result.warnings.push("Output module template not found: " + P.output_template);
                    result.available_output_templates = scList(om.templates);
                }
            }
            var ext = "";
            try {
                var cur = om.file ? om.file.name : "";
                var dot = cur.lastIndexOf(".");
                if (dot > 0) { ext = cur.substring(dot); }
            } catch (eExt) { ext = ""; }
            om.file = new File(outDir.fsName + "/" + scSafeName(comp.name) + ext);
            result.queued.push({ comp: comp.name, file: om.file.fsName, render_template: rTpl, output_template: oTpl });
        }
        if (result.queued.length === 0) { throw new Error("Nothing was queued."); }

        if (P.save_project) {
            var pf = new File(P.save_project);
            scEnsureParent(pf);
            app.project.save(pf);
            result.saved = pf.fsName;
        }
        if (P.render_now) {
            app.project.renderQueue.render();
            result.rendered = true;
        }
        result.ok = true;
    } catch (e) {
        result.error = String(e) + (e.line ? " (line " + e.line + ")" : "");
    }
    if (quiet) { try { app.endSuppressDialogs(false); } catch (e3) { /* ignore */ } }
    return scFinish(result);
})();
