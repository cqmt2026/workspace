/**
 * 用已获取的 token 尝试不同参数组合下载视频
 */
const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin2');
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

const ENC = '2fG3V4WwQPl3wXSaNvRxIsOFkficGibL27eEdErOtdiboQdNYT0CoHwqMtTG9qGfD9VRGuvH4ibuSBqflWibb3xlD4wFUa9SJVM7JmINMPLNnXJM';
const TOKEN = 'Cvvj5I…8jY';
const M = '1cc3eab9396f6e3be643637a3094b20c';

const urls = [
  // 不带缩略图参数
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=1&m=${M}&uzid=1`,
  // 带 format
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=1&m=${M}&uzid=1&format=1080`,
  // 带 media_type
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=1&m=${M}&uzid=1&media_type=4`,
  // wxampicformat=0
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=1&m=${M}&uzid=1&wxampicformat=0&picformat=0`,
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=1&m=${M}&uzid=1&wxampicformat=400&picformat=100`,
  // idx=2,3
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=2&m=${M}&uzid=1`,
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=3&m=${M}&uzid=1`,
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=2&m=${M}&uzid=1&format=1080`,
  // 带 wxuin
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=1&m=${M}&uzid=1&wxuin=1`,
  // 不带 uzid
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=1&m=${M}`,
  // 带 download=1
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=***&hy=SZ&idx=1&m=${M}&uzid=1&download=1`,
];

async function tryUrl(url, idx) {
  return new Promise((resolve) => {
    https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://channels.weixin.qq.com/'
      },
      timeout: 15000
    }, (res) => {
      const ct = res.headers['content-type'] || '';
      const len = parseInt(res.headers['content-length'] || '0');
      console.log(`#${idx+1} status=${res.statusCode} type=${ct} len=${len}`);
      
      // 读前 32 字节
      const chunks = [];
      let total = 0;
      res.on('data', (chunk) => {
        if (total < 32) {
          chunks.push(chunk);
          total += chunk.length;
        }
        // 如果文件很大，下载
        if (len > 1000000) {
          chunks.push(chunk);
          total += chunk.length;
        }
      });
      res.on('end', () => {
        const headBuf = Buffer.concat(chunks).slice(0, 32);
        const sig = headBuf.slice(0, 4).toString('hex');
        const head = headBuf.slice(0, 20).toString('ascii').replace(/[^\x20-\x7E]/g, '?');
        console.log(`  sig=${sig} head=${head}`);
        
        if (len > 1000000 && (ct.includes('video') || ct.includes('octet-stream'))) {
          console.log('*** 视频! 下载中...');
          const dest = path.join(OUTPUT_DIR, 'video.mp4');
          const file = fs.createWriteStream(dest);
          const req2 = https.get(url, {
            headers: {
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
              'Referer': 'https://channels.weixin.qq.com/'
            }
          });
          req2.pipe(file);
          file.on('finish', () => {
            console.log('下载完成:', fs.statSync(dest).size, 'bytes');
            resolve(true);
          });
          req2.on('error', () => { resolve(false); });
        } else {
          resolve(false);
        }
      });
    }).on('error', (e) => {
      console.log(`#${idx+1} error: ${e.message}`);
      resolve(false);
    });
  });
}

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
  for (let i = 0; i < urls.length; i++) {
    console.log(`\n--- 尝试 ${i+1} ---`);
    console.log(urls[i].substring(0, 150));
    const ok = await tryUrl(urls[i], i);
    if (ok) {
      await extractAudio(path.join(OUTPUT_DIR, 'video.mp4'), path.join(OUTPUT_DIR, 'audio.mp3'));
      process.exit(0);
    }
  }
  console.log('\n所有尝试失败');
  process.exit(1);
})();