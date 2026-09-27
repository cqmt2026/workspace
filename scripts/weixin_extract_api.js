/**
 * 用 Playwright 拦截视频号页面网络请求，提取视频信息 API 返回
 */
const { chromium } = require('playwright');
const { promisify } = require('util');
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');
const { spawn } = require('child_process');
const { pipeline } = promisify(require('stream').pipeline);

const VIDEO_URL = process.argv[2];
const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin');

async function main() {
  if (!VIDEO_URL) {
    console.error('用法: node weixin_extract_api.js <视频号链接>');
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
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();

  // 记录所有 XHR/fetch 请求
  const requests = [];
  page.on('request', (req) => {
    const url = req.url();
    if (url.includes('finder') || url.includes('sph') || url.includes('video') || url.includes('channels')) {
      requests.push({ url, method: req.method(), post: req.postData() });
      console.log('REQ:', req.method(), url);
    }
  });

  page.on('response', (response) => {
    const url = response.url();
    if (url.includes('finder') || url.includes('sph') || url.includes('channels') || url.includes('proxy')) {
      console.log('RESP:', response.status(), url);
    }
  });

  console.log('打开:', VIDEO_URL);
  await page.goto(VIDEO_URL, { waitUntil: 'networkidle', timeout: 30000 });

  // 等待 JS 加载
  await page.waitForTimeout(5000);

  console.log('\n=== 所有网络请求 ===');
  for (const r of requests) {
    console.log(r.method, r.url);
    if (r.post) console.log('  POST:', r.post.substring(0, 500));
  }

  // 也看页面内容
  const content = await page.content();
  console.log('\n=== 页面中可能的数据 ===');
  const stateMatches = content.match(/__INITIAL_STATE__["\']?\s*[:=]\s*({.+?})["\']/);
  if (stateMatches) {
    console.log('initial state 长度:', stateMatches[1].length);
    const cleaned = stateMatches[1].substring(0, 3000);
    console.log(cleaned);
  }

  // 找页面中嵌入的 JSON
  const scriptMatches = content.match(/<script[^>]*>([^<]{100,})<\/script>/gi);
  if (scriptMatches) {
    for (const s of scriptMatches) {
      const inner = s.replace(/<\/?script[^>]*>/gi, '');
      if (inner.includes('video') || inner.includes('sph') || inner.includes('url')) {
        console.log('SCRIPT snippet:', inner.substring(0, 1000));
      }
    }
  }

  // 直接获取页面中的 video 元素信息
  const pageData = await page.evaluate(() => {
    const result = {};
    // 查看 body 文本
    result.bodyText = document.body.innerText.substring(0, 500);
    // 查看 video 元素
    const videos = document.querySelectorAll('video');
    result.videos = Array.from(videos).map(v => ({
      src: v.src,
      currentSrc: v.currentSrc,
      readyState: v.readyState,
      duration: v.duration,
      networkState: v.networkState
    }));
    // 查看所有带 data-* 的 div
    const dataDivs = document.querySelectorAll('[data-video-id], [data-url], [data-share-url]');
    result.dataDivs = Array.from(dataDivs).slice(0, 5).map(d => ({
      tag: d.tagName,
      attrs: Object.fromEntries(Array.from(d.attributes).map(a => [a.name, a.value]))
    }));
    return result;
  });
  console.log('\n=== Page Data ===');
  console.log(JSON.stringify(pageData, null, 2));

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });