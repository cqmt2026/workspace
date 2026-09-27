/**
 * 直接调用视频号 API，获取 feed 信息
 */
const https = require('https');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin');
const SHORT_URI = 'AGkywfIEbr';

// 先调用 get_feed_info 看完整响应
function callFeedInfo(shortUri) {
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://channels.weixin.qq.com/finder-preview/pages/sph?id=' + shortUri,
        'Origin': 'https://channels.weixin.qq.com',
        'Content-Length': Buffer.byteLength(data)
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        console.log('status:', res.statusCode);
        console.log('content-type:', res.headers['content-type']);
        try {
          const json = JSON.parse(body);
          fs.writeFileSync(path.join(OUTPUT_DIR, 'feed_full2.json'), JSON.stringify(json, null, 2));
          console.log('完整响应:');
          console.log(JSON.stringify(json, null, 2));
          resolve(json);
        } catch(e) {
          console.log('raw:', body.substring(0, 2000));
          resolve(null);
        }
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// 也试一下不带 _rid 的版本
function callFeedInfoV2(shortUri) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      baseReq: { generalToken: '' },
      shortUri: shortUri
    });
    
    const req = https.request({
      hostname: 'channels.weixin.qq.com',
      path: '/api/feed/get_feed_info',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://channels.weixin.qq.com/',
        'Content-Length': Buffer.byteLength(data)
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        console.log('V2 status:', res.statusCode);
        try {
          const json = JSON.parse(body);
          console.log('V2 response:', JSON.stringify(json, null, 2).substring(0, 2000));
        } catch(e) {
          console.log('V2 raw:', body.substring(0, 500));
        }
        resolve();
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

(async () => {
  console.log('调用 feed/get_feed_info...');
  await callFeedInfo(SHORT_URI);
  console.log('\n--- 尝试 /api/feed/get_feed_info ---');
  await callFeedInfoV2(SHORT_URI);
})();