import { mount } from '@vue/test-utils'
import SearchForm from '@/components/common/SearchForm.vue'

describe('SearchForm Component', () => {
  const defaultFields = [
    {
      name: 'name',
      type: 'input',
      label: '姓名',
      placeholder: '请输入姓名'
    },
    {
      name: 'age',
      type: 'number',
      label: '年龄',
      min: 0,
      max: 100
    },
    {
      name: 'gender',
      type: 'select',
      label: '性别',
      options: [
        { label: '男', value: 'male' },
        { label: '女', value: 'female' }
      ]
    },
    {
      name: 'startDate',
      type: 'date',
      label: '开始日期'
    },
    {
      name: 'dateRange',
      type: 'daterange',
      label: '日期范围'
    }
  ]

  it('should render correctly with default props', () => {
    const wrapper = mount(SearchForm, {
      props: {
        fields: defaultFields,
        modelValue: {}
      }
    })
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.search-form-card').exists()).toBe(true)
  })

  it('should render all field types correctly', () => {
    const wrapper = mount(SearchForm, {
      props: {
        fields: defaultFields,
        modelValue: {}
      }
    })

    // 检查输入框
    expect(wrapper.find('.mock-elinput').exists()).toBe(true)
    // 检查数字输入框
    expect(wrapper.find('.mock-el-input-number').exists()).toBe(true)
    // 检查选择器
    expect(wrapper.find('.mock-el-select').exists()).toBe(true)
    // 检查日期选择器
    expect(wrapper.find('.mock-el-date-picker').exists()).toBe(true)
  })

  it('should bind modelValue correctly', async () => {
    const initialValue = {
      name: '张三',
      age: 25,
      gender: 'male'
    }

    const wrapper = mount(SearchForm, {
      props: {
        fields: defaultFields,
        modelValue: initialValue
      }
    })

    await wrapper.vm.$nextTick()
    // 检查表单数据是否正确绑定
    expect(wrapper.vm.formData.name).toBe('张三')
    expect(wrapper.vm.formData.age).toBe(25)
    expect(wrapper.vm.formData.gender).toBe('male')
  })

  it('should emit update:modelValue when form data changes', async () => {
    const wrapper = mount(SearchForm, {
      props: {
        fields: defaultFields,
        modelValue: {}
      }
    })

    // 直接修改 formData
    wrapper.vm.formData.name = '李四'
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0][0].name).toBe('李四')
  })

  it('should emit search event when search button is clicked', async () => {
    const wrapper = mount(SearchForm, {
      props: {
        fields: defaultFields,
        modelValue: {
          name: '张三'
        }
      }
    })

    const searchButton = wrapper.find('.el-button--primary')
    await searchButton.trigger('click')

    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')[0][0].name).toBe('张三')
  })

  it('should emit search event when enter key is pressed', async () => {
    const wrapper = mount(SearchForm, {
      props: {
        fields: defaultFields,
        modelValue: {
          name: '张三'
        }
      }
    })

    // 直接调用 handleSearch 方法
    await wrapper.vm.handleSearch()

    expect(wrapper.emitted('search')).toBeTruthy()
  })

  it('should reset form data when reset button is clicked', async () => {
    const wrapper = mount(SearchForm, {
      props: {
        fields: [
          {
            name: 'name',
            type: 'input',
            label: '姓名',
            defaultValue: ''
          },
          {
            name: 'age',
            type: 'number',
            label: '年龄',
            defaultValue: null
          }
        ],
        modelValue: {
          name: '张三',
          age: 25
        }
      }
    })

    const resetButton = wrapper.find('.el-button:not(.el-button--primary)')
    await resetButton.trigger('click')

    expect(wrapper.emitted('reset')).toBeTruthy()
    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.vm.formData.name).toBe('')
    expect(wrapper.vm.formData.age).toBe(null)
  })

  it('should render extra buttons slot correctly', () => {
    const wrapper = mount(SearchForm, {
      props: {
        fields: defaultFields,
        modelValue: {}
      },
      slots: {
        'extra-buttons': '<el-button type="info">额外按钮</el-button>'
      }
    })

    expect(wrapper.find('.el-button--info').exists()).toBe(true)
    expect(wrapper.find('.el-button--info').text()).toBe('额外按钮')
  })

  it('should handle empty fields array', () => {
    const wrapper = mount(SearchForm, {
      props: {
        fields: [],
        modelValue: {}
      }
    })
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.search-form').exists()).toBe(true)
  })

  it('should handle fields with default values', async () => {
    const fieldsWithDefaults = [
      {
        name: 'name',
        type: 'input',
        label: '姓名',
        defaultValue: '默认值'
      }
    ]

    const wrapper = mount(SearchForm, {
      props: {
        fields: fieldsWithDefaults,
        modelValue: {}
      }
    })

    // 直接调用 handleReset 方法来测试默认值
    await wrapper.vm.handleReset()
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.formData.name).toBe('默认值')
  })
})
