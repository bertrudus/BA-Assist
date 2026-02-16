import { create } from "zustand"
import type { AppConfig } from "@/api/types"
import { api } from "@/api/client"

interface ConfigStore {
  config: AppConfig | null
  loading: boolean
  error: string | null
  fetchConfig: () => Promise<void>
}

export const useConfigStore = create<ConfigStore>((set) => ({
  config: null,
  loading: false,
  error: null,
  fetchConfig: async () => {
    set({ loading: true, error: null })
    try {
      const data = await api.getConfig()
      set({ config: data as unknown as AppConfig, loading: false })
    } catch (err) {
      set({ error: (err as Error).message, loading: false })
    }
  },
}))
