/*
 * shotcraft: lower_third.jsx
 * Builds a lower third comp in the open After Effects project from a JSON parameter file:
 * an accent bar plus a title and a subtitle, eased in and out. Optionally saves the project
 * (as a new file) and writes a preview PNG.
 *
 * ExtendScript (ES3). Run it with run_jsx.sh, which sets $.global.SC_PARAMS_FILE and
 * $.global.SC_RESULT_FILE. Run by hand (File > Scripts > Run Script File) it asks for the JSON file.
 *
 * Params (all optional except title):
 *   comp_name "lower_third", width 1920, height 1080, fps 30, duration_s 5,
 *   title, subtitle, font_title, font_subtitle (PostScript names), title_size 64, subtitle_size 40,
 *   text_color [1,1,1], bar_color [1,1,1], bar true, align "left"|"right"|"center",
 *   margin_px [x from the side, y from the bottom to the subtitle baseline],
 *   anim_in_s 0.5, anim_out_s 0.5, slide_px 24,
 *   save_project "/abs/path/file.aep", preview_png "/abs/path/frame.png", preview_time_s (default: the hold)
 * Result JSON: {ok, script, comp, layers, saved, preview, warnings, error}
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

function scEase(prop) {
    for (var k = 1; k <= prop.numKeys; k++) {
        var e = new KeyframeEase(0, 75);
        var tries = [[e], [e, e], [e, e, e]];
        for (var t = 0; t < tries.length; t++) {
            try { prop.setTemporalEaseAtKey(k, tries[t], tries[t]); break; } catch (err) { /* try the next size */ }
        }
    }
}

function scKeys(prop, times, values) {
    for (var i = 0; i < times.length; i++) { prop.setValueAtTime(times[i], values[i]); }
    scEase(prop);
}

function scFontMissing(font) {
    try {
        if (app.fonts && app.fonts.getFontsByPostScriptName) {
            var found = app.fonts.getFontsByPostScriptName(font);
            return !found || found.length === 0;
        }
    } catch (e) { /* older After Effects: no font API */ }
    return false;
}

function scText(comp, text, font, size, color, just, name, warnings) {
    var layer = comp.layers.addText(text);
    layer.name = name;
    var prop = layer.property("ADBE Text Properties").property("ADBE Text Document");
    var td = prop.value;
    if (font) {
        if (scFontMissing(font)) { warnings.push("Font not installed: " + font + " (After Effects used a fallback)."); }
        td.font = font;
    }
    td.fontSize = size;
    td.applyFill = true;
    td.fillColor = color;
    td.applyStroke = false;
    td.justification = just;
    prop.setValue(td);
    if (font) {
        try {
            if (prop.value.font !== font) {
                warnings.push("Font " + font + " was not applied; the layer uses " + prop.value.font + ".");
            }
        } catch (e2) { /* ignore */ }
    }
    return layer;
}

(function () {
    var result = { ok: false, script: "lower_third", warnings: [], layers: [] };
    var undo = false, quiet = false;
    try {
        var P = scParams();
        if (!P.title) { throw new Error("The parameter file needs a title."); }
        app.beginSuppressDialogs(); quiet = true;
        if (!app.project) { app.newProject(); }
        app.beginUndoGroup("shotcraft: lower third"); undo = true;

        var W = Math.round(scNum(P.width, 1920)), H = Math.round(scNum(P.height, 1080));
        var FPS = scNum(P.fps, 30), DUR = scNum(P.duration_s, 5);
        var align = P.align || "left";
        var tSize = scNum(P.title_size, Math.round(H * 0.06));
        var sSize = scNum(P.subtitle_size, Math.round(tSize * 0.62));
        var textColor = scColor(P.text_color, [1, 1, 1]);
        var barColor = scColor(P.bar_color, [1, 1, 1]);
        var useBar = (P.bar !== false) && align !== "center";
        var margin = (P.margin_px instanceof Array && P.margin_px.length >= 2) ? P.margin_px
            : [Math.round(W * 0.06), Math.round(H * 0.12)];
        var slide = scNum(P.slide_px, Math.round(tSize * 0.4));
        var aIn = scNum(P.anim_in_s, 0.5), aOut = scNum(P.anim_out_s, 0.5);
        if (aIn + aOut > DUR * 0.8) {
            var k = (DUR * 0.8) / (aIn + aOut);
            aIn = aIn * k; aOut = aOut * k;
            result.warnings.push("Animation times were shortened to fit a " + DUR + " s comp.");
        }

        var comp = app.project.items.addComp(P.comp_name || "lower_third", W, H, 1.0, DUR, FPS);
        result.comp = comp.name;

        var barW = useBar ? Math.max(4, Math.round(tSize * 0.1)) : 0;
        var gap = useBar ? Math.round(tSize * 0.35) : 0;
        var subY = H - margin[1];
        var titleY = P.subtitle ? Math.round(subY - sSize * 1.35) : subY;
        var x, just;
        if (align === "right") { x = W - margin[0] - barW - gap; just = ParagraphJustification.RIGHT_JUSTIFY; }
        else if (align === "center") { x = Math.round(W / 2); just = ParagraphJustification.CENTER_JUSTIFY; }
        else { x = margin[0] + barW + gap; just = ParagraphJustification.LEFT_JUSTIFY; }

        var inT = [0, aIn], outT = [DUR - aOut, DUR];
        var layers = [];

        var title = scText(comp, P.title, P.font_title, tSize, textColor, just, "Title", result.warnings);
        layers.push({ layer: title, y: titleY, delay: 0 });
        if (P.subtitle) {
            var sub = scText(comp, P.subtitle, P.font_subtitle || P.font_title, sSize, textColor, just,
                "Subtitle", result.warnings);
            layers.push({ layer: sub, y: subY, delay: Math.min(0.1, aIn / 2) });
        }

        for (var i = 0; i < layers.length; i++) {
            var L = layers[i];
            var tr = L.layer.property("ADBE Transform Group");
            var pos = tr.property("ADBE Position");
            var op = tr.property("ADBE Opacity");
            var d = L.delay;
            scKeys(pos, [inT[0] + d, inT[1] + d, outT[0], outT[1]],
                [[x, L.y + slide], [x, L.y], [x, L.y], [x, L.y + slide]]);
            scKeys(op, [inT[0] + d, inT[1] + d, outT[0], outT[1]], [0, 100, 100, 0]);
            result.layers.push(L.layer.name);
        }

        if (useBar) {
            var top = titleY - Math.round(tSize * 0.78);
            var bottom = P.subtitle ? subY + Math.round(sSize * 0.25) : subY + Math.round(tSize * 0.2);
            var barH = Math.max(8, bottom - top);
            var bar = comp.layers.addSolid(barColor, (P.comp_name || "lower_third") + " bar", barW, barH, 1.0, DUR);
            bar.name = "Accent bar";
            var btr = bar.property("ADBE Transform Group");
            btr.property("ADBE Anchor Point").setValue([barW / 2, barH]);
            var barX = (align === "right") ? (W - margin[0] - barW / 2) : (margin[0] + barW / 2);
            btr.property("ADBE Position").setValue([barX, bottom]);
            scKeys(btr.property("ADBE Scale"), [inT[0], inT[1], outT[0], outT[1]],
                [[100, 0], [100, 100], [100, 100], [100, 0]]);
            bar.moveToEnd();
            result.layers.push(bar.name);
        }

        try { comp.openInViewer(); } catch (eView) { /* no viewer in some modes */ }

        if (P.save_project) {
            var pf = new File(P.save_project);
            scEnsureParent(pf);
            app.project.save(pf);
            result.saved = pf.fsName;
        }

        if (P.preview_png) {
            var png = new File(P.preview_png);
            scEnsureParent(png);
            var at = scNum(P.preview_time_s, Math.min(DUR - aOut, aIn + (DUR - aIn - aOut) / 2));
            try {
                comp.saveFrameToPng(at, png);
                result.preview = png.fsName;
            } catch (ePng) {
                result.warnings.push("Preview frame failed (" + ePng + "). Render one with aerender or ffmpeg.");
            }
        }
        result.ok = true;
    } catch (e) {
        result.error = String(e) + (e.line ? " (line " + e.line + ")" : "");
    }
    if (undo) { app.endUndoGroup(); }
    if (quiet) { try { app.endSuppressDialogs(false); } catch (e3) { /* ignore */ } }
    return scFinish(result);
})();
