/* <coastal-map> — real NC county geometry (us-atlas TopoJSON) + tiered community pins.
   Data in via the `points` attribute (JSON string). Clicks call window.__coastalMapPick(id). */
(function () {
  var COASTAL = ['37019','37129','37141','37133','37031','37049','37137','37103','37061','37047','37013','37095','37177','37055','37053','37029','37139','37143','37041','37187','37015','37117','37107','37147','37131'];

  class CoastalMap extends HTMLElement {
    static get observedAttributes() { return ['points']; }
    constructor() { super(); this._pts = []; this._geo = null; }

    connectedCallback() {
      this.style.display = 'block';
      this.style.position = 'relative';
      this.style.width = '100%';
      this.style.height = this.getAttribute('height') || '430px';
      if (!this._shell) {
        this._shell = document.createElement('div');
        this._shell.style.cssText = 'position:absolute;inset:0;border-radius:8px;overflow:hidden;background:oklch(0.94 0.018 225)';
        this.appendChild(this._shell);
        this._tip = document.createElement('div');
        this._tip.style.cssText = 'position:absolute;pointer-events:none;opacity:0;transition:opacity .12s;background:oklch(0.20 0.02 250);color:#fff;font:500 11px/1.4 Archivo,system-ui,sans-serif;padding:7px 9px;border-radius:6px;max-width:230px;z-index:9;box-shadow:0 6px 18px rgba(0,0,0,.22)';
        this.appendChild(this._tip);
        this._note = document.createElement('div');
        this._note.style.cssText = 'position:absolute;left:10px;bottom:8px;font:400 9.5px/1.3 "IBM Plex Mono",monospace;color:oklch(0.42 0.02 240);z-index:3';
        this._note.textContent = 'County geometry: US Census via us-atlas TopoJSON';
        this.appendChild(this._note);
      }
      this._boot();
      if (!this._ro && window.ResizeObserver) {
        this._ro = new ResizeObserver(() => this._draw());
        this._ro.observe(this);
      }
    }

    attributeChangedCallback(n, o, v) {
      if (n !== 'points') return;
      try { this._pts = JSON.parse(v || '[]'); } catch (e) { this._pts = []; }
      this._draw();
    }

    _fail(msg) {
      if (!this._shell) return;
      this._shell.innerHTML = '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;font:400 12px/1.5 Archivo,system-ui,sans-serif;color:oklch(0.45 0.02 250)">' + msg + '</div>';
    }

    async _boot() {
      if (this._booted) return;
      this._booted = true;
      var t0 = Date.now();
      while ((!window.d3 || !window.topojson) && Date.now() - t0 < 20000) {
        await new Promise(function (r) { setTimeout(r, 70); });
      }
      if (!window.d3 || !window.topojson) { this._fail('Mapping libraries did not load — check the network, then reload.'); return; }
      try {
        var topo = await fetch('https://cdn.jsdelivr.net/npm/us-atlas@3.0.1/counties-10m.json').then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        });
        var all = window.topojson.feature(topo, topo.objects.counties).features;
        this._geo = all.filter(function (f) { return String(f.id).slice(0, 2) === '37'; });
        var st = window.topojson.feature(topo, topo.objects.states).features;
        this._outline = st.filter(function (f) { return String(f.id) === '37'; })[0];
        this._draw();
      } catch (e) {
        this._fail('Could not load county geometry (' + e.message + '). The rest of the board is unaffected.');
      }
    }

    _draw() {
      if (!this._geo || !window.d3) return;
      var d3 = window.d3;
      var w = this.clientWidth || 900, h = this.clientHeight || 430;
      if (w < 40 || h < 40) return;
      var coastal = this._geo.filter(function (f) { return COASTAL.indexOf(String(f.id)) >= 0; });
      var proj = d3.geoMercator().fitExtent([[10, 10], [w - 10, h - 26]], { type: 'FeatureCollection', features: coastal });
      var path = d3.geoPath(proj);

      var svg = '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" style="display:block">';
      svg += '<rect width="' + w + '" height="' + h + '" fill="oklch(0.925 0.022 228)"/>';
      svg += '<g>';
      this._geo.forEach(function (f) {
        var isC = COASTAL.indexOf(String(f.id)) >= 0;
        svg += '<path d="' + (path(f) || '') + '" fill="' + (isC ? 'oklch(0.955 0.008 90)' : 'oklch(0.885 0.010 100)') + '" stroke="oklch(0.83 0.012 100)" stroke-width="0.6"/>';
      });
      if (this._outline) svg += '<path d="' + (path(this._outline) || '') + '" fill="none" stroke="oklch(0.62 0.02 100)" stroke-width="1.1"/>';
      svg += '</g><g id="pins">';

      var pts = this._pts.slice().sort(function (a, b) { return b.r - a.r; });
      pts.forEach(function (p, i) {
        var xy = proj([p.lng, p.lat]);
        if (!xy) return;
        p._x = xy[0]; p._y = xy[1];
        svg += '<circle data-i="' + i + '" cx="' + xy[0].toFixed(1) + '" cy="' + xy[1].toFixed(1) + '" r="' + p.r + '"'
          + ' fill="' + p.fill + '" fill-opacity="0.9" stroke="' + (p.inv ? p.ringColor : '#fff') + '" stroke-width="' + (p.inv ? 2.4 : 1.3) + '"'
          + ' style="cursor:pointer"/>';
      });
      svg += '</g></svg>';
      this._shell.innerHTML = svg;
      this._pins = pts;

      var self = this;
      var circles = this._shell.querySelectorAll('circle[data-i]');
      Array.prototype.forEach.call(circles, function (el) {
        var p = self._pins[+el.getAttribute('data-i')];
        el.addEventListener('mouseenter', function () {
          el.setAttribute('r', p.r * 1.45);
          self._tip.innerHTML = '<div style="font-weight:600;margin-bottom:2px">' + p.name + '</div>'
            + '<div style="opacity:.8;font-family:\'IBM Plex Mono\',monospace;font-size:10px">' + p.builder + '</div>'
            + '<div style="margin-top:4px;font-family:\'IBM Plex Mono\',monospace;font-size:10px">' + p.meta + '</div>'
            + (p.inv ? '<div style="margin-top:4px;font-size:10px;color:' + p.ringColor + '">investor-eligible incentive</div>' : '');
          var left = Math.min(Math.max(p._x + 14, 6), self.clientWidth - 240);
          self._tip.style.left = left + 'px';
          self._tip.style.top = Math.max(6, p._y - 18) + 'px';
          self._tip.style.opacity = '1';
        });
        el.addEventListener('mouseleave', function () { el.setAttribute('r', p.r); self._tip.style.opacity = '0'; });
        el.addEventListener('click', function () { if (window.__coastalMapPick) window.__coastalMapPick(p.id); });
      });
    }
  }

  if (!window.customElements.get('coastal-map')) window.customElements.define('coastal-map', CoastalMap);
})();
