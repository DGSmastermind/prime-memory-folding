#!/usr/bin/env node

const { spawn } = require("child_process");
const path = require("path");

const packageRoot = path.resolve(__dirname, "..");
const python = process.env.PYTHON || "python3";
const child = spawn(
  python,
  ["-m", "prime_memory_folding.mcp_server", ...process.argv.slice(2)],
  {
    cwd: packageRoot,
    env: {
      ...process.env,
      PYTHONPATH: [packageRoot, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter)
    },
    stdio: "inherit"
  }
);

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
});
