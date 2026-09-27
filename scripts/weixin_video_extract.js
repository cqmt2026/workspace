/**
 * 微信视频号视频提取 - 从分享链接获取视频信息
 * 用法: node weixin_video_extract.js <分享链接>
 */

const https = require('https');
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');

// 解析分享链接，获取实际视频ID
function resolveShareUrl(shareUrl) {
  return new Promise((resolve, reject) => {
    const client = shareUrl.startsWith('https') ? https : http;
    const options = { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' } };
    
    client.get(shareUrl, options, (res) => {
      // 跟随重定向
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        const redirectUrl = res.headers.location.startsWith('http') 
          ? res.headers.location 
          : new URL(res.headers.location, shareUrl).href;
        resolve(resolveShareUrl(redirectUrl));
        return;
      }
      resolve({ url: res.headers.location || shareUrl, finalUrl: res.responseUrl || shareUrl });
    }).on('error', reject);
  });
}

// 提取视频页面中的视频源信息
function extractVideoInfo(videoUrl) {
  return new Promise((resolve, reject) => {
    const client = videoUrl.startsWith('https') ? https : http;
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
      }
    };

    client.get(videoUrl, options, (res) => {
      let html = '';
      res.on('data', chunk => html += chunk);
      res.on('end', () => {
        // 尝试查找视频源地址
        const patterns = [
          // 微信视频号常见的视频源格式
          /videoUrl["']?\s*[:=]\s*["']([^"']+\.(?:mp4|m3u8)[^"']*?)["']/,
          /video_url["']?\s*[:=]\s*["']([^"']+\.(?:mp4|m3u8)[^"']*?)["']/,
          /src["']?\s*[:=]\s*["']([^"']+\.(?:mp4|m3u8)[^"']*?)["']/i,
          /"url"\s*:\s*"([^"]+\.(?:mp4|m3u8)[^"]*?)"/,
          /"playUrl"\s*:\s*"([^"]+)"/,
          /"videoUrl"\s*:\s*"([^"]+)"/,
          /<video[^>]+src=["']([^"']+)["']/,
        ];

        let videoUrlFound = null;
        for (const pattern of patterns) {
          const match = html.match(pattern);
          if (match) {
            videoUrlFound = match[1].replace(/\\u002F/g, '/').replace(/\\/g, '');
            break;
          }
        }

        // 也查找JSON数据
        const jsonMatches = html.match(/window\.__INITIAL_STATE__\s*=\s*({.+?});/);
        let jsonData = null;
        if (jsonMatches) {
          try {
            jsonData = JSON.parse(jsonMatches[1]);
          } catch(e) {
            // try unicode escape
            try {
              jsonData = JSON.parse(jsonMatches[1].replace(/\\u([0-9a-fA-F]{4})/g, (m, c) => String.fromCharCode(parseInt(c, 16))));
            } catch(e2) {}
          }
        }

        resolve({ html, videoUrl: videoUrlFound, jsonData, url: videoUrl });
      });
    }).on('error', reject);
  });
}

async function main() {
  const shareUrl = process.argv[2];
  if (!shareUrl) {
    console.error('用法: node weixin_video_extract.js <分享链接>');
    process.exit(1);
  }

  console.log('解析链接:', shareUrl);
  
  // 直接获取页面
  const result = await extractVideoInfo(shareUrl);
  
  // 如果没找到，可能被重定向了
  if (!result.videoUrl) {
    // 尝试跟随重定向
    const resolved = await resolveShareUrl(shareUrl);
    console.log('重定向到:', resolved.url);
    const result2 = await extractVideoInfo(resolved.url);
    
    if (result2.videoUrl) {
      console.log('找到视频源:', result2.videoUrl);
      return { videoUrl: result2.videoUrl, data: result2 };
    }
    
    // 输出部分HTML供调试
    console.log('--- HTML前2000字符 ---');
    console.log(result2.html.substring(0, 2000));
    console.log('---');
    console.log('未找到视频源');
  } else {
    console.log('找到视频源:', result.videoUrl);
  }
}

main().catch(console.error);