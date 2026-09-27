# B2 - Behavior 代码复用

**来源**: 官方文档 + 小程序社区
**更新**: 2026-05-23

---

## 一、Behavior 是什么

Behavior 是小程序中**实现代码复用**的核心机制。
类似 Vue 的 mixin，把一组数据、方法、生命周期合并到组件中。

---

## 二、基本用法

### 1. 定义 Behavior
```javascript
// behaviors/myBehavior.js
module.exports = Behavior({
  data: {
    sharedValue: 'hello'
  },
  methods: {
    sharedMethod() {
      console.log('共享方法')
    }
  },
  lifetimes: {
    created() { console.log('Behavior created') }
  }
})
```

### 2. 组件中引用
```javascript
// 组件js文件中
const myBehavior = require('./myBehavior.js')

Component({
  behaviors: [myBehavior],
  data: {
    localValue: 'world'
  },
  methods: {
    localMethod() {
      this.sharedMethod()  // 来自 Behavior
      console.log(this.data.sharedValue)  // 来自 Behavior
    }
  }
})
```

### 3. 多个 Behavior
```javascript
Component({
  behaviors: [behaviorA, behaviorB, behaviorC]
})
```

---

## 三、数据合并规则

| 来源 | 优先级 | 说明 |
|------|--------|------|
| 组件自身 data | 最高 | 冲突时覆盖 Behavior |
| 后引入的 Behavior | 高 | 后面的覆盖前面的 |
| 先引入的 Behavior | 低 | |
| Behavior data | 最低 | |

### 合并示例
```javascript
// Behavior A
Behavior({
  data: { a: 1, b: 2 }
})

// Behavior B
Behavior({
  data: { b: 3, c: 4 }
})

// 组件
Component({
  behaviors: [A, B],
  data: { a: 100, d: 5 }
})

// 最终 data: { a: 100, b: 3, c: 4, d: 5 }
// a: 组件覆盖 A
// b: B 覆盖 A
// c: 来自 B
// d: 组件独有
```

---

## 四、方法合并规则

### 同名方法：优先执行 Behavior，后执行组件方法
```javascript
// Behavior
Behavior({
  methods: {
    onTap() {
      console.log('Behavior onTap')
    }
  }
})

// 组件
Component({
  behaviors: [myBehavior],
  methods: {
    onTap() {
      console.log('组件 onTap')
    }
  }
})

// 实际执行顺序：Behavior → 组件
// 输出：Behavior onTap
//       组件 onTap
```

### 调用父级（类似 super）
```javascript
// 组件中调用 Behavior 方法：无直接方式
// 需要通过抛出事件或定义接口
```

---

## 五、生命周期合并

### 冲突时：先执行 Behavior，后执行组件
```javascript
// Behavior
Behavior({
  lifetimes: {
    created() { console.log('1-Behavior created') },
    attached() { console.log('2-Behavior attached') }
  }
})

// 组件
Component({
  behaviors: [myBehavior],
  lifetimes: {
    created() { console.log('3-组件 created') },
    attached() { console.log('4-组件 attached') }
  }
})

// 输出顺序：
// 1-Behavior created
// 3-组件 created
// 2-Behavior attached
// 4-组件 attached
```

---

## 六、真实场景：错题本 OCR 能力抽离

### 抽离为一个 Behavior
```javascript
// behaviors/ocrBehavior.js
module.exports = Behavior({
  data: {
    ocrLoading: false,
    ocrText: '',
    currentFileID: ''
  },
  methods: {
    uploadForOCR(filePath) {
      // 上传云存储
      const cloudPath = 'ocr/' + Date.now() + '.jpg'
      return wx.cloud.uploadFile({ cloudPath, filePath }).then(res => {
        this.setData({ currentFileID: res.fileID })
        return res.fileID
      })
    },
    doOCR(fileID) {
      return wx.cloud.callFunction({
        name: 'ocr',
        data: { fileID }
      }).then(res => {
        if (res.result && res.result.success) {
          this.setData({ ocrText: res.result.text })
        }
        return res.result
      })
    }
  }
})
```

### 组件中使用
```javascript
const ocrBehavior = require('./behaviors/ocrBehavior.js')

Component({
  behaviors: [ocrBehavior],
  methods: {
    onConfirm() {
      this.uploadForOCR(this.data.imagePath)
        .then(fileID => this.doOCR(fileID))
        .then(result => {
          console.log('OCR结果', result.text)
        })
    }
  }
})
```

---

## 七、Behavior vs mixin 对比

| 特性 | Behavior | mixin（其他框架） |
|------|----------|-------------------|
| 生命周期合并 | ✅ | ✅ |
| 数据合并 | ✅ | ✅ |
| 方法合并 | ✅ | ✅ |
| 冲突覆盖规则 | ✅ 明确 | ⚠️ 各不同 |
| 支持纯对象 | ✅ | ✅ |
| 社区广泛度 | ⚠️ 仅微信小程序 | ✅ |

---

## 八、注意事项

1. **Behavior 名要全局唯一**：避免重名覆盖
2. **避免深度合并嵌套 Behavior**：复杂难维护
3. **Behavior 中的 `this` 指向组件实例**：可以直接 setData
4. **Behavior 不能独立存在**：必须被组件引用

---

_由 可悦🌸 2026-05-23_