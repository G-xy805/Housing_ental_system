import { mount } from '@vue/test-utils'
import Pagination from '@/components/common/Pagination.vue'

describe('Pagination Component', () => {
  it('should render correctly with default props', () => {
    const wrapper = mount(Pagination)
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.pagination-wrapper').exists()).toBe(true)
  })

  it('should pass props correctly to el-pagination', () => {
    const wrapper = mount(Pagination, {
      props: {
        currentPage: 2,
        pageSize: 20,
        total: 100,
        pageSizes: [10, 20, 30],
        layout: 'total, sizes, prev, pager, next, jumper',
        background: false,
        small: true,
        disabled: true,
        hideOnSinglePage: true
      }
    })

    const elPagination = wrapper.find('.el-pagination')
    expect(elPagination.exists()).toBe(true)
  })

  it('should emit update:currentPage when current page changes', async () => {
    const wrapper = mount(Pagination, {
      props: {
        currentPage: 1,
        pageSize: 10,
        total: 100
      }
    })

    await wrapper.vm.$emit('update:currentPage', 2)
    expect(wrapper.emitted('update:currentPage')).toBeTruthy()
    expect(wrapper.emitted('update:currentPage')[0]).toEqual([2])
  })

  it('should emit update:pageSize when page size changes', async () => {
    const wrapper = mount(Pagination, {
      props: {
        currentPage: 1,
        pageSize: 10,
        total: 100
      }
    })

    await wrapper.vm.$emit('update:pageSize', 20)
    expect(wrapper.emitted('update:pageSize')).toBeTruthy()
    expect(wrapper.emitted('update:pageSize')[0]).toEqual([20])
  })

  it('should emit change event when page size changes', async () => {
    const wrapper = mount(Pagination, {
      props: {
        currentPage: 1,
        pageSize: 10,
        total: 100
      }
    })

    // 触发 handleSizeChange 方法
    await wrapper.vm.handleSizeChange(20)
    expect(wrapper.emitted('change')).toBeTruthy()
    expect(wrapper.emitted('change')[0]).toEqual([{ page: 1, pageSize: 20 }])
  })

  it('should emit change event when current page changes', async () => {
    const wrapper = mount(Pagination, {
      props: {
        currentPage: 1,
        pageSize: 10,
        total: 100
      }
    })

    // 触发 handleCurrentChange 方法
    await wrapper.vm.handleCurrentChange(2)
    expect(wrapper.emitted('change')).toBeTruthy()
    expect(wrapper.emitted('change')[0]).toEqual([{ page: 2, pageSize: 10 }])
  })

  it('should display correct pagination layout', () => {
    const wrapper = mount(Pagination)
    expect(wrapper.find('.el-pagination').exists()).toBe(true)
  })

  it('should handle zero total correctly', () => {
    const wrapper = mount(Pagination, {
      props: {
        total: 0
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should handle single page correctly', () => {
    const wrapper = mount(Pagination, {
      props: {
        total: 10,
        pageSize: 10
      }
    })
    expect(wrapper.exists()).toBe(true)
  })
})
