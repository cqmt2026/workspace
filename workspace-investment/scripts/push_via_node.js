const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const msgFile = 'C:/Users/Administrator/.openclaw/workspace/workspace-investment/out_data/push_msg.txt';
const target = 'o9cq8092w_2W-BHmLsGGbleQEHKg@im.wechat';
const openclaw = 'C:/Users/Administrator/AppData/Roaming/npm/openclaw.cmd';

const msg = fs.readFileSync(msgFile, 'utf8');
console.log('Message length:', msg.length);
console.log('OpenClaw exists:', fs.existsSync(openclaw));

const args = ['message', 'send', '--target', target, '--message', msg];
console.log('Args:', JSON.stringify(args));

for (let i = 0; i < 3; i++) {
    try {
        const buf = execSync(`"${openclaw}" message send --target "${target}" --message "${msg.replace(/"/g, '\\"')}"`, {
            encoding: 'utf8',
            timeout: 20000,
            stdio: ['ignore', 'pipe', 'pipe']
        });
        console.log('stdout:', buf);
        console.log('SUCCESS');
        process.exit(0);
    } catch (e) {
        console.log(`Retry ${i+1}/3:`, e.message.slice(0, 100));
    }
}

// Fallback: try via temp file + powershell
console.log('Falling back to temp file approach');
const tmpFile = 'C:/Users/Administrator/.openclaw/workspace/workspace-investment/out_data/push_tmp.txt';
fs.writeFileSync(tmpFile, msg, 'utf8');

try {
    const psArgs = [
        '-ExecutionPolicy', 'Bypass', '-File',
        'C:/Users/Administrator/.openclaw/workspace/workspace-investment/scripts/send_via_tempfile.ps1',
        tmpFile, target, openclaw
    ];
    const buf = execSync(`powershell.exe ${psArgs.map(a => `"${a.replace(/"/g,'\\"')}"`).join(' ')}`, {
        encoding: 'utf8',
        timeout: 30000,
        stdio: ['ignore', 'pipe', 'pipe']
    });
    console.log('PowerShell result:', buf);
} catch (e) {
    console.log('PS error:', e.message.slice(0, 200));
}
