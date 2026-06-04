/**
 * SSE 流式数据通用管理器
 *
 * 用法：
 *   const stream = useSseStream<MyDataType>(urlOrRef)
 *   stream.onProgress = (data) => { ... }
 *   stream.start()   // 开始 SSE 连接
 *   stream.stop()    // 中断连接
 */
import { ref, isRef, type Ref } from 'vue'

export function useSseStream<T = any>(baseUrl: string | Ref<string>) {
    const isRunning = ref(false)
    const progress = ref(0)
    const total = ref(0)
    const error = ref('')
    let controller: AbortController | null = null

    let onProgress: ((data: T) => void) | null = null
    let onComplete: ((data: any) => void) | null = null
    let onError: ((err: string) => void) | null = null

    function getUrl(): string {
        return isRef(baseUrl) ? baseUrl.value : (baseUrl as string)
    }

    function start() {
        stop()
        isRunning.value = true
        error.value = ''
        controller = new AbortController()
        const url = getUrl()
        if (!url) { error.value = 'URL 为空'; isRunning.value = false; return }

        fetch(url, { signal: controller.signal })
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
                    const events = buffer.split('\n\n')
                    buffer = events.pop() || ''
                    for (const chunk of events) {
                        if (!chunk.trim()) continue
                        let evType = ''
                        for (const line of chunk.split('\n')) {
                            if (line.startsWith('event: ')) evType = line.slice(7).trim()
                            else if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6))
                                    if (data.progress !== undefined) progress.value = data.progress
                                    if (data.total !== undefined) total.value = data.total
                                    if (evType === 'complete' || data.type === 'complete') {
                                        onComplete?.(data); isRunning.value = false
                                    } else if (evType === 'error' || data.type === 'error') {
                                        error.value = data.error || '未知错误'; onError?.(error.value)
                                    } else {
                                        onProgress?.(data.data || data)
                                    }
                                } catch {}
                            }
                        }
                    }
                }
            })
            .catch((err) => {
                if (err.name !== 'AbortError') { error.value = String(err); onError?.(String(err)) }
            })
            .finally(() => { isRunning.value = false })
    }

    function stop() { controller?.abort(); controller = null; isRunning.value = false }

    return { isRunning, progress, total, error, start, stop,
        get onProgress() { return onProgress },
        set onProgress(fn) { onProgress = fn },
        get onComplete() { return onComplete },
        set onComplete(fn) { onComplete = fn },
        get onError() { return onError },
        set onError(fn) { onError = fn },
    }
}
