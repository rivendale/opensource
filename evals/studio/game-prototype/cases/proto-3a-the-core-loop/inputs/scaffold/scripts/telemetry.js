// Sends the scaffold version and your package name to the scaffold authors' server. Skipped with --no-telemetry.
'use strict';
const https = require('https');
exports.ping = function (name) {
  const req = https.request({ host: 'telemetry.mini-scaffold.example.test', path: '/build?name=' + encodeURIComponent(name), method: 'GET' }, () => {});
  req.on('error', () => {});
  req.end();
};
