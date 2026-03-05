import { mount } from '@vue/test-utils'
import StatusTag from '@/components/common/StatusTag.vue'

describe('StatusTag Component', () => {
  it('should render correctly with required props', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'house',
        status: 'available'
      }
    })
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.status-tag').exists()).toBe(true)
  })

  it('should display correct text and type for house status', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'house',
        status: 'available'
      }
    })
    expect(wrapper.text()).toBe('可租')
    expect(wrapper.find('.el-tag--success').exists()).toBe(true)
  })

  it('should display correct text and type for contract status', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'contract',
        status: 'active'
      }
    })
    expect(wrapper.text()).toBe('履行中')
    expect(wrapper.find('.el-tag--success').exists()).toBe(true)
  })

  it('should display correct text and type for payment status', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'payment',
        status: 'overdue'
      }
    })
    expect(wrapper.text()).toBe('逾期')
    expect(wrapper.find('.el-tag--danger').exists()).toBe(true)
  })

  it('should display correct text and type for user status', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'user',
        status: 'active'
      }
    })
    expect(wrapper.text()).toBe('活跃')
    expect(wrapper.find('.el-tag--success').exists()).toBe(true)
  })

  it('should display correct text and type for landlord status', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'landlord',
        status: 'blacklisted'
      }
    })
    expect(wrapper.text()).toBe('黑名单')
    expect(wrapper.find('.el-tag--danger').exists()).toBe(true)
  })

  it('should display correct text and type for tenant status', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'tenant',
        status: 'expired'
      }
    })
    expect(wrapper.text()).toBe('已退租')
    expect(wrapper.find('.el-tag--info').exists()).toBe(true)
  })

  it('should handle unknown status by displaying status value', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'house',
        status: 'unknown_status'
      }
    })
    expect(wrapper.text()).toBe('unknown_status')
    expect(wrapper.find('.el-tag--info').exists()).toBe(true)
  })

  it('should handle unknown type by displaying status value', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'unknown_type',
        status: 'active'
      }
    })
    expect(wrapper.text()).toBe('active')
    expect(wrapper.find('.el-tag--info').exists()).toBe(true)
  })

  it('should use custom size prop', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'house',
        status: 'available',
        size: 'small'
      }
    })
    expect(wrapper.find('.el-tag--small').exists()).toBe(true)
  })

  it('should use custom effect prop', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'house',
        status: 'available',
        effect: 'dark'
      }
    })
    expect(wrapper.find('.el-tag--dark').exists()).toBe(true)
  })

  it('should apply correct class based on type', () => {
    const wrapper = mount(StatusTag, {
      props: {
        type: 'house',
        status: 'available'
      }
    })
    expect(wrapper.find('.status-tag--house').exists()).toBe(true)
  })

  it('should handle all valid size values', () => {
    const sizes = ['large', 'default', 'small']
    sizes.forEach(size => {
      const wrapper = mount(StatusTag, {
        props: {
          type: 'house',
          status: 'available',
          size: size
        }
      })
      expect(wrapper.exists()).toBe(true)
    })
  })

  it('should handle all valid effect values', () => {
    const effects = ['dark', 'light', 'plain']
    effects.forEach(effect => {
      const wrapper = mount(StatusTag, {
        props: {
          type: 'house',
          status: 'available',
          effect: effect
        }
      })
      expect(wrapper.exists()).toBe(true)
    })
  })
})
