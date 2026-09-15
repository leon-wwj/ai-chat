import axios from 'axios'
import type { AxiosError, AxiosInstance } from 'axios'

const BASE_URL = 'http://localhost:8000'
const TIMEOUT_MS = 10000

export interface ApiErrorBody {
  error?: string
}

const request: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: TIMEOUT_MS
})

request.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    const detail = error.response?.data?.error || error.message
    return Promise.reject(new Error(detail))
  }
)

export default request
