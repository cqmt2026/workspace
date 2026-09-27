const fs = require('fs');
let content = fs.readFileSync('my-video/index.html', 'utf8');
// 修复错误的引号嵌套：data-depth="\" 应该改为 data-depth='
content = content.replace(/data-depth="\\"/g, "data-depth='");
// 修复结尾的引号
content = content.replace(/"\]\s*,/g, "'],");
content = content.replace(/"\]\s*\)/g, "'])");
fs.writeFileSync('my-video/index.html', content, 'utf8');
console.log('Fixed');

// 验证修复
const scripts = content.match(/<script>([\s\S]*?)<\/script>/g) || [];
scripts.forEach((s, i) => {
  const code = s.replace(/<script>/, '').replace('</script>', '');
  try {
    new Function(code);
    console.log('Script ' + i + ': OK');
  } catch(e) {
    console.log('Script ' + i + ': ERROR - ' + e.message.substring(0, 100));
  }
});
