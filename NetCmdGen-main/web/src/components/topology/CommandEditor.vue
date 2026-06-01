<template>
  <div class="command-editor">
    <div class="editor-toolbar">
      <span class="toolbar-tip">
        <el-icon><InfoFilled /></el-icon>
        输入命令名前缀（如 ospf、vlan、acl）按 Ctrl+空格 触发自动补全
      </span>
      <div class="toolbar-actions">
        <el-button size="small" @click="handleClear" :disabled="!modelValue">清空</el-button>
        <el-button size="small" type="primary" @click="handleFormat">格式化</el-button>
      </div>
    </div>

    <div ref="editorRef" class="monaco-container"></div>

    <div v-if="errors.length" class="error-panel">
      <div class="error-title">
        <el-icon color="#f56c6c"><WarningFilled /></el-icon>
        发现 {{ errors.length }} 处可能的问题
      </div>
      <div v-for="(err, i) in errors" :key="i" class="error-item">
        第 {{ err.line }} 行：{{ err.message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as monaco from 'monaco-editor'
import { InfoFilled, WarningFilled } from '@element-plus/icons-vue'
import { registerNetworkLanguage, validateCommands } from './networkLanguage'

const props = defineProps<{
  modelValue: string
  vendor?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const editorRef = ref<HTMLDivElement>()
let editor: monaco.editor.IStandaloneCodeEditor | null = null
const errors = ref<Array<{ line: number; message: string }>>([])

onMounted(() => {
  if (!editorRef.value) return

  // 注册自定义语言
  const langId = registerNetworkLanguage(monaco)

  editor = monaco.editor.create(editorRef.value, {
    value: props.modelValue || '',
    language: langId,
    theme: 'network-cli-theme',
    fontSize: 13,
    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
    lineNumbers: 'on',
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    automaticLayout: true,
    tabSize: 1,
    wordWrap: 'on',
    suggestOnTriggerCharacters: true,
    quickSuggestions: { other: true, comments: false, strings: false },
    renderLineHighlight: 'line',
    padding: { top: 8, bottom: 8 },
  })

  // 内容变化时同步到外部 + 校验
  editor.onDidChangeModelContent(() => {
    const value = editor!.getValue()
    emit('update:modelValue', value)
    validate(value)
  })

  validate(props.modelValue || '')
})

watch(() => props.modelValue, (v) => {
  if (editor && editor.getValue() !== v) {
    editor.setValue(v || '')
  }
})

onBeforeUnmount(() => {
  editor?.dispose()
})

function validate(text: string) {
  errors.value = validateCommands(text)
}

function handleClear() {
  editor?.setValue('')
}

function handleFormat() {
  if (!editor) return
  // 简单格式化：清理多余空行 + 统一缩进（保留命令层级）
  const text = editor.getValue()
  const lines = text.split('\n')
  let indent = 0
  const formatted: string[] = []
  for (const raw of lines) {
    const line = raw.trim()
    if (!line) {
      if (formatted.length && formatted[formatted.length - 1] !== '') {
        formatted.push('')
      }
      continue
    }
    if (line === 'quit' || line === 'exit' || line === 'return') {
      indent = Math.max(0, indent - 1)
      formatted.push(' '.repeat(indent) + line)
    } else if (
      line.startsWith('interface ') ||
      line.startsWith('vlan ') ||
      line.startsWith('ospf ') ||
      line.startsWith('acl ') ||
      line.startsWith('aaa') ||
      line.startsWith('area ')
    ) {
      formatted.push(' '.repeat(indent) + line)
      indent += 1
    } else {
      formatted.push(' '.repeat(indent) + line)
    }
  }
  editor.setValue(formatted.join('\n'))
}
</script>

<style scoped>
.command-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 300px;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: #f0f4f8;
  border: 1px solid #dcdfe6;
  border-bottom: none;
  border-radius: 4px 4px 0 0;
  font-size: 12px;
}

.toolbar-tip {
  color: #606266;
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-actions {
  display: flex;
  gap: 6px;
}

.monaco-container {
  flex: 1;
  min-height: 280px;
  border: 1px solid #dcdfe6;
  border-radius: 0 0 4px 4px;
  overflow: hidden;
}

.error-panel {
  margin-top: 8px;
  padding: 8px 10px;
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 4px;
  font-size: 12px;
}

.error-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
  color: #f56c6c;
  margin-bottom: 4px;
}

.error-item {
  color: #909399;
  padding-left: 20px;
  line-height: 1.6;
}
</style>
