import { ref, computed, type Ref } from 'vue'

export interface FilterState {
  searchQuery: Ref<string>
  filters: Ref<Record<string, unknown>>
  sortBy: Ref<string>
  sortOrder: Ref<'asc' | 'desc'>
  currentPage: Ref<number>
  pageSize: Ref<number>
}

export interface UseListOptions<T> {
  initialPageSize?: number
  searchFields?: (keyof T)[]
}

export function useListFilter<T>(
  items: Ref<T[]>,
  options: UseListOptions<T> = {}
) {
  const {
    initialPageSize = 10,
    searchFields = []
  } = options

  const searchQuery = ref('')
  const filters = ref<Record<string, unknown>>({})
  const sortBy = ref('')
  const sortOrder = ref<'asc' | 'desc'>('desc')
  const currentPage = ref(1)
  const pageSize = ref(initialPageSize)

  const filteredItems = computed(() => {
    let result = [...items.value]

    if (searchQuery.value && searchFields.length > 0) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(item => 
        searchFields.some(field => {
          const value = item[field]
          if (typeof value === 'string') {
            return value.toLowerCase().includes(query)
          }
          return false
        })
      )
    }

    Object.entries(filters.value).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        result = result.filter(item => (item as Record<string, unknown>)[key] === value)
      }
    })

    if (sortBy.value) {
      result.sort((a, b) => {
        const aVal = (a as Record<string, unknown>)[sortBy.value]
        const bVal = (b as Record<string, unknown>)[sortBy.value]
        
        let comparison = 0
        if (aVal === null || aVal === undefined) comparison = 1
        else if (bVal === null || bVal === undefined) comparison = -1
        else if (typeof aVal === 'string' && typeof bVal === 'string') {
          comparison = aVal.localeCompare(bVal, 'zh-CN')
        } else if (aVal < bVal) comparison = -1
        else if (aVal > bVal) comparison = 1
        
        return sortOrder.value === 'asc' ? comparison : -comparison
      })
    }

    return result
  })

  const total = computed(() => filteredItems.value.length)

  const paginatedItems = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredItems.value.slice(start, end)
  })

  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  const setSearchQuery = (query: string) => {
    searchQuery.value = query
    currentPage.value = 1
  }

  const setFilter = (key: string, value: unknown) => {
    filters.value[key] = value
    currentPage.value = 1
  }

  const clearFilters = () => {
    filters.value = {}
    searchQuery.value = ''
    currentPage.value = 1
  }

  const setSort = (field: string, order: 'asc' | 'desc' = 'desc') => {
    sortBy.value = field
    sortOrder.value = order
  }

  const handlePageChange = (page: number) => {
    currentPage.value = page
  }

  const handleSizeChange = (size: number) => {
    pageSize.value = size
    currentPage.value = 1
  }

  return {
    searchQuery,
    filters,
    sortBy,
    sortOrder,
    currentPage,
    pageSize,
    filteredItems,
    paginatedItems,
    total,
    totalPages,
    setSearchQuery,
    setFilter,
    clearFilters,
    setSort,
    handlePageChange,
    handleSizeChange
  }
}

export function useSelection<T extends { id: number }>() {
  const selectedIds = ref<number[]>([])
  const selectedItems = ref<T[]>([]) as Ref<T[]>

  const isSelected = (id: number): boolean => {
    return selectedIds.value.includes(id)
  }

  const toggleSelection = (item: T) => {
    const index = selectedIds.value.indexOf(item.id)
    if (index === -1) {
      selectedIds.value.push(item.id)
      selectedItems.value.push(item)
    } else {
      selectedIds.value.splice(index, 1)
      selectedItems.value.splice(index, 1)
    }
  }

  const selectAll = (items: T[]) => {
    selectedIds.value = items.map(item => item.id)
    selectedItems.value = [...items]
  }

  const clearSelection = () => {
    selectedIds.value = []
    selectedItems.value = []
  }

  const selectMultiple = (items: T[]) => {
    items.forEach(item => {
      if (!selectedIds.value.includes(item.id)) {
        selectedIds.value.push(item.id)
        selectedItems.value.push(item)
      }
    })
  }

  return {
    selectedIds,
    selectedItems,
    isSelected,
    toggleSelection,
    selectAll,
    clearSelection,
    selectMultiple
  }
}

export function useDialog<T = void>() {
  const visible = ref(false)
  const loading = ref(false)
  const data = ref<T | null>(null) as Ref<T | null>

  const open = (initialData?: T) => {
    data.value = initialData ?? null
    visible.value = true
  }

  const close = () => {
    visible.value = false
    data.value = null
  }

  const confirm = async (handler: () => Promise<boolean | void>) => {
    loading.value = true
    try {
      const result = await handler()
      if (result !== false) {
        close()
        return true
      }
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    visible,
    loading,
    data,
    open,
    close,
    confirm
  }
}

export function useRefresh(fetchFn: () => Promise<void>) {
  const refreshing = ref(false)
  const lastRefreshTime = ref<Date | null>(null)

  const refresh = async () => {
    refreshing.value = true
    try {
      await fetchFn()
      lastRefreshTime.value = new Date()
    } finally {
      refreshing.value = false
    }
  }

  return {
    refreshing,
    lastRefreshTime,
    refresh
  }
}
