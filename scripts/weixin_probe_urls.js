/**
 * 尝试不同参数组合下载视频号视频
 */
const https = require('https');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin');

const ENC = '2fG3V4WwQPl3wXSaNvRxIsOFkficGibL27eEdErOtdiboQdNYT0CoHwqMtTG9qGfD9VRGuvH4ibuSBqflWibb3xlD4wFUa9SJVM7JmINMPLNnXJM';
const TOKEN = 'Cvvj5Ix3eewIL2QHboXicEibHV95fpGicWZAllH5k82cxlLklk8QaYNoZFLvRLkq3zo6hcWmyzJ6SvoxMzc4OyBVcjQwQc87OojTQ85Kmym4RHI9vKFJUlYIrPiauClqXYacadEibdGRD8awqr7ia0iarU981yEKeWZcTrEylOkNKtmmz9Yy4MtcGticJTEcMvdUptRyVXZ3Yp8g5ibNvxPZ84IozVcY6De3LGm9VgzxfVRKqRDk';
const M = '1cc3eab9396f6e3be643637a3094b20c';
const EXPORT = 'UzFfBgAAxKihBHRUeymMjMzT4DCsIsqUOwMsQZgNedFiGaXyevcn23LW9w';

const urls = [
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=${TOKEN}&hy=SZ&idx=1&m=${M}&uzid=1&v=1`,
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=${TOKEN}&hy=SZ&idx=1&m=${M}&uzid=1&format=1080`,
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=${TOKEN}&hy=SZ&idx=1&m=${M}&uzid=1&needfilekey=1`,
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=${TOKEN}&hy=SZ&idx=1&m=${M}&uzid=1&filetype=mp4`,
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=${TOKEN}&hy=SZ&idx=1&m=${M}&uzid=1&size=1080`,
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=${TOKEN}&hy=SZ&idx=1&m=${M}&uzid=1&video=1`,
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=${TOKEN}&hy=SZ&idx=1&m=${M}&uzid=1&v=2`,
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=${TOKEN}&hy=SZ&idx=1&m=${M}&uzid=1&wxampicformat=0`,
  // 不带 wxampicformat/picformat
  `https://finder.video.qq.com/251/20304/stodownload?encfilekey=${ENC}&token=${TOKEN}&hy=SZ&idx=1&m=${M}&uzid=1`,
];

let idx = 0;
async function tryUrl(url) {
  idx++;
  return new Promise((resolve) => {
    https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://channels.weixin.qq.com/'
      },
      timeout: 15000
    }, (res) => {
      console.log(`#${idx} status=${res.statusCode} type=${res.headers['content-type']} len=${res.headers['content-length']}`);
      // 读前 200 字节
      let head = '';
      res.on('data', (chunk) => {
        head += chunk.toString('ascii').substring(0, 100);
        if (head.length > 100) {
          head = head.substring(0, 100);
          res.destroy();
        }
      });
      res.on('end', () => {
        const clean = head.replace(/[^\x20-\x7E]/g, '?');
        console.log(`  head: ${clean}`);
        resolve();
      });
    }).on('error', (e) => {
      console.log(`#${idx} error: ${e.message}`);
      resolve();
    });
  });
}

(async () => {
  for (const url of urls) {
    await tryUrl(url);
  }
})();