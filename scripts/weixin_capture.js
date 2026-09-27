/**
 * 拦截视频号页面所有 XHR/fetch 请求，找含 videoUrl 的响应
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

async function downloadVideo(videoUrl, destPath) {
  console.log('下载视频:', videoUrl);
  const client = videoUrl.startsWith('https') ? https : http;
  const file = fs.createWriteStream(destPath);
  const req = client.get(videoUrl, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Referer': 'https://channels.weixin.qq.com/'
    }
  });
  await pipeline(req, file);
  console.log('下载完成:', fs.statSync(destPath).size, 'bytes');
}

async function main() {
  if (!VIDEO_URL) { console.error('用法: node weixin_capture.js <分享链接>'); process.exit(1); }

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

  // 拦截所有 XHR/fetch 响应
  const videoUrl = [];
  page.on('response', async (response) => {
    const url = response.url();
    const ct = response.headers()['content-type'] || '';
    if (!url.includes('channels.weixin.qq.com') && !url.includes('finder.video.qq.com')) return;
    if (ct.includes('text') || ct.includes('json') || url.includes('get_feed') || url.includes('feed')) {
      try {
        const json = await response.json();
        const s = JSON.stringify(json);
        // 检查是否包含 videoUrl
        if (s.includes('videoUrl') || s.includes('video_url')) {
          console.log('=== 含视频URL的API响应 ===');
          console.log('URL:', url);
          console.log('Response size:', s.length);
          // 提取 videoUrl 值
          const mp4 = [...s.matchAll(/https?:\/?\/[^"\\]+\.(?:mp4|m3u8)/g)].map(m => m[0].replace(/\\u002F/g, '/'));
          if (mp4.length) {
            console.log('提取到的视频URL:', mp4);
            for (const v of mp4) {
              videoUrl.push(v);
            }
          }
          fs.writeFileSync(path.join(OUTPUT_DIR, 'feed_full.json'), s);
        }
      } catch(e) {
        // not JSON
      }
    }
  });

  console.log('打开:', VIDEO_URL);
  await page.goto(VIDEO_URL, { waitUntil: 'networkidle', timeout: 30000 });

  // 等更长时间让所有请求完成
  console.log('等待15秒...');
  await page.waitForTimeout(15000);

  // 尝试通过页面 JS 获取 feed 数据
  const feedData = await page.evaluate(() => {
    // 找 Vue 实例中的数据
    const app = document.querySelector('#app');
    if (!app) return null;
    
    // 尝试访问 Vue devtools 暴露的数据
    const vm = app.__vue__ || app.__vueParentComponent;
    if (!vm) return null;
    
    try {
      // 遍历组件树找 feed 数据
      const walk = (comp, depth = 0) => {
        if (!comp || depth > 20) return null;
        const data = comp.data || comp.$.data || {};
        if (data && (data.feed || data.videoUrl)) {
          return { comp: comp.__vccOpts && comp.__vccOpts.__name, data };
        }
        if (comp.subTree) return walk(comp.subTree, depth + 1);
        if (comp.sub树的 && comp.sub树的.subTree) return walk(comp.sub树的.subTree, depth + 1);
        return null;
      };
      return walk(vm);
    } catch(e) {
      return null;
    }
  }).catch(e => null);
  console.log('Vue数据:', JSON.stringify(feedData).substring(0, 500));

  console.log('找到的视频URL:', videoUrl);
  
  await browser.close();

  if (videoUrl.length === 0) {
    console.error('未找到视频URL');
    process.exit(1);
  }

  // 下载视频并提取音频
  const vurl = videoUrl[0];
  const videoPath = path.join(OUTPUT_DIR, 'video.mp4');
  await downloadVideo(vurl, videoPath);

  const audioPath = path.join(OUTPUT_DIR, 'audio.mp3');
  console.log('提取音频...');
  const ffmpeg = spawn('ffmpeg', [
    '-y', '-i', videoPath,
    '-vn', '-ar', '44100', '-ac', '2',
    '-b:a', '128k', audioPath
  ], { shell: false });

  ffmpeg.on('close', (code) => {
    if (code !== 0) { console.error('FFmpeg失败'); process.exit(1); }
    console.log('音频提取成功:', audioPath);
    console.log('大小:', fs.statSync(audioPath).size, 'bytes');
  });
}

main().catch(e => { console.error(e); process.exit(1); });