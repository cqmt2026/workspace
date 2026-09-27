/**
 * 用移动端 UA + token 调用视频号 API，尝试获取完整视频数据
 */
const https = require('https');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin');
const SHORT_URI = 'AGkywfIEbr';

// 用不同 token 和参数组合
async function callAPI(url, data, referer, ua) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(data);
    const req = https.request({
      hostname: 'channels.weixin.qq.com',
      path: url,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': ua,
        'Referer': referer,
        'Origin': 'https://channels.weixin.qq.com',
        'Content-Length': Buffer.byteLength(body)
      }
    }, (res) => {
      let text = '';
      res.on('data', chunk => text += chunk);
      res.on('end', () => {
        console.log('status:', res.statusCode);
        try {
          const json = JSON.parse(text);
          // 检查是否含 videoUrl
          const s = JSON.stringify(json);
          if (s.includes('videoUrl') || s.includes('video_url')) {
            console.log('=== 含视频URL ===');
            fs.writeFileSync(path.join(OUTPUT_DIR, 'feed_has_video.json'), JSON.stringify(json, null, 2));
          }
          console.log('响应:', JSON.stringify(json, null, 2).substring(0, 2000));
          resolve(json);
        } catch(e) {
          console.log('raw:', text.substring(0, 500));
          resolve(null);
        }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function main() {
  const mobileUa = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
  const pcUa = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

  // 尝试不同的 baseReq 组合
  const tests = [
    { name: 'base1', data: { baseReq: { generalToken: '' }, shortUri: SHORT_URI } },
    { name: 'base2', data: { baseReq: { generalToken: '', scene: 1 }, shortUri: SHORT_URI } },
    { name: 'base3', data: { baseReq: { generalToken: '', platform: 1 }, shortUri: SHORT_URI } },
    { name: 'base4', data: { baseReq: { generalToken: '', appid: '1101' }, shortUri: SHORT_URI } },
    { name: 'base5', data: { baseReq: { generalToken: '', platform: 1, scene: 1 }, shortUri: SHORT_URI } },
  ];

  for (const t of tests) {
    console.log(`\n=== ${t.name} ===`);
    await callAPI('/finder-preview/api/feed/get_feed_info?_rid=test',
      t.data,
      'https://channels.weixin.qq.com/finder-preview/pages/sph?id=' + SHORT_URI,
      pcUa);
  }
}

main().catch(console.error);