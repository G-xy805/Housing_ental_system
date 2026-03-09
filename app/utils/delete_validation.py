"""
删除验证工具模块

提供统一的删除预览和验证功能，支持：
- 删除前验证
- 删除预览
- 级联软删除
- 删除操作日志记录
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DeleteValidationHelper:
    """
    删除验证辅助类
    
    提供统一的删除验证和预览功能
    """
    
    @staticmethod
    def validate_and_preview(model_instance) -> Dict[str, Any]:
        """
        验证并预览删除操作
        
        Args:
            model_instance: 模型实例
            
        Returns:
            Dict: 包含验证结果和预览信息的字典
        """
        can_delete, errors = model_instance.validate_delete()
        preview = model_instance.get_delete_preview()
        
        return {
            'can_delete': can_delete,
            'errors': errors,
            'preview': preview,
            'model_name': model_instance.__class__.__name__,
            'model_id': model_instance.id,
            'model_display': str(model_instance)
        }
    
    @staticmethod
    def execute_cascade_delete(model_instance, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        执行级联软删除
        
        Args:
            model_instance: 模型实例
            user_id: 操作用户 ID
            
        Returns:
            Dict: 删除结果
        """
        # 先验证
        can_delete, errors = model_instance.validate_delete()
        if not can_delete:
            return {
                'success': False,
                'message': '; '.join(errors),
                'errors': errors,
                'deleted_count': 0
            }
        
        # 执行级联软删除
        success, message, deleted_count = model_instance.cascade_soft_delete(user_id=user_id)
        
        return {
            'success': success,
            'message': message,
            'deleted_count': deleted_count,
            'model_name': model_instance.__class__.__name__,
            'model_id': model_instance.id
        }
    
    @staticmethod
    def batch_validate(model_instances: List) -> Dict[str, Any]:
        """
        批量验证删除操作
        
        Args:
            model_instances: 模型实例列表
            
        Returns:
            Dict: 批量验证结果
        """
        results = []
        can_delete_all = True
        total_errors = []
        
        for instance in model_instances:
            result = DeleteValidationHelper.validate_and_preview(instance)
            results.append(result)
            
            if not result['can_delete']:
                can_delete_all = False
                total_errors.extend([
                    f"{result['model_name']}({result['model_id']}): {error}"
                    for error in result['errors']
                ])
        
        return {
            'can_delete_all': can_delete_all,
            'total_errors': total_errors,
            'total_count': len(model_instances),
            'deletable_count': sum(1 for r in results if r['can_delete']),
            'results': results
        }
    
    @staticmethod
    def get_deletion_summary(model_instance) -> Dict[str, Any]:
        """
        获取删除摘要信息
        
        Args:
            model_instance: 模型实例
            
        Returns:
            Dict: 删除摘要
        """
        preview = model_instance.get_delete_preview()
        
        # 统计各级联模型的删除数量
        cascade_summary = {}
        for item in preview['cascade_items']:
            model_name = item['model']
            if model_name not in cascade_summary:
                cascade_summary[model_name] = 0
            cascade_summary[model_name] += 1
        
        # 统计各受影响模型的数量
        affected_summary = {}
        for item in preview['affected_items']:
            model_name = item['model']
            if model_name not in affected_summary:
                affected_summary[model_name] = 0
            affected_summary[model_name] += 1
        
        return {
            'model_name': model_instance.__class__.__name__,
            'model_id': model_instance.id,
            'model_display': str(model_instance),
            'can_delete': preview['can_delete'],
            'errors': preview['errors'],
            'cascade_summary': cascade_summary,
            'affected_summary': affected_summary,
            'total_cascade': preview['total_cascade'],
            'total_affected': preview['total_affected']
        }


class DeleteLogger:
    """
    删除操作日志记录器
    
    记录所有删除操作的详细信息
    """
    
    @staticmethod
    def log_delete_operation(
        model_name: str,
        model_id: int,
        action: str,
        user_id: Optional[int] = None,
        details: Optional[Dict] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        记录删除操作日志
        
        Args:
            model_name: 模型名称
            model_id: 模型 ID
            action: 操作类型（soft_delete/hard_delete/cascade_delete）
            user_id: 操作用户 ID
            details: 详细信息
            success: 是否成功
            error_message: 错误消息
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'model_name': model_name,
            'model_id': model_id,
            'action': action,
            'user_id': user_id,
            'success': success,
            'error_message': error_message,
            'details': details or {}
        }
        
        if success:
            logger.info(f"删除操作成功: {log_data}")
        else:
            logger.warning(f"删除操作失败: {log_data}")
    
    @staticmethod
    def log_cascade_delete(
        parent_model: str,
        parent_id: int,
        cascade_items: List[Dict],
        user_id: Optional[int] = None,
        success: bool = True
    ):
        """
        记录级联删除操作日志
        
        Args:
            parent_model: 父模型名称
            parent_id: 父模型 ID
            cascade_items: 级联删除的项目列表
            user_id: 操作用户 ID
            success: 是否成功
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'parent_model': parent_model,
            'parent_id': parent_id,
            'user_id': user_id,
            'cascade_count': len(cascade_items),
            'cascade_items': cascade_items,
            'success': success
        }
        
        if success:
            logger.info(f"级联删除操作成功: {log_data}")
        else:
            logger.warning(f"级联删除操作失败: {log_data}")


class DeletePreviewFormatter:
    """
    删除预览格式化器
    
    提供用户友好的删除预览信息格式化
    """
    
    @staticmethod
    def format_preview(model_instance) -> str:
        """
        格式化删除预览信息为可读文本
        
        Args:
            model_instance: 模型实例
            
        Returns:
            str: 格式化后的预览文本
        """
        summary = DeleteValidationHelper.get_deletion_summary(model_instance)
        
        lines = []
        lines.append(f"{'='*50}")
        lines.append(f"删除预览: {summary['model_name']} (ID: {summary['model_id']})")
        lines.append(f"{'='*50}")
        
        if not summary['can_delete']:
            lines.append("\n[警告] 无法删除，原因如下:")
            for error in summary['errors']:
                lines.append(f"  - {error}")
        else:
            lines.append("\n[可以删除]")
        
        if summary['cascade_summary']:
            lines.append("\n将被级联删除的数据:")
            for model_name, count in summary['cascade_summary'].items():
                lines.append(f"  - {model_name}: {count} 条")
        
        if summary['affected_summary']:
            lines.append("\n将受影响的数据:")
            for model_name, count in summary['affected_summary'].items():
                lines.append(f"  - {model_name}: {count} 条")
        
        lines.append(f"\n总计: 级联删除 {summary['total_cascade']} 条，受影响 {summary['total_affected']} 条")
        lines.append(f"{'='*50}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_preview_html(model_instance) -> str:
        """
        格式化删除预览信息为 HTML
        
        Args:
            model_instance: 模型实例
            
        Returns:
            str: HTML 格式的预览文本
        """
        summary = DeleteValidationHelper.get_deletion_summary(model_instance)
        
        html_parts = []
        html_parts.append('<div class="delete-preview">')
        html_parts.append(f'<h3>删除预览: {summary["model_name"]} (ID: {summary["model_id"]})</h3>')
        
        if not summary['can_delete']:
            html_parts.append('<div class="alert alert-warning">')
            html_parts.append('<strong>无法删除，原因如下:</strong>')
            html_parts.append('<ul>')
            for error in summary['errors']:
                html_parts.append(f'<li>{error}</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')
        else:
            html_parts.append('<div class="alert alert-success">可以删除</div>')
        
        if summary['cascade_summary']:
            html_parts.append('<div class="cascade-items">')
            html_parts.append('<h4>将被级联删除的数据:</h4>')
            html_parts.append('<ul>')
            for model_name, count in summary['cascade_summary'].items():
                html_parts.append(f'<li>{model_name}: {count} 条</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')
        
        if summary['affected_summary']:
            html_parts.append('<div class="affected-items">')
            html_parts.append('<h4>将受影响的数据:</h4>')
            html_parts.append('<ul>')
            for model_name, count in summary['affected_summary'].items():
                html_parts.append(f'<li>{model_name}: {count} 条</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')
        
        html_parts.append(f'<p><strong>总计:</strong> 级联删除 {summary["total_cascade"]} 条，受影响 {summary["total_affected"]} 条</p>')
        html_parts.append('</div>')
        
        return ''.join(html_parts)
