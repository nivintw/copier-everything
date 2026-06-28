/*
 * SPDX-FileCopyrightText: © 2026 Tyler Nivin
 * SPDX-License-Identifier: MIT
 */


// copier-everything docs — vanilla JS, no build step. Theme toggle, client-side search over
// search-index.json, mobile sidebar, and active-link highlighting. Loaded as a classic
// <script src="app.js"> with a relative path so it works from file:// and GitHub Pages alike.

(function () {
  "use strict";

  // ---- Theme toggle (persisted; falls back to prefers-color-scheme) --------
  var root = document.documentElement;
  try {
    var saved = localStorage.getItem("ce-theme");
    if (saved === "light" || saved === "dark") root.setAttribute("data-theme", saved);
  } catch (e) { /* private mode: ignore */ }

  function currentTheme() {
    var t = root.getAttribute("data-theme");
    if (t) return t;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  document.addEventListener("click", function (ev) {
    var toggle = ev.target.closest && ev.target.closest("[data-theme-toggle]");
    if (toggle) {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("ce-theme", next); } catch (e) { /* ignore */ }
      return;
    }
    var menu = ev.target.closest && ev.target.closest("[data-menu-toggle]");
    if (menu) { toggleSidebar(); return; }
    var scrim = ev.target.classList && ev.target.classList.contains("scrim");
    if (scrim) { toggleSidebar(false); }
  });

  // ---- Mobile sidebar ------------------------------------------------------
  function toggleSidebar(force) {
    var sb = document.querySelector(".sidebar");
    var sc = document.querySelector(".scrim");
    if (!sb) return;
    var open = force === undefined ? !sb.classList.contains("open") : force;
    sb.classList.toggle("open", open);
    if (sc) sc.classList.toggle("open", open);
  }

  // ---- Search --------------------------------------------------------------
  var input = document.querySelector(".search input");
  var results = document.querySelector(".search-results");
  var index = [];
  var activeIdx = -1;

  if (input && results) {
    // Resolve the index relative to the current page so it works in any subdir.
    fetch("search-index.json")
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (data) { index = Array.isArray(data) ? data : []; })
      .catch(function () { index = []; });

    input.addEventListener("input", function () { runSearch(input.value); });
    input.addEventListener("focus", function () { if (input.value) runSearch(input.value); });
    input.addEventListener("keydown", onKey);
    document.addEventListener("click", function (ev) {
      if (!ev.target.closest || !ev.target.closest(".search")) closeResults();
    });
    // "/" focuses search.
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "/" && document.activeElement !== input) { ev.preventDefault(); input.focus(); }
    });
  }

  function runSearch(q) {
    q = (q || "").trim().toLowerCase();
    if (!q) { closeResults(); return; }
    var terms = q.split(/\s+/);
    var scored = [];
    for (var i = 0; i < index.length; i++) {
      var it = index[i];
      var hay = (it.title + " " + (it.text || "") + " " + (it.page || "")).toLowerCase();
      var ok = true, score = 0;
      for (var t = 0; t < terms.length; t++) {
        var pos = hay.indexOf(terms[t]);
        if (pos < 0) { ok = false; break; }
        score += (it.title.toLowerCase().indexOf(terms[t]) >= 0 ? 10 : 1) - pos / 1000;
      }
      if (ok) scored.push({ it: it, score: score });
    }
    scored.sort(function (a, b) { return b.score - a.score; });
    render(scored.slice(0, 12).map(function (s) { return s.it; }), q);
  }

  function render(items, q) {
    activeIdx = -1;
    if (!items.length) {
      results.innerHTML = '<div class="search-empty">No matches for "' + escapeHtml(q) + '"</div>';
      results.classList.add("open");
      return;
    }
    var html = "";
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      html += '<a href="' + escapeHtml(it.url) + '" data-i="' + i + '">' +
        '<span class="r-title">' + escapeHtml(it.title) + "</span> " +
        '<span class="r-page">' + escapeHtml(it.page || "") + "</span></a>";
    }
    results.innerHTML = html;
    results.classList.add("open");
  }

  function onKey(ev) {
    if (!results.classList.contains("open")) return;
    var links = results.querySelectorAll("a");
    if (!links.length) return;
    if (ev.key === "ArrowDown") { ev.preventDefault(); activeIdx = Math.min(activeIdx + 1, links.length - 1); }
    else if (ev.key === "ArrowUp") { ev.preventDefault(); activeIdx = Math.max(activeIdx - 1, 0); }
    else if (ev.key === "Enter") { if (activeIdx >= 0) { ev.preventDefault(); window.location.href = links[activeIdx].getAttribute("href"); } return; }
    else if (ev.key === "Escape") { closeResults(); input.blur(); return; }
    else return;
    for (var i = 0; i < links.length; i++) links[i].classList.toggle("active", i === activeIdx);
  }

  function closeResults() { if (results) { results.classList.remove("open"); activeIdx = -1; } }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // ---- Active section highlighting in the TOC (current page) ----------------
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll("nav.toc a[href*='#']"));
  var samePage = tocLinks.filter(function (a) {
    var href = a.getAttribute("href") || "";
    return href.indexOf("#") === 0 || href.indexOf(location.pathname.split("/").pop()) === 0;
  });
  if (samePage.length && "IntersectionObserver" in window) {
    var byId = {};
    samePage.forEach(function (a) {
      var id = (a.getAttribute("href") || "").split("#")[1];
      if (id) byId[id] = a;
    });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && byId[en.target.id]) {
          samePage.forEach(function (a) { a.classList.remove("current"); });
          byId[en.target.id].classList.add("current");
        }
      });
    }, { rootMargin: "-10% 0px -75% 0px" });
    Object.keys(byId).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) obs.observe(el);
    });
  }
})();
