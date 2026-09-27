const fs = require('fs');
const path = require('path');

const CACHE_DIR = 'C:\\Users\\Administrator\\AppData\\Roaming\\Tencent\\xwechat\\radium\\web\\profiles\\multitab_6cb1da877eed1733a5c6084e5af0f138\\Cache\\Cache_Data';
const OUT = path.resolve(__dirname, '..', 'temp_weixin2');
fs.mkdirSync(OUT, { recursive: true });

// 读取 data_3
const data3Path = path.join(CACHE_DIR, 'data_3');
const buf = fs.readFileSync(data3Path);
console.log('data_3:', (buf.length/1024/1024).toFixed(1), 'MB');

// 搜索 styp (fMP4 段头)
const stypStr = 'styp';
const stypResults = [];
let idx = 0;
while (idx < buf.length - 4) {
  idx = buf.indexOf(stypStr, idx);
  if (idx < 0) break;
  const boxSize = buf.readUInt32BE(idx - 4);
  stypResults.push({ pos: idx - 4, size: boxSize });
  idx += 4;
}
console.log('styp:', stypResults.length, 'entries');
stypResults.forEach((s, i) => console.log(`  styp[${i}] pos=${s.pos} size=${s.size}`));

// 搜索 moof
const moofResults = [];
idx = 0;
while (idx < buf.length - 4) {
  idx = buf.indexOf('moof', idx);
  if (idx < 0) break;
  const boxSize = buf.readUInt32BE(idx - 4);
  moofResults.push({ pos: idx - 4, size: boxSize });
  idx += 4;
}
console.log('moof:', moofResults.length, 'entries');

// 搜索 mdat
const mdatResults = [];
idx = 0;
while (idx < buf.length - 4) {
  idx = buf.indexOf('mdat', idx);
  if (idx < 0) break;
  const boxSize = buf.readUInt32BE(idx - 4);
  mdatResults.push({ pos: idx - 4, size: boxSize });
  idx += 4;
}
console.log('mdat:', mdatResults.length, 'entries');

// 搜索 moov (init segment)
const moovResults = [];
idx = 0;
while (idx < buf.length - 4) {
  idx = buf.indexOf('moov', idx);
  if (idx < 0) break;
  const boxSize = buf.readUInt32BE(idx - 4);
  moovResults.push({ pos: idx - 4, size: boxSize });
  console.log(`  moov[${idx}] pos=${idx-4} size=${boxSize}`);
  idx += 4;
}
console.log('moov:', moovResults.length, 'entries');

// 搜索 ftyp (MP4 header)
idx = 0;
const ftypResults = [];
while (idx < buf.length - 4) {
  idx = buf.indexOf('ftyp', idx);
  if (idx < 0) break;
  const boxSize = buf.readUInt32BE(idx - 4);
  ftypResults.push({ pos: idx - 4, size: boxSize });
  console.log(`  ftyp[${idx}] pos=${idx-4} size=${boxSize}`);
  const snip = buf.slice(Math.max(0, idx-8), Math.min(buf.length, idx+32));
  console.log('    ', snip.toString('ascii').replace(/[^\x20-\x7E]/g, '.'));
  idx += 4;
}
console.log('ftyp:', ftypResults.length, 'entries');

// 搜索 'mp4'、'dash'、'iso6' 等品牌
['mp4', 'iso6', 'iso5', 'iso2', 'dash', 'avif', 'MSNV'].forEach(brand => {
  let c = 0;
  let p = 0;
  while ((p = buf.indexOf(brand, p)) >= 0) {
    c++; p += 1;
  }
  if (c > 0) console.log(brand + ':', c, 'occurrences');
});

// 尝试从 styp 位置提取 fMP4 片段
// 每个 fMP4 片段 = styp (box) + 0~N moof + mdat
// 找到连续的一段
if (stypResults.length > 0) {
  console.log('\n--- 提取 fMP4 片段 ---');
  stypResults.forEach((s, i) => {
    const next = i < stypResults.length - 1 ? stypResults[i + 1].pos : buf.length;
    const end = Math.min(s.pos + s.size, next, buf.length);
    const chunk = buf.slice(s.pos, end);
    console.log(`segment_${i}: ${chunk.length} bytes at ${s.pos}`);
    // 保存
    const outPath = path.join(OUT, `mp4_segment_${i}.mp4`);
    fs.writeFileSync(outPath, chunk);
    console.log(`  saved: ${outPath}`);
    
    // 也用 head 看看内容
    const head = chunk.slice(0, 32).toString('ascii').replace(/[^\x20-\x7E]/g, '.');
    console.log('  head:', head);
  });
}

// 如果 styp 结果大小异常（boxSize 太大），可能位置不对
// 试试直接从 data_3 的每个 moof+mdat 对提取
if (moofResults.length > 0 && mdatResults.length > 0) {
  console.log('\n--- 从 moof+mdat 对提取 ---');
  moofResults.forEach((m, i) => {
    const nextMdat = mdatResults.find(d => d.pos > m.pos);
    if (nextMdat && nextMdat.pos < buf.length - 4) {
      const mdatEnd = Math.min(nextMdat.pos + nextMdat.size, buf.length);
      const chunk = buf.slice(m.pos, mdatEnd);
      console.log(`moof+mdat[${i}]: ${chunk.length} bytes`);
    }
  });
}

// 搜索所有 NAL unit 起始码 (00 00 01 或 00 00 00 01) - H.264
let nalCount = 0;
let p = 0;
while (p < buf.length - 4) {
  const val = buf.readUInt32BE(p);
  if (val === 0x00000001 || val === 0x00000000) {
    if (val === 0x00000001 || (p < buf.length - 4 && buf[p+4] === 1)) {
      nalCount++;
      if (nalCount <= 5) console.log('NAL at', p);
    }
  }
  p++;
}
console.log('NAL start codes found:', nalCount, 'in 32MB');

// 看看 moof 附近有什么
if (moofResults.length > 0) {
  const m = moofResults[0];
  const head = buf.slice(Math.max(0, m.pos - 8), Math.min(buf.length, m.pos + 32));
  console.log('\nFirst moof area:', head.toString('ascii').replace(/[^\x20-\x7E]/g, '.'));
  console.log('hex:', head.toString('hex'));
}