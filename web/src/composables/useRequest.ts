/**
 * 通用 API 请求封装 — 自动处理 loading / try-catch / resp.ok / ElMessage
 * 解决项目中 7/10 页面缺少错误处理的问题
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

interface ReqOptions {
    /** ElMessage 成功提示文字，空字符串不提示 */
    successMsg?: string
    /** ElMessage 错误提示前缀 */
    errorMsg?: string
    /** 请求超时 ms，0 不设置 */
    timeout?: number
}

export function useRequest() {
    const loading = ref(false)

    async function request<T = any>(
        input: RequestInfo,
        init?: RequestInit,
        options: ReqOptions = {},
    ): Promise<T | null> {
        const { successMsg = '', errorMsg = '请求失败', timeout = 0 } = options
        const controller = timeout > 0 ? new AbortController() : null
        if (controller) {
            init = { ...init, signal: controller.signal }
            setTimeout(() => controller.abort(), timeout)
        }

        loading.value = true
        try {
            const resp = await fetch(input, init)
            if (!resp.ok) {
                const text = await resp.text().catch(() => '')
                const detail = text.length > 100 ? text.slice(0, 100) + '...' : text
                ElMessage.error(`${errorMsg}: ${resp.status} ${detail}`)
                return null
            }
            const data = await resp.json() as T
            if (successMsg) ElMessage.success(successMsg)
            return data
        } catch (e: any) {
            if (e.name === 'AbortError') {
                ElMessage.error(`${errorMsg}: 请求超时`)
            } else {
                ElMessage.error(`${errorMsg}: ${e.message || '网络异常'}`)
            }
            return null
        } finally {
            loading.value = false
        }
    }

    async function get<T = any>(url: string, options?: ReqOptions): Promise<T | null> {
        return request<T>(url, undefined, options)
    }

    async function post<T = any>(url: string, body?: any, options?: ReqOptions): Promise<T | null> {
        return request<T>(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body ? JSON.stringify(body) : undefined,
        }, options)
    }

    async function del(url: string, options?: ReqOptions): Promise<boolean> {
        const r = await request(url, { method: 'DELETE' }, options)
        return r !== null
    }

    return { loading, request, get, post, del }
}
