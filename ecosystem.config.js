const path = require('path');

const servicesRoot = path.join(__dirname, 'services');

const nodeServices = [
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
  apps: nodeServices.map((service) => ({
    name: `zttato-${service}`,
    cwd: path.join(servicesRoot, service),
    script: 'npm',
    args: 'run start',
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production',
    },
  })),
};
