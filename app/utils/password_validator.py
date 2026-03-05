"""
密码验证工具模块
提供密码强度验证、复杂度评分、密码建议等功能
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PasswordStrengthResult:
    """密码强度检测结果"""
    is_valid: bool  # 是否符合要求
    score: int  # 强度评分（0-100）
    level: str  # 强度等级（weak/medium/strong/very_strong）
    errors: List[str]  # 错误信息列表
    suggestions: List[str]  # 改进建议列表
    checks: Dict[str, bool]  # 各项检查结果


class PasswordValidator:
    """
    密码验证器
    
    功能：
    1. 密码复杂度验证（最小长度、大小写字母、数字、特殊字符）
    2. 密码强度评分（0-100分）
    3. 密码强度等级（weak/medium/strong/very_strong）
    4. 密码改进建议
    """
    
    # 密码强度等级
    STRENGTH_LEVELS = {
        'very_weak': (0, 20),
        'weak': (21, 40),
        'medium': (41, 60),
        'strong': (61, 80),
        'very_strong': (81, 100)
    }
    
    # 常见弱密码列表
    COMMON_PASSWORDS = {
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'monkey', 'master', 'dragon', '111111', 'baseball',
        'iloveyou', 'trustno1', 'sunshine', 'princess', 'admin',
        'welcome', 'shadow', 'ashley', 'football', 'jesus',
        'michael', 'ninja', 'mustang', 'password1', 'password123'
    }
    
    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
        min_unique_chars: int = 4,
        max_repeated_chars: int = 3
    ):
        """
        初始化密码验证器
        
        Args:
            min_length: 最小长度（默认8位）
            require_uppercase: 是否要求大写字母
            require_lowercase: 是否要求小写字母
            require_digit: 是否要求数字
            require_special: 是否要求特殊字符
            min_unique_chars: 最少不同字符数
            max_repeated_chars: 最大连续重复字符数
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.min_unique_chars = min_unique_chars
        self.max_repeated_chars = max_repeated_chars
    
    def validate(self, password: str, username: Optional[str] = None) -> PasswordStrengthResult:
        """
        验证密码强度
        
        Args:
            password: 待验证的密码
            username: 用户名（可选，用于检查密码是否包含用户名）
            
        Returns:
            PasswordStrengthResult: 验证结果
        """
        errors = []
        suggestions = []
        checks = {}
        score = 0
        
        # 1. 检查密码是否为空
        if not password:
            errors.append("密码不能为空")
            return PasswordStrengthResult(
                is_valid=False,
                score=0,
                level='very_weak',
                errors=errors,
                suggestions=["请输入密码"],
                checks=checks
            )
        
        # 2. 检查最小长度
        length = len(password)
        checks['min_length'] = length >= self.min_length
        if not checks['min_length']:
            errors.append(f"密码长度至少为 {self.min_length} 位")
            suggestions.append(f"建议增加密码长度至 {self.min_length} 位以上")
        else:
            # 长度得分（最多25分）
            score += min(25, length * 2)
        
        # 3. 检查大写字母
        has_uppercase = bool(re.search(r'[A-Z]', password))
        checks['has_uppercase'] = has_uppercase
        if self.require_uppercase and not has_uppercase:
            errors.append("密码必须包含大写字母")
            suggestions.append("建议添加大写字母（A-Z）")
        elif has_uppercase:
            score += 15
        
        # 4. 检查小写字母
        has_lowercase = bool(re.search(r'[a-z]', password))
        checks['has_lowercase'] = has_lowercase
        if self.require_lowercase and not has_lowercase:
            errors.append("密码必须包含小写字母")
            suggestions.append("建议添加小写字母（a-z）")
        elif has_lowercase:
            score += 15
        
        # 5. 检查数字
        has_digit = bool(re.search(r'\d', password))
        checks['has_digit'] = has_digit
        if self.require_digit and not has_digit:
            errors.append("密码必须包含数字")
            suggestions.append("建议添加数字（0-9）")
        elif has_digit:
            score += 15
        
        # 6. 检查特殊字符
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password))
        checks['has_special'] = has_special
        if self.require_special and not has_special:
            errors.append("密码必须包含特殊字符")
            suggestions.append("建议添加特殊字符（如：!@#$%^&*）")
        elif has_special:
            score += 15
        
        # 7. 检查字符多样性
        unique_chars = len(set(password))
        checks['unique_chars'] = unique_chars >= self.min_unique_chars
        if not checks['unique_chars']:
            errors.append(f"密码至少需要 {self.min_unique_chars} 个不同的字符")
            suggestions.append("建议使用更多不同的字符")
        else:
            # 多样性得分（最多10分）
            score += min(10, unique_chars)
        
        # 8. 检查连续重复字符
        has_repeated = self._check_repeated_chars(password)
        checks['no_repeated'] = not has_repeated
        if has_repeated:
            errors.append(f"密码不能包含连续 {self.max_repeated_chars} 个以上相同字符")
            suggestions.append("避免连续重复的字符")
        else:
            score += 5
        
        # 9. 检查是否为常见弱密码
        is_common = password.lower() in self.COMMON_PASSWORDS
        checks['not_common'] = not is_common
        if is_common:
            errors.append("密码过于简单，请使用更复杂的密码")
            suggestions.append("避免使用常见密码（如：password、123456）")
            score = max(0, score - 20)
        
        # 10. 检查是否包含用户名
        if username:
            contains_username = username.lower() in password.lower()
            checks['not_contains_username'] = not contains_username
            if contains_username:
                errors.append("密码不能包含用户名")
                suggestions.append("避免在密码中使用用户名")
                score = max(0, score - 15)
        
        # 11. 检查连续字符模式（如：123、abc）
        has_sequential = self._check_sequential_chars(password)
        checks['no_sequential'] = not has_sequential
        if has_sequential:
            suggestions.append("避免使用连续字符（如：123、abc）")
            score = max(0, score - 10)
        
        # 确定密码强度等级
        level = self._get_strength_level(score)
        
        # 判断是否有效
        is_valid = len(errors) == 0
        
        # 如果没有建议，添加正面反馈
        if not suggestions:
            if score >= 80:
                suggestions.append("密码强度很好！")
            elif score >= 60:
                suggestions.append("密码强度良好")
        
        return PasswordStrengthResult(
            is_valid=is_valid,
            score=score,
            level=level,
            errors=errors,
            suggestions=suggestions,
            checks=checks
        )
    
    def _check_repeated_chars(self, password: str) -> bool:
        """检查是否有连续重复字符"""
        for i in range(len(password) - self.max_repeated_chars):
            if len(set(password[i:i + self.max_repeated_chars + 1])) == 1:
                return True
        return False
    
    def _check_sequential_chars(self, password: str) -> bool:
        """检查是否有连续字符模式"""
        # 检查数字序列
        for i in range(len(password) - 2):
            if password[i:i+3].isdigit():
                if ord(password[i+1]) - ord(password[i]) == 1 and \
                   ord(password[i+2]) - ord(password[i+1]) == 1:
                    return True
            
            # 检查字母序列
            if password[i:i+3].isalpha():
                if ord(password[i+1].lower()) - ord(password[i].lower()) == 1 and \
                   ord(password[i+2].lower()) - ord(password[i+1].lower()) == 1:
                    return True
        
        return False
    
    def _get_strength_level(self, score: int) -> str:
        """根据分数获取强度等级"""
        for level, (min_score, max_score) in self.STRENGTH_LEVELS.items():
            if min_score <= score <= max_score:
                return level
        return 'very_weak'
    
    def get_strength_label(self, level: str) -> str:
        """获取强度等级的中文标签"""
        labels = {
            'very_weak': '非常弱',
            'weak': '弱',
            'medium': '中等',
            'strong': '强',
            'very_strong': '非常强'
        }
        return labels.get(level, '未知')
    
    def generate_password_suggestions(self) -> List[str]:
        """生成密码建议"""
        return [
            "使用至少 8 个字符",
            "包含大写字母（A-Z）",
            "包含小写字母（a-z）",
            "包含数字（0-9）",
            "包含特殊字符（如：!@#$%^&*）",
            "避免使用个人信息（如生日、姓名）",
            "避免使用常见单词或连续字符",
            "建议使用密码管理器生成随机密码"
        ]


def validate_password_strength(password: str, username: Optional[str] = None) -> Tuple[bool, str]:
    """
    验证密码强度（简化版接口）
    
    Args:
        password: 待验证的密码
        username: 用户名（可选）
        
    Returns:
        Tuple[bool, str]: (是否有效，错误消息)
    """
    validator = PasswordValidator()
    result = validator.validate(password, username)
    
    if result.is_valid:
        return True, f"密码强度：{validator.get_strength_label(result.level)}（{result.score}分）"
    else:
        return False, "；".join(result.errors)


def get_password_strength_details(password: str, username: Optional[str] = None) -> Dict:
    """
    获取密码强度详细信息
    
    Args:
        password: 待验证的密码
        username: 用户名（可选）
        
    Returns:
        Dict: 密码强度详细信息
    """
    validator = PasswordValidator()
    result = validator.validate(password, username)
    
    return {
        'is_valid': result.is_valid,
        'score': result.score,
        'level': result.level,
        'level_label': validator.get_strength_label(result.level),
        'errors': result.errors,
        'suggestions': result.suggestions,
        'checks': result.checks
    }
