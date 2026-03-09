"""
JSON 字段验证工具模块
提供 JSON 字段的结构验证功能
"""
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, field


# ============================================================================
# 验证规则定义
# ============================================================================

@dataclass
class FieldRule:
    """
    字段验证规则
    
    Attributes:
        name: 字段名称
        field_type: 字段类型 (bool, str, int, float, dict, list)
        required: 是否必需
        default: 默认值
        min_value: 最小值（用于数值类型）
        max_value: 最大值（用于数值类型）
        min_length: 最小长度（用于字符串、列表）
        max_length: 最大长度（用于字符串、列表）
        allowed_values: 允许的值列表
        pattern: 正则表达式模式（用于字符串）
        description: 字段描述
        nested_rules: 嵌套字段的验证规则（用于 dict 类型）
        item_rule: 列表项的验证规则（用于 list 类型）
    """
    name: str
    field_type: type
    required: bool = False
    default: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    description: str = ""
    nested_rules: Optional[List['FieldRule']] = None
    item_rule: Optional['FieldRule'] = None


@dataclass
class ValidationResult:
    """
    验证结果
    
    Attributes:
        is_valid: 是否验证通过
        errors: 错误信息列表
        warnings: 警告信息列表
        data: 验证后的数据（包含默认值填充）
    """
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: str) -> None:
        """添加错误信息"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """添加警告信息"""
        self.warnings.append(warning)
    
    def merge(self, other: 'ValidationResult', prefix: str = "") -> None:
        """
        合并另一个验证结果
        
        Args:
            other: 要合并的验证结果
            prefix: 错误信息前缀
        """
        if not other.is_valid:
            self.is_valid = False
        
        for error in other.errors:
            self.errors.append(f"{prefix}{error}" if prefix else error)
        
        for warning in other.warnings:
            self.warnings.append(f"{prefix}{warning}" if prefix else warning)


# ============================================================================
# 房源配套设施验证规则
# ============================================================================

# 房源设施基础配置定义
FACILITIES_CONFIG = {
    # 基础设施
    'wifi': {'type': bool, 'description': '无线网络', 'default': False},
    'ac': {'type': bool, 'description': '空调', 'default': False},
    'heater': {'type': bool, 'description': '热水器', 'default': False},
    'washing_machine': {'type': bool, 'description': '洗衣机', 'default': False},
    'refrigerator': {'type': bool, 'description': '冰箱', 'default': False},
    'tv': {'type': bool, 'description': '电视', 'default': False},
    'microwave': {'type': bool, 'description': '微波炉', 'default': False},
    'induction_cooker': {'type': bool, 'description': '电磁炉', 'default': False},
    'range_hood': {'type': bool, 'description': '抽油烟机', 'default': False},
    
    # 家具
    'bed': {'type': bool, 'description': '床', 'default': False},
    'wardrobe': {'type': bool, 'description': '衣柜', 'default': False},
    'desk': {'type': bool, 'description': '书桌', 'default': False},
    'chair': {'type': bool, 'description': '椅子', 'default': False},
    'sofa': {'type': bool, 'description': '沙发', 'default': False},
    'dining_table': {'type': bool, 'description': '餐桌', 'default': False},
    'bookshelf': {'type': bool, 'description': '书架', 'default': False},
    'shoe_cabinet': {'type': bool, 'description': '鞋柜', 'default': False},
    
    # 卫浴设施
    'water_heater': {'type': bool, 'description': '电热水器', 'default': False},
    'gas_water_heater': {'type': bool, 'description': '燃气热水器', 'default': False},
    'bathtub': {'type': bool, 'description': '浴缸', 'default': False},
    'shower': {'type': bool, 'description': '淋浴', 'default': False},
    'toilet': {'type': bool, 'description': '马桶', 'default': False},
    'washbasin': {'type': bool, 'description': '洗手台', 'default': False},
    
    # 安全设施
    'smart_lock': {'type': bool, 'description': '智能门锁', 'default': False},
    'security_door': {'type': bool, 'description': '防盗门', 'default': False},
    'surveillance': {'type': bool, 'description': '监控', 'default': False},
    'fire_extinguisher': {'type': bool, 'description': '灭火器', 'default': False},
    'smoke_detector': {'type': bool, 'description': '烟雾报警器', 'default': False},
    
    # 其他设施
    'balcony': {'type': bool, 'description': '阳台', 'default': False},
    'parking': {'type': bool, 'description': '停车位', 'default': False},
    'elevator': {'type': bool, 'description': '电梯', 'default': False},
    'garden': {'type': bool, 'description': '花园', 'default': False},
    'terrace': {'type': bool, 'description': '露台', 'default': False},
    'basement': {'type': bool, 'description': '地下室', 'default': False},
    'storage': {'type': bool, 'description': '储物间', 'default': False},
}

# 允许的设施字段列表
ALLOWED_FACILITY_KEYS = set(FACILITIES_CONFIG.keys())


# ============================================================================
# 验证函数
# ============================================================================

def validate_field(value: Any, rule: FieldRule, path: str = "") -> ValidationResult:
    """
    验证单个字段
    
    Args:
        value: 字段值
        rule: 验证规则
        path: 字段路径（用于错误信息）
        
    Returns:
        ValidationResult: 验证结果
    """
    result = ValidationResult()
    field_path = f"{path}.{rule.name}" if path else rule.name
    
    # 检查必需字段
    if value is None:
        if rule.required:
            result.add_error(f"字段 '{field_path}' 是必需的")
        else:
            result.data[rule.name] = rule.default
        return result
    
    # 类型检查
    if not isinstance(value, rule.field_type):
        # 特殊处理：允许 int 作为 float 类型
        if rule.field_type == float and isinstance(value, int):
            value = float(value)
        else:
            result.add_error(
                f"字段 '{field_path}' 类型错误，期望 {rule.field_type.__name__}，"
                f"实际 {type(value).__name__}"
            )
            return result
    
    # 数值范围检查
    if rule.field_type in (int, float) and isinstance(value, (int, float)):
        if rule.min_value is not None and value < rule.min_value:
            result.add_error(
                f"字段 '{field_path}' 值 {value} 小于最小值 {rule.min_value}"
            )
        if rule.max_value is not None and value > rule.max_value:
            result.add_error(
                f"字段 '{field_path}' 值 {value} 大于最大值 {rule.max_value}"
            )
    
    # 长度检查
    if rule.field_type in (str, list) and isinstance(value, (str, list)):
        length = len(value)
        if rule.min_length is not None and length < rule.min_length:
            result.add_error(
                f"字段 '{field_path}' 长度 {length} 小于最小长度 {rule.min_length}"
            )
        if rule.max_length is not None and length > rule.max_length:
            result.add_error(
                f"字段 '{field_path}' 长度 {length} 大于最大长度 {rule.max_length}"
            )
    
    # 允许值检查
    if rule.allowed_values is not None and value not in rule.allowed_values:
        result.add_error(
            f"字段 '{field_path}' 值 '{value}' 不在允许的值列表中: {rule.allowed_values}"
        )
    
    # 正则表达式检查
    if rule.pattern and rule.field_type == str and isinstance(value, str):
        import re
        if not re.match(rule.pattern, value):
            result.add_error(
                f"字段 '{field_path}' 值 '{value}' 不匹配模式 '{rule.pattern}'"
            )
    
    # 嵌套结构验证（字典类型）
    if rule.field_type == dict and rule.nested_rules and isinstance(value, dict):
        nested_result = validate_dict(value, rule.nested_rules, field_path)
        result.merge(nested_result)
        result.data[rule.name] = nested_result.data
    # 列表项验证
    elif rule.field_type == list and rule.item_rule and isinstance(value, list):
        validated_items = []
        for i, item in enumerate(value):
            item_path = f"{field_path}[{i}]"
            item_result = validate_field(item, rule.item_rule, item_path)
            result.merge(item_result)
            if item_result.is_valid:
                validated_items.append(item_result.data.get(rule.item_rule.name, item))
        result.data[rule.name] = validated_items
    else:
        result.data[rule.name] = value
    
    return result


def validate_dict(
    data: Dict[str, Any], 
    rules: List[FieldRule], 
    path: str = ""
) -> ValidationResult:
    """
    验证字典数据
    
    Args:
        data: 要验证的字典数据
        rules: 验证规则列表
        path: 当前路径
        
    Returns:
        ValidationResult: 验证结果
    """
    result = ValidationResult()
    validated_data = {}
    
    # 获取规则定义的字段名集合
    rule_fields = {rule.name for rule in rules}
    
    # 验证每个规则字段
    for rule in rules:
        value = data.get(rule.name)
        field_result = validate_field(value, rule, path)
        result.merge(field_result)
        if rule.name in field_result.data:
            validated_data[rule.name] = field_result.data[rule.name]
    
    # 检查未知字段
    unknown_fields = set(data.keys()) - rule_fields
    if unknown_fields:
        for field_name in unknown_fields:
            result.add_warning(
                f"发现未知字段 '{path}.{field_name}'" if path else f"发现未知字段 '{field_name}'"
            )
            # 保留未知字段
            validated_data[field_name] = data[field_name]
    
    result.data = validated_data
    return result


def validate_facilities(
    facilities: Any,
    strict: bool = False
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    验证房源配套设施
    
    Args:
        facilities: 配套设施数据
        strict: 是否严格模式（严格模式下未知字段会报错）
        
    Returns:
        Tuple[bool, List[str], Dict]: (是否验证通过, 错误信息列表, 验证后的数据)
    """
    errors = []
    warnings = []
    validated_data = {}
    
    # 空值检查
    if facilities is None:
        return True, [], {}
    
    # 类型检查
    if not isinstance(facilities, dict):
        return False, ["配套设施必须是对象类型"], {}
    
    # 验证每个设施字段
    for key, value in facilities.items():
        # 检查是否为允许的设施字段
        if key not in ALLOWED_FACILITY_KEYS:
            if strict:
                errors.append(f"未知的设施字段: '{key}'")
            else:
                warnings.append(f"未知的设施字段: '{key}'，将保留该字段")
                validated_data[key] = value
            continue
        
        # 获取字段配置
        config = FACILITIES_CONFIG[key]
        expected_type = config['type']
        
        # 类型验证
        if not isinstance(value, expected_type):
            errors.append(
                f"设施 '{key}' 类型错误，期望 {expected_type.__name__}，"
                f"实际 {type(value).__name__}"
            )
            continue
        
        validated_data[key] = value
    
    # 如果没有错误，填充默认值
    if not errors:
        for key, config in FACILITIES_CONFIG.items():
            if key not in validated_data:
                validated_data[key] = config['default']
    
    return len(errors) == 0, errors, validated_data


def validate_facilities_detailed(
    facilities: Any,
    strict: bool = False
) -> ValidationResult:
    """
    详细验证房源配套设施（返回完整验证结果）
    
    Args:
        facilities: 配套设施数据
        strict: 是否严格模式
        
    Returns:
        ValidationResult: 完整验证结果
    """
    result = ValidationResult()
    
    # 空值检查
    if facilities is None:
        result.data = {}
        return result
    
    # 类型检查
    if not isinstance(facilities, dict):
        result.add_error("配套设施必须是对象类型")
        return result
    
    # 验证每个设施字段
    for key, value in facilities.items():
        # 检查是否为允许的设施字段
        if key not in ALLOWED_FACILITY_KEYS:
            if strict:
                result.add_error(f"未知的设施字段: '{key}'")
            else:
                result.add_warning(f"未知的设施字段: '{key}'，将保留该字段")
                result.data[key] = value
            continue
        
        # 获取字段配置
        config = FACILITIES_CONFIG[key]
        expected_type = config['type']
        
        # 类型验证
        if not isinstance(value, expected_type):
            result.add_error(
                f"设施 '{key}' 类型错误，期望 {expected_type.__name__}，"
                f"实际 {type(value).__name__}"
            )
            continue
        
        result.data[key] = value
    
    # 如果没有错误，填充默认值
    if result.is_valid:
        for key, config in FACILITIES_CONFIG.items():
            if key not in result.data:
                result.data[key] = config['default']
    
    return result


# ============================================================================
# 通用 JSON 字段验证器
# ============================================================================

class JSONFieldValidator:
    """
    JSON 字段验证器
    
    提供灵活的 JSON 字段验证功能，支持自定义规则
    """
    
    def __init__(self, rules: List[FieldRule] = None, strict: bool = False):
        """
        初始化验证器
        
        Args:
            rules: 验证规则列表
            strict: 是否严格模式
        """
        self.rules = rules or []
        self.strict = strict
    
    def validate(self, data: Any) -> ValidationResult:
        """
        验证数据
        
        Args:
            data: 要验证的数据
            
        Returns:
            ValidationResult: 验证结果
        """
        if data is None:
            return ValidationResult(data={})
        
        if not isinstance(data, dict):
            result = ValidationResult()
            result.add_error("数据必须是对象类型")
            return result
        
        return validate_dict(data, self.rules)
    
    def add_rule(self, rule: FieldRule) -> None:
        """添加验证规则"""
        self.rules.append(rule)
    
    def set_strict(self, strict: bool) -> None:
        """设置严格模式"""
        self.strict = strict


# ============================================================================
# 辅助函数
# ============================================================================

def get_facility_description(key: str) -> Optional[str]:
    """
    获取设施字段的描述
    
    Args:
        key: 设施字段名
        
    Returns:
        str: 设施描述，如果不存在返回 None
    """
    config = FACILITIES_CONFIG.get(key)
    return config['description'] if config else None


def get_all_facilities() -> Dict[str, Dict]:
    """
    获取所有设施配置
    
    Returns:
        Dict: 设施配置字典
    """
    return FACILITIES_CONFIG.copy()


def get_default_facilities() -> Dict[str, bool]:
    """
    获取默认设施配置
    
    Returns:
        Dict: 默认设施配置
    """
    return {key: config['default'] for key, config in FACILITIES_CONFIG.items()}


def sanitize_facilities(facilities: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理和规范化设施数据
    
    Args:
        facilities: 原始设施数据
        
    Returns:
        Dict: 清理后的设施数据
    """
    if not facilities or not isinstance(facilities, dict):
        return get_default_facilities()
    
    sanitized = {}
    for key, config in FACILITIES_CONFIG.items():
        value = facilities.get(key)
        if isinstance(value, config['type']):
            sanitized[key] = value
        else:
            sanitized[key] = config['default']
    
    return sanitized
