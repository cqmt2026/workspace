const fs = require('fs');
const html = fs.readFileSync('my-video/index.html', 'utf8');
const scripts = html.match(/<script>([\s\S]*?)<\/script>/g) || [];
scripts.forEach((s, i) => {
  const code = s.replace(/<script>/, '').replace('</script>', '');
  try {
    new Function(code);
    console.log('Script ' + i + ': OK');
  } catch(e) {
    console.log('Script ' + i + ': ERROR - ' + e.message);
    // 找出错误位置
    const match = e.message.match(/position\s+(\d+)/i);
    if (match) {
      const pos = parseInt(match[1]);
      console.log('Error around position: ' + pos);
      console.log('Context: ...' + code.substring(Math.max(0, pos-50), pos+50) + '...');
    }
  }
});
