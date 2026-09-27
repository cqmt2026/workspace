/**
 * 用 Playwright 打开视频号页面，从页面 JS 中提取 videoUrl
 * 关键：等待所有 XHR 完成，然后从页面 data 中找 videoUrl
 */
const { chromium } = require('playwright');
const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin2');
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

async function extractAudio(videoPath, audioPath) {
  return new Promise((resolve) => {
    const ffmpeg = spawn('ffmpeg', [
      '-y', '-i', videoPath,
      '-vn', '-ar', '44100', '-ac', '2',
      '-b:a', '128k', audioPath
    ], { shell: false });
    ffmpeg.on('close', (code) => {
      if (code !== 0) { console.error('FFmpeg failed'); resolve(); return; }
      console.log('音频提取成功:', audioPath, fs.statSync(audioPath).size, 'bytes');
      resolve();
    });
  });
}

(async () => {
  console.log('启动 Playwright...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Users\\Administrator\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe',
    args: ['--no-sandbox', '--disable-blink-features=AutomationControlled']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 720 }
  });

  // 从 feed 页面先获取 token
  console.log('访问旧链接获取 token...');
  const page = await context.newPage();

  // 记录所有 API 响应
  const apiResponses = [];
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('get_feed_info') && url.includes('channels.weixin.qq.com')) {
      console.log('捕获到 feed API:', response.status());
      try {
        const json = await response.json();
        apiResponses.push({ url, json });
        fs.writeFileSync(path.join(OUTPUT_DIR, 'api_response.json'), JSON.stringify(json, null, 2));
        console.log('API响应:', JSON.stringify(json, null, 2).substring(0, 500));
      } catch(e) {}
    }
  });

  // 访问旧链接，浏览器会自动带上 cookie（如果有）
  await page.goto('https://weixin.qq.com/sph/AGkywfIEbr', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(5000);

  // 收集页面中所有视频相关信息
  const pageData = await page.evaluate(() => {
    // 查找所有 script 中可能嵌入的 JSON
    const scripts = document.querySelectorAll('script');
    const results = {};
    for (const s of scripts) {
      const text = s.textContent || '';
      if (text.includes('videoUrl') || text.includes('video_url') || text.includes('h265VideoInfo')) {
        results.snippet = text.substring(0, 2000);
      }
      if (text.includes('__INITIAL_STATE__')) {
        results.initState = text.substring(0, 1000);
      }
    }

    // 查找 video 元素
    const videos = Array.from(document.querySelectorAll('video'));
    results.videos = videos.map(v => ({ src: v.src, currentSrc: v.currentSrc, readyState: v.readyState }));

    // 查找 source 元素
    const sources = Array.from(document.querySelectorAll('source'));
    results.sources = sources.map(s => s.src);

    // 页面文本
    results.bodyText = document.body.innerText.substring(0, 500);
    results.url = window.location.href;

    return results;
  });
  console.log('页面数据:', JSON.stringify(pageData, null, 2));

  // 也尝试通过 Playwright 的 request 获取 cookie
  const cookies = await context.cookies('https://channels.weixin.qq.com');
  console.log('Channels cookies:', JSON.stringify(cookies, null, 2));

  await browser.close();

  // 从旧链接的 API 响应中获取 token
  if (apiResponses.length === 0) {
    console.log('没有捕获到 API 响应');
  }

  // 不管有没有旧链接的 cookie，都用当前浏览器的 cookie 访问新链接
  console.log('\n--- 重新打开新链接 ---');
  const browser2 = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Users\\Administrator\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe',
    args: ['--no-sandbox']
  });
  const context2 = await browser2.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 720 }
  });
  const page2 = await context2.newPage();

  const allMedia = [];
  page2.on('response', async (response) => {
    const url = response.url();
    if (url.includes('stodownload') || url.includes('.mp4')) {
      allMedia.push(url);
      console.log('发现媒体:', url);
    }
    if (url.includes('get_feed_info')) {
      try {
        const json = await response.json();
        fs.writeFileSync(path.join(OUTPUT_DIR, 'new_feed.json'), JSON.stringify(json, null, 2));
        const s = JSON.stringify(json);
        if (s.includes('videoUrl')) {
          console.log('!!! 新链接含 videoUrl !!!');
        }
        console.log('新链接 API 响应:', JSON.stringify(json, null, 2).substring(0, 500));
      } catch(e) {}
    }
  });

  await page2.goto('https://weixin.qq.com/sph/AcH5mhteTb', { waitUntil: 'networkidle', timeout: 30000 });
  await page2.waitForTimeout(10000);

  console.log('所有媒体:', allMedia);

  // 查看新链接页面数据
  const newData = await page2.evaluate(() => {
    const videos = Array.from(document.querySelectorAll('video'));
    const sources = Array.from(document.querySelectorAll('source'));
    const html = document.documentElement.outerHTML;
    return {
      videos: videos.map(v => ({ src: v.src, currentSrc: v.currentSrc })),
      sources: sources.map(s => s.src),
      hasVideoTag: !!document.querySelector('video'),
      bodyText: document.body.innerText.substring(0, 500),
      htmlLength: html.length,
      htmlSnippet: html.substring(0, 500)
    };
  });
  console.log('新链接页面:', JSON.stringify(newData, null, 2));

  await browser2.close();
})();