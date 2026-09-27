/**
 * 从微信 Simple Cache 中提取视频数据
 * 微信 Radium 用 Chromium Simple Cache 存储视频
 * 数据在 data_3 (32MB) 中，以 block 格式存储
 * 每个条目：header(12-16字节) + key + data
 * 找到 styp/mdat box 后提取完整 fMP4 片段
 */
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const CACHE_DIR = 'C:\\Users\\Administrator\\AppData\\Roaming\\Tencent\\xwechat\\radium\\web\\profiles\\multitab_6cb1da877eed1733a5c6084e5af0f138\\Cache\\Cache_Data';
const OUTPUT_DIR = path.resolve(__dirname, '..', 'temp_weixin2');
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

const buf = fs.readFileSync(path.join(CACHE_DIR, 'data_3'));
console.log('data_3 size:', (buf.length / 1024 / 1024).toFixed(1), 'MB');

// 搜索所有 styp (segment type) box 位置
// styp 是 fMP4 片段的起始标志
let stypPos = 0;
const segments = [];
while ((stypPos = buf.indexOf('styp', stypPos)) >= 0) {
  // 前 4 字节是 box 大小
  const boxSize = buf.readUInt32BE(stypPos - 4);
  segments.push({ start: stypPos - 4, size: boxSize, pos: stypPos });
  console.log(`styp at ${stypPos - 4}, box size: ${boxSize}`);
  stypPos += 4;
}

// 也搜索 mdat (media data)
let mdatPos = 0;
const mdatSegments = [];
while ((mdatPos = buf.indexOf('mdat', mdatPos)) >= 0) {
  const boxSize = buf.readUInt32BE(mdatPos - 4);
  mdatSegments.push({ start: mdatPos - 4, size: boxSize, pos: mdatPos });
  console.log(`mdat at ${mdatPos - 4}, box size: ${boxSize}`);
  mdatPos += 4;
}

// 搜索 moof (movie fragment)
let moofPos = 0;
const moofSegments = [];
while ((moofPos = buf.indexOf('moof', moofPos)) >= 0) {
  const boxSize = buf.readUInt32BE(moofPos - 4);
  moofSegments.push({ start: moofPos - 4, size: boxSize, pos: moofPos });
  console.log(`moof at ${moofPos - 4}, box size: ${boxSize}`);
  moofPos += 4;
}

// 提取所有可能的 fMP4 片段
// fMP4 格式：styp + moov 或 moof + mdat
// 尝试从第一个 styp 开始提取到最后一个 mdat 结束

if (segments.length > 0) {
  // 从第一个 styp 到文件末尾，或到下一个 styp 之前
  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    const end = i < segments.length - 1 ? segments[i + 1].start : buf.length;
    const chunk = buf.slice(seg.start, Math.min(seg.start + seg.size, end));
    if (chunk.length > 1000) {
      const outPath = path.join(OUTPUT_DIR, `segment_${i}.mp4`);
      fs.writeFileSync(outPath, chunk);
      console.log(`segment_${i}.mp4: ${chunk.length} bytes`);
    }
  }
}

// 如果上面没提取到有效内容，尝试直接从 data_3 中提取所有连续的大段数据
// 跳过 block 文件头（16 字节）
// 每个条目：header(16B) + key(data_3 中 key 可能为空) + value
// 尝试找连续的、非零的、看起来像视频的数据

// 提取所有以 Lavc 开头的片段
const lavcEntries = [];
let searchPos = 0;
while ((searchPos = buf.indexOf('Lavc', searchPos)) >= 0) {
  // 前 4 字节是数据大小
  // 但 Lavc 可能是 H.264 数据的一部分，不是格式 header
  // 简单保存：从 Lavc 前 12 字节开始到下一个明显格式标记或文件末尾
  const start = Math.max(0, searchPos - 12);
  let end = buf.indexOf('Lavc', searchPos + 4);
  if (end < 0) end = buf.length;
  else end = Math.min(end + 12, buf.length);
  
  const chunk = buf.slice(start, end);
  lavcEntries.push({ start, end, size: chunk.length });
  console.log(`Lavc entry at ${start}, size: ${chunk.length}`);
  searchPos += 4;
}

// 看看用 ffmpeg 能不能直接修复
// 先尝试把所有 segment 合并
console.log('\n尝试用 ffmpeg 合并...');
const segmentsList = segments.map((_, i) => path.join(OUTPUT_DIR, `segment_${i}.mp4`));
const concatPath = path.join(OUTPUT_DIR, 'concat_list.txt');
fs.writeFileSync(concatPath, segmentsList.filter(f => fs.existsSync(f) && fs.statSync(f).size > 1000).map(f => `file '${f}'`).join('\n'));

// 也试试直接保存 data_3 为 mp4 看看
fs.writeFileSync(path.join(OUTPUT_DIR, 'data_3.mp4'), buf);
console.log('data_3.mp4 saved (32MB)');

// 用 ffmpeg 检查
console.log('\nffmpeg 检查 data_3.mp4...');
const ffmpeg = spawn('ffmpeg', ['-v', 'error', '-i', path.join(OUTPUT_DIR, 'data_3.mp4'), '-f', 'null', '-'], { shell: false });
let stderr = '';
ffmpeg.stderr.on('data', (d) => { stderr += d.toString(); });
ffmpeg.on('close', (code) => {
  console.log('ffmpeg exit:', code);
  console.log(stderr.substring(0, 500));
});