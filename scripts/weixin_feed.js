/**
 * 拦截视频号 feed API 响应，提取视频 URL
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const VIDEO_URL = process.argv[2];
const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin');
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

async function main() {
  if (!VIDEO_URL) { console.error('用法: node weixin_feed.js <视频号链接>'); process.exit(1); }

  console.log('启动浏览器...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Users\\Administrator\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe',
    args: ['--no-sandbox']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();

  // 拦截 feed API 响应
  let feedData = null;
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('get_feed_info')) {
      console.log('捕获到 feed API 响应:', response.status());
      try {
        const json = await response.json();
        feedData = json;
        fs.writeFileSync(path.join(OUTPUT_DIR, 'feed_response.json'), JSON.stringify(json, null, 2));
        console.log('feed JSON 已保存');
        // 打印关键点
        const s = JSON.stringify(json);
        // 找所有 url 字段
        const urls = [];
        let i = 0;
        while ((i = s.indexOf('"url"', i)) !== -1) {
          const start = Math.max(0, i - 10);
          urls.push(s.substring(start, Math.min(s.length, i + 300)));
          i += 5;
        }
        console.log('feed 中 url 字段:');
        urls.forEach(u => console.log(' ', u));

        // 找 mp4/m3u8
        const media = s.match(/https?:\/\/[^"\\]+\.mp4[^"\\]*/g) || [];
        const m3u8 = s.match(/https?:\/\/[^"\\]+\.m3u8[^"\\]*/g) || [];
        if (media.length) console.log('mp4 URLs:', media);
        if (m3u8.length) console.log('m3u8 URLs:', m3u8);
      } catch(e) {
        console.log('parse error:', e.message);
      }
    }
  });

  console.log('打开:', VIDEO_URL);
  await page.goto(VIDEO_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(5000);

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });