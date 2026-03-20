const path = require('path');

const rootDir = __dirname;
const logDir = path.join(rootDir, 'logs', 'node');
const pidDir = path.join(rootDir, 'pids', 'node');

const services = [
  'shopee-crawler',
  'tiktok-uploader',
  'tiktok-shop-miner',
  'tiktok-farm',
  'account-farm',
  'analytics',
  'admin-panel',
  'ai-video-generator',
  'click-tracker',
];

module.exports = {
  apps: services.map((service) => ({
    name: `node-${service}`,
    cwd: path.join(rootDir, 'services', service),
    script: 'npm',
    args: 'run start',
    instances: 1,
    exec_mode: 'fork',
    autorestart: true,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production',
    },
    out_file: path.join(logDir, `${service}.out.log`),
    error_file: path.join(logDir, `${service}.error.log`),
    pid_file: path.join(pidDir, `${service}.pid`),
  })),
};
