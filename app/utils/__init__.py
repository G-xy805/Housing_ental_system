"""
应用工具包
提供 JWT、认证装饰器、响应格式、错误处理等工具模块
"""
from app.utils.jwt import (
    generate_token,
    verify_token,
    refresh_token,
    get_token_from_request,
    get_current_user,
    create_token_response,
    JWTError,
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingError
)

from app.utils.decorators import (
    token_required,
    login_required,
    admin_required,
    role_required,
    permission_required,
    optional_login
)

from app.utils.responses import (
    APIResponse,
    AuthResponse,
    PaginationResponse,
    register_error_handlers,
    format_user_response,
    format_error_response
)

# 异常处理
from app.utils.exceptions import (
    BaseException as AppBaseException,
    DatabaseException,
    DatabaseConnectionException,
    DatabaseTimeoutException,
    DeadlockException,
    IntegrityException,
    ValidationException,
    RequiredFieldException,
    InvalidFormatException,
    ValueOutOfRangeException,
    DuplicateValueException,
    AuthenticationException,
    InvalidCredentialsException,
    TokenExpiredException,
    TokenInvalidException,
    TokenMissingException,
    AccountLockedException,
    PasswordExpiredException,
    AuthorizationException,
    PermissionDeniedException,
    RoleRequiredException,
    ResourceOwnershipException,
    BusinessException,
    ResourceNotFoundException,
    ResourceAlreadyExistsException,
    InvalidOperationException,
    StateConflictException,
    QuotaExceededException,
    DependencyException,
    ExternalServiceException,
    ServiceUnavailableException,
    ServiceTimeoutException,
    FileException,
    FileNotFoundException,
    FileSizeExceededException,
    InvalidFileTypeException,
    raise_if_not_found,
    raise_if_exists
)

# 事务管理
from app.utils.transaction import (
    transaction_context,
    transactional,
    with_transaction,
    with_nested_transaction,
    begin_transaction,
    commit_transaction,
    rollback_transaction,
    begin_nested_transaction,
    batch_insert,
    batch_update,
    batch_delete
)

# 错误处理
from app.utils.error_handler import (
    log_error,
    log_request_context,
    handle_errors,
    get_error_statistics,
    clear_error_statistics
)

# 重试机制
from app.utils.retry import (
    RetryConfig,
    retry_on_exception,
    retry_call,
    retry_on_db_error,
    with_retry,
    with_db_retry,
    RetryContext,
    retry_batch_operation,
    get_retry_statistics,
    clear_retry_statistics
)

__all__ = [
    # JWT
    'generate_token',
    'verify_token',
    'refresh_token',
    'get_token_from_request',
    'get_current_user',
    'create_token_response',
    'JWTError',
    'TokenExpiredError',
    'TokenInvalidError',
    'TokenMissingError',
    
    # Decorators
    'token_required',
    'login_required',
    'admin_required',
    'role_required',
    'permission_required',
    'optional_login',
    
    # Responses
    'APIResponse',
    'AuthResponse',
    'PaginationResponse',
    'register_error_handlers',
    'format_user_response',
    'format_error_response',
    
    # Exceptions
    'AppBaseException',
    'DatabaseException',
    'DatabaseConnectionException',
    'DatabaseTimeoutException',
    'DeadlockException',
    'IntegrityException',
    'ValidationException',
    'RequiredFieldException',
    'InvalidFormatException',
    'ValueOutOfRangeException',
    'DuplicateValueException',
    'AuthenticationException',
    'InvalidCredentialsException',
    'TokenExpiredException',
    'TokenInvalidException',
    'TokenMissingException',
    'AccountLockedException',
    'PasswordExpiredException',
    'AuthorizationException',
    'PermissionDeniedException',
    'RoleRequiredException',
    'ResourceOwnershipException',
    'BusinessException',
    'ResourceNotFoundException',
    'ResourceAlreadyExistsException',
    'InvalidOperationException',
    'StateConflictException',
    'QuotaExceededException',
    'DependencyException',
    'ExternalServiceException',
    'ServiceUnavailableException',
    'ServiceTimeoutException',
    'FileException',
    'FileNotFoundException',
    'FileSizeExceededException',
    'InvalidFileTypeException',
    'raise_if_not_found',
    'raise_if_exists',
    
    # Transaction
    'transaction_context',
    'transactional',
    'with_transaction',
    'with_nested_transaction',
    'begin_transaction',
    'commit_transaction',
    'rollback_transaction',
    'begin_nested_transaction',
    'batch_insert',
    'batch_update',
    'batch_delete',
    
    # Error Handler
    'log_error',
    'log_request_context',
    'handle_errors',
    'get_error_statistics',
    'clear_error_statistics',
    
    # Retry
    'RetryConfig',
    'retry_on_exception',
    'retry_call',
    'retry_on_db_error',
    'with_retry',
    'with_db_retry',
    'RetryContext',
    'retry_batch_operation',
    'get_retry_statistics',
    'clear_retry_statistics'
]