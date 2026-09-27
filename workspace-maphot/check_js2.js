const fs = require('fs');
const html = fs.readFileSync('my-video/index.html', 'utf8');
const scripts = html.match(/<script>([\s\S]*?)<\/script>/g) || [];
const s2 = scripts[2].replace(/<script>/, '').replace('</script>', '');
console.log('Script 2 length: ' + s2.length);
// 尝试逐行检查
const lines = s2.split('\n');
let accumulated = '';
for (let i = 0; i < lines.length; i++) {
  accumulated += lines[i] + '\n';
  try {
    new Function(accumulated);
  } catch(e) {
    if (e.message.includes('Invalid or unexpected token')) {
      console.log('Error at line ' + (i+1) + ':');
      console.log('Line: ' + lines[i]);
      console.log('Accumulated preview: ' + accumulated.substring(Math.max(0, accumulated.length-200)));
      break;
    }
  }
}
