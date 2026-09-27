# API速查.md - 高频API快速参考

**创建时间**: 2026-05-23
**版本**: V1.0
**来源**: 错题本实战经验

---

## 一、云存储 API

### 1. 上传文件（最常用）
```javascript
wx.cloud.uploadFile({
  cloudPath: 'ocr/' + Date.now() + '.jpg',  // 云端路径（不要传临时路径）
  filePath: tempFilePath,                    // 本地临时路径
  success: res => {
    console.log(res.fileID)  // 云存储文件ID，后续靠它访问
  },
  fail: err => console.error(err)
})

// 返回格式
{ fileID: "cloud://xxx/ocr/123.jpg" }
```

### 2. 获取临时链接
```javascript
wx.cloud.getTempFileURL({
  fileList: [fileID1, fileID2],
  success: res => {
    res.fileList.forEach(item => {
      console.log(item.tempFileURL)  // 临时HTTPS链接
    })
  }
})
```

### 3. 删除文件
```javascript
wx.cloud.deleteFile({
  fileList: [fileID],
  success: res => {
    console.log(res.fileList[0].status)  // 0=成功
  }
})
```

---

## 二、云函数 API

### 1. 调用云函数（最常用）
```javascript
wx.cloud.callFunction({
  name: 'ocr',                    // 云函数名
  data: { fileID: 'cloud://...' }, // 参数（不要传大对象/坐标）
  timeout: 30000,                  // 超时ms（可选）
  success: res => {
    const result = res.result     // 云函数返回
    if (result.success) {
      console.log(result.text)
    } else {
      console.error(result.errMsg)
    }
  },
  fail: err => {
    console.error(err)
  }
})
```

### 2. 云函数内调用其他云函数
```javascript
const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

exports.main = async function(event, context) {
  const result = await cloud.callFunction({
    name: 'getKnowledge',
    data: { question: event.question }
  })
  return result.result
}
```

### 3. 云数据库基础操作
```javascript
const db = cloud.database()

// 查
db.collection('wrongbooks')
  .where({ grade: 3 })
  .field({ question: true, answer: true })
  .limit(20)
  .get()

// 增
db.collection('wrongbooks').add({
  data: { question: 'xxx', answer: 'yyy' }
})

// 改
db.collection('wrongbooks').doc(id).update({
  data: { answer: 'new answer' }
})

// 删
db.collection('wrongbooks').doc(id).remove()
```

---

## 三、图片处理 API

### 1. 选择图片
```javascript
wx.chooseImage({
  count: 1,
  sourceType: ['camera', 'album'],  // 默认 ['album', 'camera']
  success: res => {
    const path = res.tempFilePaths[0]  // 本地临时路径
  }
})
```

### 2. 裁剪图片（Canvas方案）
```javascript
// 1. 获取Canvas实例（必须 in(this)）
const query = wx.createSelectorQuery().in(this)
query.select('#cropCanvas').node(res => {
  const canvas = res.node
  const ctx = canvas.getContext('2d')
  canvas.width = cropW
  canvas.height = cropH
  
  const img = canvas.createImage()
  img.onload = () => {
    ctx.drawImage(img, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH)
    wx.canvasToTempFilePath({
      canvas: res.node,        // 传对象不传id
      x: 0, y: 0,
      width: cropW, height: cropH,
      destWidth: cropW, destHeight: cropH,
      fileType: 'jpg', quality: 0.9,
      success: r => resolve(r.tempFilePath)
    })
  }
  img.src = imagePath
}).exec()

// 2. 导出裁剪结果
wx.canvasToTempFilePath({
  canvas: canvasInstance,  // ✅ 对象
  // canvas: 'cropCanvas', // ❌ 字符串id会报错
  x: 0, y: 0, width: 300, height: 200,
  destWidth: 300, destHeight: 200,
  fileType: 'jpg', quality: 0.9,
  success: res => console.log(res.tempFilePath)
})
```

---

## 四、界面/交互 API

### 1. 显示加载/提示
```javascript
wx.showLoading({ title: '加载中...', mask: true })
wx.hideLoading()

wx.showToast({ title: '成功', icon: 'success' })
wx.showToast({ title: '失败', icon: 'none' })  // icon:none 不弹图标
wx.showModal({
  title: '确认',
  content: '是否删除',
  success: res => {
    if (res.confirm) console.log('确认')
  }
})
```

### 2. 页面跳转
```javascript
// 跳转TabBar页面（必须用 switchTab）
wx.switchTab({ url: '/pages/index/index' })

// 跳转普通页面
wx.navigateTo({ url: '/pages/detail/detail?id=123' })

// 页面间传参获取
onLoad(options) {
  const id = options.id
}

// 关闭当前页，跳转新页
wx.redirectTo({ url: '/pages/add/add' })

// 跳转并清空页面栈
wx.reLaunch({ url: '/pages/index/index' })

// 获取当前页面栈
const pages = getCurrentPages()
const currentPage = pages[pages.length - 1]
```

### 3. 元素查询（组件内必须 in(this)）
```javascript
// ✅ 组件内正确用法
const query = wx.createSelectorQuery().in(this)
query.select('.my-element').boundingClientRect()
query.select('#myCanvas').node()
query.exec(res => console.log(res))

// ❌ 组件内错误用法（查不到）
wx.createSelectorQuery().select('#myCanvas').node(...)
```

---

## 五、Canvas 2D API

### 1. 创建离屏Canvas
```javascript
// 方式1：通过 wxml 节点获取
<canvas type="2d" id="myCanvas" />

const query = wx.createSelectorQuery().in(this)
query.select('#myCanvas').node(res => {
  const canvas = res.node       // Canvas 实例
  const ctx = canvas.getContext('2d')
}).exec()

// 方式2：createOffscreenCanvas（2024新增）
const offscreen = wx.createOffscreenCanvas({
  type: '2d',
  width: 300,
  height: 200
})
const ctx = offscreen.getContext('2d')
```

### 2. 绘制图片
```javascript
const img = canvas.createImage()
img.onload = () => {
  ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh)
  // sx/sy: 源图起点
  // sw/sh: 源图裁剪宽高
  // dx/dy: 目标画布位置
  // dw/dh: 目标宽高
}
img.src = 'https://...'  // 仅支持本地路径或云存储URL
```

### 3. 绘制文字
```javascript
ctx.font = '16px sans-serif'
ctx.fillStyle = '#333333'
ctx.fillText('错题内容', x, y)
ctx.strokeStyle = '#FF6B35'
ctx.strokeText('答案', x, y + 20)
```

---

## 六、获取设备信息
```javascript
// ✅ 兼容写法
let screenW = 375
try {
  const d = wx.getDeviceInfo()
  screenW = d.windowWidth || d.screenWidth || 375
} catch(e) {
  const sys = wx.getSystemInfoSync()
  screenW = sys.windowWidth
}

// 设备像素比（用于高清渲染）
const dpr = wx.getSystemInfoSync().pixelRatio
```

---

## 七、定时器与延迟
```javascript
// setData 延迟执行
this.setData({ value: 'new' }, () => {
  console.log('setData完成')
})

// wx.nextTick 等同于 this.tick
wx.nextTick(() => {
  console.log('下一帧')
})

// 定时器（页面卸载要清理）
onLoad() {
  this.data.timer = setInterval(() => {...}, 3000)
},
onUnload() {
  clearInterval(this.data.timer)
}
```

---

## 八、OCR 常用流程（错题本实战）
```
1. wx.chooseImage()        → 获取本地临时路径
2. wx.cloud.uploadFile()    → 上传到云存储，拿到 fileID
3. wx.cloud.callFunction() → fileID 发给云函数
4. 云函数 OCR              → 识别返回文字
5. 前端展示结果            → setData 渲染
```

---

_由 可悦🌸 2026-05-23_