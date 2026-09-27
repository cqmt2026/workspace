const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const msg = fs.readFileSync(path.join(__dirname, '..', 'out_data', 'daily_decision_latest.txt'), 'utf8');
const target = 'o9cq8092w_2W-BHmLsGGbleQEHKg@im.wechat';
const openclaw = 'C:\\Users\\Administrator\\AppData\\Roaming\\npm\\openclaw.cmd';

console.log(`Message length: ${msg.length}`);
console.log(`Target: ${target}`);

const child = exec(`"${openclaw}" message send --target "${target}" --message "${msg.replace(/"/g, '\\"')}"`, {
  timeout: 20000,
  env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
}, (err, stdout, stderr) => {
  console.log('STDOUT:', stdout);
  console.log('STDERR:', stderr);
  if (err) console.log('Error:', err.message);
});

child.on('error', (err) => {
  console.log('Child error:', err.message);
});

child.on('close', (code) => {
  console.log('Exit code:', code);
  process.exit(code || 0);
});
