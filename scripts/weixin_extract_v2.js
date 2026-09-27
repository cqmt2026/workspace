/**
 * 快速提取微信视频号音频
 * 1. 调用 API 获取 feed 信息
 * 2. 从 coverUrl 提取 token 尝试不同参数
 * 3. 用 Playwright 带 cookie 尝试
 */
const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin2');
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

const SHORT_URI = 'AcH5mhteTb';

function callApi(shortUri) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      baseReq: { generalToken: '' },
      shortUri: shortUri
    });
    const req = https.request({
      hostname: 'channels.weixin.qq.com',
      path: '/finder-preview/api/feed/get_feed_info?_rid=test',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://channels.weixin.qq.com/finder-preview/pages/sph?id=' + shortUri,
        'Content-Length': Buffer.byteLength(data)
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        console.log('status:', res.statusCode);
        try {
          const json = JSON.parse(body);
          fs.writeFileSync(path.join(OUTPUT_DIR, 'feed.json'), JSON.stringify(json, null, 2));
          console.log(JSON.stringify(json, null, 2));
          resolve(json);
        } catch(e) {
          console.log('raw:', body.substring(0, 500));
          resolve(null);
        }
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// 用不同参数组合尝试下载视频
function tryDownloadUrl(url, dest) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    const file = fs.createWriteStream(dest);
    const req = client.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://channels.weixin.qq.com/'
      }
    });
    req.on('response', (res) => {
      console.log('download:', res.statusCode, res.headers['content-type'], res.headers['content-length']);
      if (res.statusCode === 200 && (res.headers['content-type'] || '').includes('video') && res.headers['content-length']) {
        const len = parseInt(res.headers['content-length']);
        if (len > 10000) {
          console.log('看起来是视频!', len, 'bytes');
          res.pipe(file);
          file.on('finish', () => {
            console.log('下载完成:', dest, fs.statSync(dest).size);
            resolve(true);
          });
        } else {
          console.log('文件太小，跳过');
          res.resume();
          res.on('end', () => resolve(false));
        }
      } else {
        res.resume();
        res.on('end', () => {
          file.close();
          resolve(false);
        });
      }
    });
    req.on('error', (e) => {
      file.close();
      resolve(false);
    });
  });
}

(async () => {
  const json = await callApi(SHORT_URI);
  if (!json) { console.error('API failed'); process.exit(1); }

  const coverUrl = json.data.feedInfo.coverUrl;
  const exportId = json.data.sceneInfo.dynamicExportId;
  console.log('\ncoverUrl:', coverUrl);
  console.log('exportId:', exportId);

  // 提取 URL 参数
  const m = coverUrl.match(/&m=([a-f0-9]+)/);
  const mVal = m ? m[1] : '';
  
  // 尝试不同参数的 stodownload
  const tries = [
    `https://finder.video.qq.com/251/20304/stodownload?${new URL(coverUrl).searchParams.toString().replace(/&?wxampicformat=\d+/, '').replace(/&?picformat=\d+/, '')}`,
    coverUrl.replace(/&wxampicformat=\d+/, '').replace(/&picformat=\d+/, ''),
    coverUrl + '&v=2',
    coverUrl + '&needfilekey=1',
    `https://finder.video.qq.com/export/${exportId}`,
    `https://finder.video.qq.com/finder/export/${exportId}`,
    coverUrl + '&video=1',
    coverUrl + '&format=video',
  ];

  for (let i = 0; i < tries.length; i++) {
    console.log(`\n--- 尝试 ${i+1}/${tries.length} ---`);
    console.log(tries[i].substring(0, 200));
    const ok = await tryDownloadUrl(tries[i], path.join(OUTPUT_DIR, `video_${i}.mp4`));
    if (ok) {
      console.log('找到视频!');
      // 提取音频
      await extractAudio(path.join(OUTPUT_DIR, `video_${i}.mp4`), path.join(OUTPUT_DIR, 'audio.mp3'));
      process.exit(0);
    }
  }

  console.log('\n所有尝试都失败');
  process.exit(1);
})();

function extractAudio(videoPath, audioPath) {
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