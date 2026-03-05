"""
统一异常处理模块
提供标准化的异常类型和错误处理机制
"""
from typing import Optional, Dict, Any


# ============================================================================
# 基础异常类
# ============================================================================

class BaseException(Exception):
    """
    基础异常类
    所有自定义异常的父类
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码（用于前端识别）
            status_code: HTTP 状态码
            details: 详细错误信息
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.lower()
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            dict: 异常信息字典
        """
        result = {
            'success': False,
            'error': {
                'code': self.error_code,
                'message': self.message,
                'type': self.__class__.__name__
            }
        }
        
        if self.details:
            result['error']['details'] = self.details
        
        return result


# ============================================================================
# 数据库异常
# ============================================================================

class DatabaseException(BaseException):
    """
    数据库异常
    用于数据库操作相关的错误
    """
    
    def __init__(
        self,
        message: str = "数据库操作失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code or 'database_error',
            status_code=500,
            details=details
        )


class DatabaseConnectionException(DatabaseException):
    """
    数据库连接异常
    用于数据库连接失败的情况
    """
    
    def __init__(
        self,
        message: str = "数据库连接失败",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code='database_connection_error',
            details=details
        )


class DatabaseTimeoutException(DatabaseException):
    """
    数据库超时异常
    用于数据库操作超时的情况
    """
    
    def __init__(
        self,
        message: str = "数据库操作超时",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code='database_timeout_error',
            details=details
        )


class DeadlockException(DatabaseException):
    """
    死锁异常
    用于数据库死锁的情况
    """
    
    def __init__(
        self,
        message: str = "数据库死锁，请重试",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code='database_deadlock_error',
            details=details
        )


class IntegrityException(DatabaseException):
    """
    数据完整性异常
    用于违反数据约束的情况
    """
    
    def __init__(
        self,
        message: str = "数据完整性错误",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code='database_integrity_error',
            details=details
        )


# ============================================================================
# 验证异常
# ============================================================================

class ValidationException(BaseException):
    """
    验证异常
    用于数据验证失败的情况
    """
    
    def __init__(
        self,
        message: str = "数据验证失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code or 'validation_error',
            status_code=422,
            details=details
        )


class RequiredFieldException(ValidationException):
    """
    必填字段异常
    用于缺少必填字段的情况
    """
    
    def __init__(
        self,
        field_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"必填字段 '{field_name}' 不能为空"
        super().__init__(
            message=message,
            error_code='required_field_error',
            details=details or {'field': field_name}
        )


class InvalidFormatException(ValidationException):
    """
    格式无效异常
    用于字段格式不正确的情况
    """
    
    def __init__(
        self,
        field_name: str,
        expected_format: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"字段 '{field_name}' 格式不正确"
        if expected_format:
            message += f"，期望格式：{expected_format}"
        
        super().__init__(
            message=message,
            error_code='invalid_format_error',
            details=details or {'field': field_name, 'expected_format': expected_format}
        )


class ValueOutOfRangeException(ValidationException):
    """
    值超出范围异常
    用于字段值超出允许范围的情况
    """
    
    def __init__(
        self,
        field_name: str,
        min_value: Any = None,
        max_value: Any = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"字段 '{field_name}' 的值超出允许范围"
        if min_value is not None and max_value is not None:
            message += f"，有效范围：{min_value} - {max_value}"
        elif min_value is not None:
            message += f"，最小值：{min_value}"
        elif max_value is not None:
            message += f"，最大值：{max_value}"
        
        super().__init__(
            message=message,
            error_code='value_out_of_range_error',
            details=details or {'field': field_name, 'min': min_value, 'max': max_value}
        )


class DuplicateValueException(ValidationException):
    """
    重复值异常
    用于字段值已存在的情况
    """
    
    def __init__(
        self,
        field_name: str,
        value: Any = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"字段 '{field_name}' 的值已存在"
        if value is not None:
            message += f"：{value}"
        
        super().__init__(
            message=message,
            error_code='duplicate_value_error',
            details=details or {'field': field_name, 'value': value}
        )


# ============================================================================
# 认证异常
# ============================================================================

class AuthenticationException(BaseException):
    """
    认证异常
    用于身份验证失败的情况
    """
    
    def __init__(
        self,
        message: str = "认证失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code or 'authentication_error',
            status_code=401,
            details=details
        )


class InvalidCredentialsException(AuthenticationException):
    """
    无效凭证异常
    用于用户名或密码错误的情况
    """
    
    def __init__(
        self,
        message: str = "用户名或密码错误",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code='invalid_credentials',
            details=details
        )


class TokenExpiredException(AuthenticationException):
    """
    Token 过期异常
    用于 Token 已过期的情况
    """
    
    def __init__(
        self,
        message: str = "认证令牌已过期，请重新登录",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code='token_expired',
            details=details
        )


class TokenInvalidException(AuthenticationException):
    """
    Token 无效异常
    用于 Token 无效的情况
    """
    
    def __init__(
        self,
        message: str = "认证令牌无效",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code='token_invalid',
            details=details
        )


class TokenMissingException(AuthenticationException):
    """
    Token 缺失异常
    用于未提供 Token 的情况
    """
    
    def __init__(
        self,
        message: str = "未提供认证令牌",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code='token_missing',
            details=details
        )


class AccountLockedException(AuthenticationException):
    """
    账户锁定异常
    用于账户被锁定的情况
    """
    
    def __init__(
        self,
        message: str = "账户已被锁定",
        unlock_time: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if unlock_time:
            message += f"，将在 {unlock_time} 解锁"
        
        super().__init__(
            message=message,
            error_code='account_locked',
            details=details or {'unlock_time': unlock_time}
        )


class PasswordExpiredException(AuthenticationException):
    """
    密码过期异常
    用于密码已过期需要修改的情况
    """
    
    def __init__(
        self,
        message: str = "密码已过期，请修改密码",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code='password_expired',
            details=details
        )


# ============================================================================
# 授权异常
# ============================================================================

class AuthorizationException(BaseException):
    """
    授权异常
    用于权限验证失败的情况
    """
    
    def __init__(
        self,
        message: str = "权限不足",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code or 'authorization_error',
            status_code=403,
            details=details
        )


class PermissionDeniedException(AuthorizationException):
    """
    权限拒绝异常
    用于没有特定权限的情况
    """
    
    def __init__(
        self,
        permission: Optional[str] = None,
        message: str = "没有权限执行此操作",
        details: Optional[Dict[str, Any]] = None
    ):
        if permission:
            message = f"没有 '{permission}' 权限"
        
        super().__init__(
            message=message,
            error_code='permission_denied',
            details=details or {'permission': permission}
        )


class RoleRequiredException(AuthorizationException):
    """
    角色要求异常
    用于需要特定角色的情况
    """
    
    def __init__(
        self,
        required_roles: list = None,
        message: str = "需要特定角色权限",
        details: Optional[Dict[str, Any]] = None
    ):
        if required_roles:
            message = f"需要以下角色之一：{', '.join(required_roles)}"
        
        super().__init__(
            message=message,
            error_code='role_required',
            details=details or {'required_roles': required_roles}
        )


class ResourceOwnershipException(AuthorizationException):
    """
    资源所有权异常
    用于无权访问他人资源的情况
    """
    
    def __init__(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        message: str = "无权访问此资源",
        details: Optional[Dict[str, Any]] = None
    ):
        if resource_type and resource_id:
            message = f"无权访问 {resource_type} (ID: {resource_id})"
        
        super().__init__(
            message=message,
            error_code='resource_ownership_error',
            details=details or {'resource_type': resource_type, 'resource_id': resource_id}
        )


# ============================================================================
# 业务异常
# ============================================================================

class BusinessException(BaseException):
    """
    业务异常
    用于业务逻辑错误的情况
    """
    
    def __init__(
        self,
        message: str = "业务操作失败",
        error_code: Optional[str] = None,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code or 'business_error',
            status_code=status_code,
            details=details
        )


class ResourceNotFoundException(BusinessException):
    """
    资源不存在异常
    用于请求的资源不存在的情况
    """
    
    def __init__(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        message: str = "请求的资源不存在",
        details: Optional[Dict[str, Any]] = None
    ):
        if resource_type and resource_id:
            message = f"{resource_type} (ID: {resource_id}) 不存在"
        elif resource_type:
            message = f"{resource_type} 不存在"
        
        super().__init__(
            message=message,
            error_code='resource_not_found',
            status_code=404,
            details=details or {'resource_type': resource_type, 'resource_id': resource_id}
        )


class ResourceAlreadyExistsException(BusinessException):
    """
    资源已存在异常
    用于资源已存在的情况
    """
    
    def __init__(
        self,
        resource_type: Optional[str] = None,
        identifier: Optional[str] = None,
        message: str = "资源已存在",
        details: Optional[Dict[str, Any]] = None
    ):
        if resource_type and identifier:
            message = f"{resource_type} '{identifier}' 已存在"
        
        super().__init__(
            message=message,
            error_code='resource_already_exists',
            status_code=409,
            details=details or {'resource_type': resource_type, 'identifier': identifier}
        )


class InvalidOperationException(BusinessException):
    """
    无效操作异常
    用于不允许的操作的情况
    """
    
    def __init__(
        self,
        message: str = "不允许的操作",
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if operation:
            message = f"不允许执行操作：{operation}"
        
        super().__init__(
            message=message,
            error_code='invalid_operation',
            details=details or {'operation': operation}
        )


class StateConflictException(BusinessException):
    """
    状态冲突异常
    用于资源状态不允许操作的情况
    """
    
    def __init__(
        self,
        current_state: Optional[str] = None,
        required_state: Optional[str] = None,
        message: str = "资源状态冲突",
        details: Optional[Dict[str, Any]] = None
    ):
        if current_state and required_state:
            message = f"当前状态为 '{current_state}'，需要 '{required_state}' 状态才能执行此操作"
        
        super().__init__(
            message=message,
            error_code='state_conflict',
            status_code=409,
            details=details or {'current_state': current_state, 'required_state': required_state}
        )


class QuotaExceededException(BusinessException):
    """
    配额超限异常
    用于超出配额限制的情况
    """
    
    def __init__(
        self,
        quota_type: Optional[str] = None,
        limit: Optional[int] = None,
        current: Optional[int] = None,
        message: str = "已超出配额限制",
        details: Optional[Dict[str, Any]] = None
    ):
        if quota_type and limit:
            message = f"{quota_type} 配额已超限（限制：{limit}，当前：{current or '未知'}）"
        
        super().__init__(
            message=message,
            error_code='quota_exceeded',
            details=details or {'quota_type': quota_type, 'limit': limit, 'current': current}
        )


class DependencyException(BusinessException):
    """
    依赖异常
    用于资源存在依赖关系无法操作的情况
    """
    
    def __init__(
        self,
        resource_type: Optional[str] = None,
        dependency_type: Optional[str] = None,
        dependency_count: Optional[int] = None,
        message: str = "存在依赖关系，无法执行操作",
        details: Optional[Dict[str, Any]] = None
    ):
        if resource_type and dependency_type:
            message = f"{resource_type} 存在 {dependency_count or 0} 个关联的 {dependency_type}，无法执行操作"
        
        super().__init__(
            message=message,
            error_code='dependency_error',
            details=details or {
                'resource_type': resource_type,
                'dependency_type': dependency_type,
                'dependency_count': dependency_count
            }
        )


# ============================================================================
# 外部服务异常
# ============================================================================

class ExternalServiceException(BaseException):
    """
    外部服务异常
    用于外部服务调用失败的情况
    """
    
    def __init__(
        self,
        service_name: Optional[str] = None,
        message: str = "外部服务调用失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if service_name:
            message = f"{service_name} 服务调用失败"
        
        super().__init__(
            message=message,
            error_code=error_code or 'external_service_error',
            status_code=503,
            details=details or {'service_name': service_name}
        )


class ServiceUnavailableException(ExternalServiceException):
    """
    服务不可用异常
    用于外部服务不可用的情况
    """
    
    def __init__(
        self,
        service_name: Optional[str] = None,
        message: str = "服务暂时不可用",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            service_name=service_name,
            message=message,
            error_code='service_unavailable',
            details=details
        )


class ServiceTimeoutException(ExternalServiceException):
    """
    服务超时异常
    用于外部服务调用超时的情况
    """
    
    def __init__(
        self,
        service_name: Optional[str] = None,
        timeout: Optional[int] = None,
        message: str = "服务调用超时",
        details: Optional[Dict[str, Any]] = None
    ):
        if timeout:
            message = f"服务调用超时（{timeout}秒）"
        
        super().__init__(
            service_name=service_name,
            message=message,
            error_code='service_timeout',
            details=details or {'timeout': timeout}
        )


# ============================================================================
# 文件异常
# ============================================================================

class FileException(BaseException):
    """
    文件异常
    用于文件操作相关的错误
    """
    
    def __init__(
        self,
        message: str = "文件操作失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code or 'file_error',
            status_code=400,
            details=details
        )


class FileNotFoundException(FileException):
    """
    文件不存在异常
    """
    
    def __init__(
        self,
        filename: Optional[str] = None,
        message: str = "文件不存在",
        details: Optional[Dict[str, Any]] = None
    ):
        if filename:
            message = f"文件 '{filename}' 不存在"
        
        super().__init__(
            message=message,
            error_code='file_not_found',
            details=details or {'filename': filename}
        )


class FileSizeExceededException(FileException):
    """
    文件大小超限异常
    """
    
    def __init__(
        self,
        max_size: Optional[str] = None,
        message: str = "文件大小超出限制",
        details: Optional[Dict[str, Any]] = None
    ):
        if max_size:
            message = f"文件大小超出限制（最大 {max_size}）"
        
        super().__init__(
            message=message,
            error_code='file_size_exceeded',
            details=details or {'max_size': max_size}
        )


class InvalidFileTypeException(FileException):
    """
    文件类型无效异常
    """
    
    def __init__(
        self,
        allowed_types: Optional[list] = None,
        message: str = "不支持的文件类型",
        details: Optional[Dict[str, Any]] = None
    ):
        if allowed_types:
            message = f"不支持的文件类型，允许的类型：{', '.join(allowed_types)}"
        
        super().__init__(
            message=message,
            error_code='invalid_file_type',
            details=details or {'allowed_types': allowed_types}
        )


# ============================================================================
# 辅助函数
# ============================================================================

def raise_if_not_found(resource, resource_type: str = "资源", resource_id: Any = None):
    """
    如果资源不存在则抛出异常
    
    Args:
        resource: 资源对象
        resource_type: 资源类型名称
        resource_id: 资源 ID
        
    Raises:
        ResourceNotFoundException: 资源不存在时抛出
    """
    if resource is None:
        raise ResourceNotFoundException(
            resource_type=resource_type,
            resource_id=resource_id
        )


def raise_if_exists(resource, resource_type: str = None, identifier: str = None):
    """
    如果资源已存在则抛出异常
    
    Args:
        resource: 资源对象
        resource_type: 资源类型名称
        identifier: 资源标识符
        
    Raises:
        ResourceAlreadyExistsException: 资源已存在时抛出
    """
    if resource is not None:
        raise ResourceAlreadyExistsException(
            resource_type=resource_type,
            identifier=identifier
        )
