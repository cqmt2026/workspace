/**
 * 解析微信 Radium 浏览器的 Simple Cache，提取视频
 */
const fs = require('fs');
const path = require('path');

const CACHE_DIR = 'C:\\Users\\Administrator\\AppData\\Roaming\\Tencent\\xwechat\\radium\\web\\profiles\\multitab_6cb1da877eed1733a5c6084e5af0f138\\Cache\\Cache_Data';
const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin2');
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// 读取 data_3 (33MB block)
const data3Path = path.join(CACHE_DIR, 'data_3');
const buf = fs.readFileSync(data3Path);
console.log('data_3 size:', (buf.length / 1024 / 1024).toFixed(1), 'MB');

// 搜索 ftyp (mp4 header)
let ftypPos = buf.indexOf('ftyp');
if (ftypPos >= 0) {
  console.log('ftyp found at', ftypPos);
  const snippet = buf.slice(Math.max(0, ftypPos - 4), Math.min(buf.length, ftypPos + 32));
  console.log('snippet:', snippet.toString('ascii').replace(/[^\x20-\x7E]/g, '.'));
}

// 搜索 moov
let moovPos = buf.indexOf('moov');
if (moovPos >= 0) {
  console.log('moov found at', moovPos);
  const snippet = buf.slice(Math.max(0, moovPos - 4), Math.min(buf.length, moovPos + 32));
  console.log('snippet:', snippet.toString('ascii').replace(/[^\x20-\x7E]/g, '.'));
}

// 搜索 Lavc (H.264/AVC data)
let searchPos = 0;
const lavcPositions = [];
while ((searchPos = buf.indexOf('Lavc', searchPos)) >= 0) {
  lavcPositions.push(searchPos);
  searchPos += 4;
}
console.log('Lavc found at', lavcPositions.length, 'positions');
if (lavcPositions.length > 0) {
  console.log('first Lavc at', lavcPositions[0]);
  const snip = buf.slice(Math.max(0, lavcPositions[0] - 4), Math.min(buf.length, lavcPositions[0] + 16));
  console.log('snippet:', snip.toString('ascii').replace(/[^\x20-\x7E]/g, '.'));
}

// 尝试提取所有可能的视频片段
// Simple Cache 中，每个条目开头有 12 字节的 header，然后是 key 和 data
// 但 data_3 是 block 文件，不是直接可读的

// 尝试从 data_3 中提取连续的 mp4 数据
// 搜索连续的 00 00 01 或 00 00 00 01 (H.264 NAL unit)
let nalCount = 0;
let nalStart = -1;
const nal = Buffer.from([0, 0, 0, 1]);
searchPos = 0;
while ((searchPos = buf.indexOf(nal, searchPos)) >= 0 && nalCount < 5) {
  if (nalStart < 0) nalStart = searchPos;
  nalCount++;
  searchPos += 4;
}
console.log('\nNAL units found:', nalCount, 'first at', nalStart);

// 搜索所有可能的视频文件头
const patterns = [
  { name: 'ftypmp4', bytes: Buffer.from('ftypmp4') },
  { name: 'ftypisom', bytes: Buffer.from('ftypisom') },
  { name: 'ftyp3gp', bytes: Buffer.from('ftyp3gp') },
  { name: 'ftypMSNV', bytes: Buffer.from('ftypMSNV') },
  { name: 'Lavc', bytes: Buffer.from('Lavc') },
  { name: 'moov', bytes: Buffer.from('moov') },
  { name: 'mdat', bytes: Buffer.from('mdat') },
  { name: 'moof', bytes: Buffer.from('moof') },
  { name: 'styp', bytes: Buffer.from('styp') }, // fmp4
];

for (const p of patterns) {
  let pos = 0;
  const positions = [];
  while ((pos = buf.indexOf(p.bytes, pos)) >= 0) {
    positions.push(pos);
    pos += 1;
  }
  if (positions.length > 0) {
    console.log(`${p.name}: ${positions.length} occurrences, first at ${positions[0]}, last at ${positions[positions.length-1]}`);
  }
}

// 尝试找 ftyp 附近的完整 mp4 头
// 先看 buf 中是否有大段连续的 mp4 数据
// 简单检查：找一段连续的 ISO 媒体数据
console.log('\n--- 前 100 字节 ---');
console.log(buf.slice(0, 100).toString('ascii').replace(/[^\x20-\x7E]/g, '.'));
console.log('hex:', buf.slice(0, 32).toString('hex'));

// 检查 data_3 的格式
// Chromium Simple Cache block 文件格式：
// 前 16 字节：block 文件头
// 然后每个条目：entry header + key + data
// 看第 16 字节开始的条目
for (let i = 0; i < 10; i++) {
  const offset = i * 16;
  if (offset + 16 > buf.length) break;
  const block = buf.slice(offset, offset + 16);
  const hex = block.toString('hex');
  const ascii = block.toString('ascii').replace(/[^\x20-\x7E]/g, '.');
  console.log(`offset ${offset}: ${hex} | ${ascii}`);
}

// 看最近的缓存文件 f_000338 和 f_000339
// 它们可能是 Simple Cache 的独立文件条目
// 格式：前 4 字节 = 条目大小，然后 4 字节 = 数据大小，然后 key，然后数据
const f338 = fs.readFileSync(path.join(CACHE_DIR, 'f_000338'));
console.log('\nf_000338 size:', f338.length);
console.log('f_000338 hex:', f338.slice(0, 48).toString('hex'));
console.log('f_000338 ascii:', f338.slice(0, 48).toString('ascii').replace(/[^\x20-\x7E]/g, '.'));

const f339 = fs.readFileSync(path.join(CACHE_DIR, 'f_000339'));
console.log('\nf_000339 size:', f339.length);
console.log('f_000339 hex:', f339.slice(0, 48).toString('hex'));
console.log('f_000339 ascii:', f339.slice(0, 48).toString('ascii').replace(/[^\x20-\x7E]/g, '.'));

// 把 f339 保存为 mp4 看看
fs.writeFileSync(path.join(OUTPUT_DIR, 'f_000339.mp4'), f339);
console.log('f_000339 saved as mp4');