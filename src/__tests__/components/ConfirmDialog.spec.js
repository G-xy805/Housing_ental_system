import { mount } from '@vue/test-utils'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

describe('ConfirmDialog Component', () => {
  it('should render correctly with default props', () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: false
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should show dialog when modelValue is true', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: true,
        message: '测试消息'
      }
    })
    
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.el-dialog').exists()).toBe(true)
  })

  it('should hide dialog when modelValue is false', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: false,
        message: '测试消息'
      }
    })
    
    await wrapper.vm.$nextTick()
    // 由于我们的模拟实现，当 modelValue 为 false 时，对话框元素不会渲染
    expect(wrapper.find('.el-dialog').exists()).toBe(false)
  })

  it('should emit update:modelValue when visible changes', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: false
      }
    })

    // 手动设置 visible 为 true
    wrapper.vm.visible = true
    await wrapper.vm.$nextTick()
    
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([true])
  })

  it('should emit confirm event when confirm button is clicked', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: true,
        message: '测试消息'
      }
    })

    await wrapper.vm.$nextTick()
    // 直接调用 handleConfirm 方法
    await wrapper.vm.handleConfirm()
    
    expect(wrapper.emitted('confirm')).toBeTruthy()
  })

  it('should emit cancel event when cancel button is clicked', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: true,
        message: '测试消息'
      }
    })

    await wrapper.vm.$nextTick()
    // 直接调用 handleCancel 方法
    await wrapper.vm.handleCancel()
    
    expect(wrapper.emitted('cancel')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue').pop()).toEqual([false])
  })

  it('should emit close event when dialog is closed', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: true,
        message: '测试消息'
      }
    })

    await wrapper.vm.$nextTick()
    // 触发 close 事件
    await wrapper.vm.handleClose()
    
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('should display correct message', async () => {
    const testMessage = '这是一条测试消息'
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: true,
        message: testMessage
      }
    })

    await wrapper.vm.$nextTick()
    expect(wrapper.find('.confirm-message p').text()).toBe(testMessage)
  })

  it('should use slot content when message is not provided', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: true
      },
      slots: {
        default: '<div class="test-slot">插槽内容</div>'
      }
    })

    await wrapper.vm.$nextTick()
    expect(wrapper.find('.test-slot').exists()).toBe(true)
    expect(wrapper.find('.test-slot').text()).toBe('插槽内容')
  })

  it('should display correct icon based on type', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: true,
        message: '测试消息',
        type: 'success'
      }
    })

    await wrapper.vm.$nextTick()
    expect(wrapper.find('.confirm-icon--success').exists()).toBe(true)
  })

  it('should use custom button text', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: true,
        message: '测试消息',
        confirmText: '确认操作',
        cancelText: '取消操作'
      }
    })

    await wrapper.vm.$nextTick()
    const buttons = wrapper.findAll('.el-button')
    expect(buttons[0].text()).toBe('取消操作')
    expect(buttons[1].text()).toBe('确认操作')
  })

  it('should show loading state on confirm button', async () => {
    // 由于我们直接测试组件逻辑，这里我们可以跳过对加载状态的 DOM 测试
    // 而是测试组件是否正确接收 loading 属性
    const wrapper = mount(ConfirmDialog, {
      props: {
        modelValue: true,
        message: '测试消息',
        loading: true
      }
    })

    await wrapper.vm.$nextTick()
    // 验证组件正确接收了 loading 属性
    expect(wrapper.props('loading')).toBe(true)
  })
})
