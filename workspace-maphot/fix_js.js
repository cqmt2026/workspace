const fs = require('fs');
let content = fs.readFileSync('my-video/index.html', 'utf8');
// 修复单引号嵌套问题：将 data-depth='" 改为 data-depth=\"
content = content.replace(/data-depth='"/g, 'data-depth="\\"');
content = content.replace(/'"\]\s*,/g, '"\]","');
content = content.replace(/'"\]\s*\)/g, '"\]")');
fs.writeFileSync('my-video/index.html', content, 'utf8');
console.log('Fixed');
