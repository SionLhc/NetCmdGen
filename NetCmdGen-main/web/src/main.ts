import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'

// Monaco Editor Worker 配置（Vite 环境下使用 ?worker 引入）
import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
// @ts-ignore
self.MonacoEnvironment = {
  getWorker() {
    return new EditorWorker()
  },
}

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')
