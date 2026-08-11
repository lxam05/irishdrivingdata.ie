(function () {
  'use strict';
  var ORIGIN = 'https://irishdrivingdata.ie';
  try {
    if (typeof document !== 'undefined' && document.currentScript && document.currentScript.src) {
      ORIGIN = new URL(document.currentScript.src).origin;
    }
  } catch (e) {}

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function render(el, centre, meta) {
    var pass =
      centre.passRate === null || centre.passRate === undefined
        ? 'Not published'
        : centre.passRate + '%';
    var wait =
      centre.waitWeeks === null || centre.waitWeeks === undefined
        ? 'Not published'
        : centre.waitWeeks + ' weeks';
    var href = ORIGIN + '/centres/' + encodeURIComponent(centre.slug) + '/';
    el.innerHTML =
      '<div style="font:14px/1.45 system-ui,sans-serif;color:#1a2332;border:1px solid #d4cfc4;border-radius:8px;background:#fffcf7;padding:12px 14px;max-width:22rem">' +
      '<div style="font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:#5a6578">RSA Category B · ' +
      esc(meta.lastUpdatedLabel || '') +
      '</div>' +
      '<div style="font-weight:650;margin:4px 0 8px">' +
      esc(centre.name) +
      ' driving test</div>' +
      '<div style="display:flex;gap:16px;flex-wrap:wrap">' +
      '<div><strong style="display:block;font-size:20px;font-variant-numeric:tabular-nums">' +
      esc(pass) +
      '</strong><span style="color:#5a6578;font-size:12px">Pass rate</span></div>' +
      '<div><strong style="display:block;font-size:20px;font-variant-numeric:tabular-nums">' +
      esc(wait) +
      '</strong><span style="color:#5a6578;font-size:12px">Wait (est.)</span></div>' +
      '</div>' +
      '<div style="margin-top:8px;font-size:12px;color:#5a6578">Data by <a href="' +
      href +
      '" style="color:#0c6e5a" target="_blank" rel="noopener">Irish Driving Data</a></div>' +
      '</div>';
  }

  function boot() {
    var nodes = document.querySelectorAll('[data-idd-centre]');
    if (!nodes.length) return;
    fetch(ORIGIN + '/data/latest.json', { credentials: 'omit' })
      .then(function (r) {
        if (!r.ok) throw new Error('fetch failed');
        return r.json();
      })
      .then(function (payload) {
        var bySlug = {};
        (payload.centres || []).forEach(function (c) {
          bySlug[c.slug] = c;
        });
        nodes.forEach(function (el) {
          var slug = el.getAttribute('data-idd-centre');
          var centre = bySlug[slug];
          if (!centre) {
            el.textContent = 'Centre not found: ' + slug;
            return;
          }
          render(el, centre, payload.meta || {});
        });
      })
      .catch(function () {
        nodes.forEach(function (el) {
          var slug = el.getAttribute('data-idd-centre') || '';
          el.innerHTML =
            '<iframe title="Irish Driving Data" src="' +
            ORIGIN +
            '/embed/' +
            encodeURIComponent(slug) +
            '/" style="width:100%;max-width:22rem;height:11rem;border:0" loading="lazy"></iframe>';
        });
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
