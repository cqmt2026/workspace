/**
 * 用 Playwright 打开微信视频号页面，捕获视频源，下载后提取音频
 */
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const { promisify } = require('util');
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');
const { pipeline } = promisify(require('stream').pipeline);

const VIDEO_URL = process.argv[2];
const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin');

async function downloadFile(fileUrl, destPath) {
  console.log('下载视频:', fileUrl);
  const client = fileUrl.startsWith('https') ? https : http;
  const file = fs.createWriteStream(destPath);
  const req = client.get(fileUrl, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Referer': 'https://channels.weixin.qq.com/'
    }
  });
  await pipeline(req, file);
  console.log('下载完成:', destPath, fs.statSync(destPath).size, 'bytes');
}

async function main() {
  if (!VIDEO_URL) {
    console.error('用法: node weixin_extract_audio.js <视频号链接>');
    process.exit(1);
  }
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  console.log('启动浏览器...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Users\\Administrator\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe',
    args: ['--no-sandbox']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    viewport: { width: 375, height: 812 }
  });
  const page = await context.newPage();

  // 监听所有网络响应
  const mediaUrls = [];
  page.on('response', (response) => {
    const u = response.url();
    if (u.match(/\.(mp4|m3u8|aac|mp3)/i)) {
      mediaUrls.push(u);
      console.log('发现媒体源:', u);
    }
  });

  console.log('打开:', VIDEO_URL);
  await page.goto(VIDEO_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });

  // 等待 JS 渲染 + 视频加载
  console.log('等待 12 秒...');
  await page.waitForTimeout(12000);

  // 尝试点击播放按钮
  try {
    const buttons = await page.$$('button, .play, [class*="play"]');
    for (const b of buttons) {
      const cls = await b.getAttribute('class');
      if (cls && cls.toLowerCase().includes('play')) {
        await b.click();
        await page.waitForTimeout(3000);
        break;
      }
    }
  } catch(e) {
    console.log('点击失败:', e.message);
  }

  // 收集所有来源
  const videoSrcs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('video')).map(v => v.currentSrc || v.src).filter(Boolean);
  });

  const pageContent = await page.content();
  const mp4Matches = (pageContent.match(/https?:\/\/[^"'\s&]+\.(mp4|m3u8)(?:\?[^"'\s]*)?/gi) || [])
    .filter(u => u.length > 100 && !u.includes('avatar') && !u.includes('thumb'));

  // 截图调试
  await page.screenshot({ path: path.join(OUTPUT_DIR, 'screenshot2.png') });

  console.log('video src:', videoSrcs);
  console.log('mediaUrls:', mediaUrls);
  console.log('mp4 from HTML:', mp4Matches.slice(0,5));

  let target = null;
  if (videoSrcs.length > 0) target = videoSrcs[0];
  else if (mediaUrls.length > 0) target = mediaUrls.find(u => !u.includes('avatar') && !u.includes('thumb') && u.includes('mp4')) || mediaUrls[0];
  else if (mp4Matches.length > 0) target = mp4Matches[0];

  if (!target) {
    console.error('未找到视频源');
    console.log('页面内容长度:', pageContent.length);
    await browser.close();
    process.exit(1);
  }

  console.log('目标视频:', target);
  await browser.close();

  const ext = target.includes('m3u8') ? 'm3u8' : 'mp4';
  const videoPath = path.join(OUTPUT_DIR, `video.${ext}`);
  await downloadFile(target, videoPath);

  const audioPath = path.join(OUTPUT_DIR, 'audio.mp3');
  console.log('提取音频中...');
  const ffmpeg = spawn('ffmpeg', [
    '-y', '-i', videoPath,
    '-vn', '-ar', '44100', '-ac', '2',
    '-b:a', '128k', audioPath
  ], { shell: false });

  ffmpeg.on('close', (code) => {
    if (code !== 0) { console.error('FFmpeg 失败, code=' + code); process.exit(1); }
    console.log('音频提取成功:', audioPath);
    console.log('文件大小:', fs.statSync(audioPath).size, 'bytes');
  });
}

main().catch(e => { console.error(e); process.exit(1); });