const fs = require('fs');
let content = fs.readFileSync('my-video/index.html', 'utf8');
// 查找所有包含data-depth的行
const lines = content.split('\n');
lines.forEach((line, i) => {
  if (line.includes('data-depth')) {
    console.log(`Line ${i+1}: ${line.trim()}`);
  }
});
