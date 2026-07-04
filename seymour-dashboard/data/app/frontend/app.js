function fmtHashrate(v) {
  if (!v || isNaN(v)) return "—";
  if (v >= 1e15) return (v / 1e15).toFixed(2) + " PH/s";
  if (v >= 1e12) return (v / 1e12).toFixed(2) + " TH/s";
  if (v >= 1e9) return (v / 1e9).toFixed(2) + " GH/s";
  return v.toFixed(2) + " H/s";
}

async function load() {
  const health = await fetch("/api/health").then(r => r.json());
  document.getElementById("appStatus").textContent = health.status.toUpperCase();
  document.getElementById("statusBadge").textContent = "Seymour app online";

  const mc = await fetch("/api/miningcore").then(r => r.json());

  document.getElementById("mcStatus").textContent = mc.connected ? "ONLINE" : "OFFLINE";
  document.getElementById("mcStatus").className = mc.connected ? "value green" : "value red";

  if (mc.connected && mc.pool && mc.pool.pool) {
    const pool = mc.pool.pool;
    document.getElementById("hashrate").textContent = fmtHashrate(pool.poolStats?.poolHashrate || 0);
    document.getElementById("workers").textContent = pool.poolStats?.connectedMiners || "—";
  }

  document.getElementById("raw").textContent = JSON.stringify(mc, null, 2);
}

load();
setInterval(load, 10000);
