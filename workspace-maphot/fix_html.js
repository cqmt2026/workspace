const fs = require('fs');
let content = fs.readFileSync('my-video/index.html', 'utf8');
// 修复所有data-depth的引号问题
content = content.replace(/data-depth='\s*\+\s*/g, "data-depth='\" + ");
content = content.replace(/\s*\+\s*'\]'/g, " + '\"]'");
fs.writeFileSync('my-video/index.html', content, 'utf8');
console.log('Fixed HTML');

// 验证
const scripts = content.match(/<script>([\s\S]*?)<\/script>/g) || [];
scripts.forEach((s, i) => {
  const code = s.replace(/<script>/, '').replace('</script>', '');
  try {
    new Function(code);
    console.log('Script ' + i + ': OK');
  } catch(e) {
    console.log('Script ' + i + ': ERROR - ' + e.message.substring(0, 80));
  }
});
