// Preloaded with `node --require` by the prototype checkers: records every attempt to reach the network and refuses it. The log path is in STUDIO_NET_LOG.
'use strict';
const fs = require('fs');
const log = (kind, what) => { try { fs.appendFileSync(process.env.STUDIO_NET_LOG, JSON.stringify({ kind, what: String(what) }) + '\n'); } catch (e) { /* no log */ } };
const refuse = (kind, what) => { log(kind, what); const e = new Error('network blocked by the checker'); e.code = 'ECONNREFUSED'; return e; };
const net = require('net');
const origConnect = net.Socket.prototype.connect;
net.Socket.prototype.connect = function (...a) { const o = a[0]; const host = o && typeof o === 'object' ? (o.host || o.path) : a[1]; if (host && host !== 'localhost' && host !== '127.0.0.1') { const e = refuse('connect', host); process.nextTick(() => this.destroy(e)); return this; } return origConnect.apply(this, a); };
const dns = require('dns');
dns.lookup = function (host, ...a) { const cb = a[a.length - 1]; const e = refuse('dns', host); if (typeof cb === 'function') process.nextTick(() => cb(e)); };
for (const m of ['http', 'https']) {
  const mod = require(m);
  const orig = mod.request;
  mod.request = function (o, ...rest) { const host = typeof o === 'string' ? o : (o && (o.host || o.hostname)) || (o && o.href) || ''; log(m, host); return orig.call(this, o, ...rest); };
  mod.get = function (o, ...rest) { const r = mod.request(o, ...rest); r.end(); return r; };
}
if (typeof globalThis.fetch === 'function') globalThis.fetch = function (u) { log('fetch', typeof u === 'string' ? u : (u && u.url) || u); return Promise.reject(refuse('fetch', u)); };
