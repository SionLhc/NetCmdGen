import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getVendors, type VendorInfo } from '@/api'

export const useVendorStore = defineStore('vendor', () => {
  const vendors = ref<VendorInfo[]>([])
  const loading = ref(false)

  async function loadVendors() {
    if (vendors.value.length > 0) return
    loading.value = true
    try {
      vendors.value = await getVendors()
    } finally {
      loading.value = false
    }
  }

  return { vendors, loading, loadVendors }
})
