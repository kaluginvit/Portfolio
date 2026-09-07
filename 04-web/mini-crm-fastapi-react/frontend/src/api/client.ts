import axios, { type AxiosInstance } from 'axios'
import { demoGet, demoPost, demoPatch, demoPut, demoDelete } from './demoAdapter'

export const apiBase =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') || 'http://localhost:8000'

const IS_DEMO = import.meta.env.VITE_DEMO_MODE === 'true'

const realApi = axios.create({
  baseURL: apiBase,
  headers: { 'Content-Type': 'application/json' },
})

const mockApi = { get: demoGet, post: demoPost, patch: demoPatch, put: demoPut, delete: demoDelete }

export const api: AxiosInstance = IS_DEMO
  ? (mockApi as unknown as AxiosInstance)
  : realApi

export function apiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err) && err.response?.data) {
    const d = err.response.data as { message?: string; detail?: unknown }
    if (d.message) return d.message
  }
  if (err instanceof Error) return err.message
  return 'Неизвестная ошибка'
}
