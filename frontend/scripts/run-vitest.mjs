#!/usr/bin/env node
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';

const [, , ...rawArgs] = process.argv;
let ciRequested = false;
const args = [];

for (const arg of rawArgs) {
  if (arg === '--ci') {
    ciRequested = true;
    continue;
  }
  args.push(arg);
}

if (ciRequested && !process.env.CI) {
  process.env.CI = 'true';
}

const require = createRequire(import.meta.url);
const vitestCli = require.resolve('vitest/dist/cli.js');

const child = spawn(process.execPath, [vitestCli, ...args], {
  stdio: 'inherit',
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
