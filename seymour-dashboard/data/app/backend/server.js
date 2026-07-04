const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = 3000;

const miningcoreApi = process.env.MININGCORE_API || "http://192.168.1.156:4000";

function sendJson(res, data) {
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify(data, null, 2));
}

function sendFile(res, filePath, contentType) {
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }
    res.writeHead(200, { "Content-Type": contentType });
    res.end(data);
  });
}

async function fetchJson(url) {
  const r = await fetch(url, { signal: AbortSignal.timeout(5000) });
  return await r.json();
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.url === "/api/health") {
      return sendJson(res, {
        app: "Seymour Dashboard",
        status: "online",
        miningcoreApi,
        timestamp: new Date().toISOString()
      });
    }

    if (req.url === "/api/miningcore") {
      try {
        const stats = await fetchJson(`${miningcoreApi}/api/pools/bch`);
        return sendJson(res, {
          connected: true,
          source: miningcoreApi,
          pool: stats
        });
      } catch (e) {
        return sendJson(res, {
          connected: false,
          source: miningcoreApi,
          error: e.message
        });
      }
    }

    if (req.url === "/" || req.url === "/index.html") {
      return sendFile(res, path.join(__dirname, "../frontend/index.html"), "text/html");
    }

    if (req.url === "/app.js") {
      return sendFile(res, path.join(__dirname, "../frontend/app.js"), "application/javascript");
    }

    if (req.url === "/style.css") {
      return sendFile(res, path.join(__dirname, "../frontend/style.css"), "text/css");
    }

    res.writeHead(404);
    res.end("Not found");
  } catch (e) {
    res.writeHead(500);
    res.end(e.message);
  }
});

server.listen(PORT, () => {
  console.log(`Seymour Dashboard backend running on ${PORT}`);
});
