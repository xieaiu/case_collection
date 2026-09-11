const http = require('node:http');
const { sign } = require('./sign');

const port = Number(process.env.JD_H5ST_PORT || 3456);
const server = http.createServer((req, res) => {
  if (req.method !== 'POST' || req.url !== '/sign') {
    res.writeHead(404); res.end('Not Found'); return;
  }
  let body = '';
  req.on('data', chunk => { body += chunk; if (body.length > 1024 * 1024) req.destroy(); });
  req.on('end', () => {
    try {
      const payload = JSON.parse(body || '{}');
      const result = sign(payload.input, payload.seed || {
        token: process.env.JD_H5ST_TOKEN || '',
        fingerprint: process.env.JD_H5ST_FINGERPRINT || '',
        isNormal: process.env.JD_H5ST_IS_NORMAL === '1'
      });
      const out = { output: result, h5stLength: result?.h5st ? String(result.h5st).length : 0 };
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify(out));
    } catch (error) {
      res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ error: String(error.message || error) }));
    }
  });
});
server.listen(port, () => console.log(`jd_h5st signer listening on http://127.0.0.1:${port}/sign`));
