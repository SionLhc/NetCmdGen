/**
 * SSE 流式数据通用管理器
 *
 * 用法：
 *   const stream = useSseStream<MyDataType>(url)
 *   stream.onProgress = (data) => { ... }
 *   stream.onComplete = (data) => { ... }
 *   stream.onError = (err) => { ... }
 *   stream.start()   // 开始 SSE 连接
 *   stream.stop()    // 中断连接
 */
import { ref, type Ref } from 'vue'

export interface SseEvent<T = any> {
    type: 'progress' | 'complete' | 'error'
    data: T
    progress?: number
    total?: number
}

export function useSseStream<T = any>(baseUrl: string) {
    const isRunning = ref(false)
    const progress = ref(0)
    const total = ref(0)
    const error = ref('')
    let controller: AbortController | null = null

    /** 进度回调 */
    let onProgress: ((data: T) => void) | null = null
    /** 完成回调 */
    let onComplete: ((data: any) => void) | null = null
    /** 错误回调 */
    let onError: ((err: string) => void) | null = null

    function start() {
        stop()
        isRunning.value = true
        error.value = ''
        controller = new AbortController()

        fetch(baseUrl, { signal: controller.signal })
            .then(async (response) => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`)
                const reader = response.body?.getReader()
                if (!reader) throw new Error('不支持流式读取')

                const decoder = new TextDecoder()
                let buffer = ''

                while (true) {
                    const { done, value } = await reader.read()
                    if (done) break
                    buffer += decoder.decode(value, { stream: true })
                    const lines = buffer.split('\n')
                    buffer = lines.pop() || ''

                    let currentEvent = ''
                    for (const line of lines) {
                        if (line.startsWith('event: ')) {
                            currentEvent = line.slice(7).trim()
                        } else if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6))
                                handleEvent(currentEvent, data)
                            } catch {
                                // 解析失败忽略
                            }
                        }
                    }
                }
            })
            .catch((err) => {
                if (err.name !== 'AbortError') {
                    error.value = String(err)
                    onError?.(String(err))
                }
            })
            .finally(() => {
                isRunning.value = false
            })
    }

    function handleEvent(eventType: string, payload: any) {
        const evt: SseEvent = {
            type: (payload.type as any) || eventType,
            data: payload.data || payload,
            progress: payload.progress,
            total: payload.total,
        }

        if (payload.progress !== undefined) progress.value = payload.progress
        if (payload.total !== undefined) total.value = payload.total

        if (evt.type === 'complete') {
            onComplete?.(payload)
            isRunning.value = false
        } else if (evt.type === 'error') {
            error.value = payload.error || '未知错误'
            onError?.(error.value)
        } else {
            onProgress?.(evt.data as T)
        }
    }

    function stop() {
        controller?.abort()
        controller = null
        isRunning.value = false
    }

    return { isRunning, progress, total, error, start, stop, onProgress, onComplete, onError }
}
