/**
 * 用 Playwright 等视频号页面 video 元素加载，然后获取视频源
 */
const { chromium } = require('playwright');
const https = require('https');
const http = require('http');
const { pipeline } = require('stream').promises;
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const VIDEO_URL = process.argv[2];
const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin');
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

async function main() {
  if (!VIDEO_URL) { console.error('用法: node weixin_get_video.js <分享链接>'); process.exit(1); }

  console.log('启动浏览器...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Users\\Administrator\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe',
    args: ['--no-sandbox']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 720 }
  });
  const page = await context.newPage();

  // 记录所有媒体 URL
  const mediaUrls = new Set();
  page.on('response', async (response) => {
    const url = response.url();
    // 记录所有媒体类型
    if (url.match(/\.mp4/)) mediaUrls.add(url);
    if (url.includes('stodownload')) mediaUrls.add(url);
  });

  console.log('打开:', VIDEO_URL);
  await page.goto(VIDEO_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });

  // 等 JS 渲染
  await page.waitForTimeout(10000);

  // 获取页面中所有 video 元素
  const info = await page.evaluate(() => {
    const videos = Array.from(document.querySelectorAll('video'));
    const sources = Array.from(document.querySelectorAll('source'));
    return {
      videos: videos.map(v => ({
        src: v.src,
        currentSrc: v.currentSrc,
        readyState: v.readyState,
        networkState: v.networkState,
        duration: v.duration,
        paused: v.paused
      })),
      sources: sources.map(s => s.src),
      bodyText: document.body.innerText.substring(0, 200)
    };
  });
  console.log('页面元素:', JSON.stringify(info, null, 2));

  // 收集所有 stodownload 请求
  console.log('捕获到的媒体 URL:', [...mediaUrls]);

  // 如果还是没找到，用 evaluate 找页面中可能的 video 数据
  if (info.videos.length === 0) {
    // 查找包含 video 字段的 data-* 属性
    const data = await page.evaluate(() => {
      const els = Array.from(document.querySelectorAll('[data-video], [data-share], [data-url]'));
      return els.map(e => ({
        tag: e.tagName,
        attrs: Object.fromEntries(Array.from(e.attributes).map(a => [a.name, a.value.substring(0, 200)]))
      }));
    });
    console.log('data-* 元素:', JSON.stringify(data, null, 2));

    // 找所有 iframe
    const iframes = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('iframe')).map(f => ({
        src: f.src,
        id: f.id
      }));
    });
    console.log('iframes:', iframes);
  }

  // 截图
  await page.screenshot({ path: path.join(OUTPUT_DIR, 'screenshot3.png'), fullPage: true });

  // 尝试通过 page.route 拦截下一个加载
  // 看看页面中是否有隐藏的 video 信息
  const allMedia = await page.evaluate(() => {
    // 找所有可能的视频 URL 在 HTML 中
    const html = document.documentElement.outerHTML;
    const mp4 = [...html.matchAll(/https?:\/\/[^"'\s]+\.mp4[^"'\s]*/g)].map(m => m[0]);
    const vostd = [...html.matchAll(/stodownload\?[^"'\s]+/g)].map(m => m[0]);
    return { mp4, vostd };
  });
  console.log('HTML 中的视频:', JSON.stringify(allMedia, null, 2));

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });