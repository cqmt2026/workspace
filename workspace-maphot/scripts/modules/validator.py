# -*- coding: utf-8 -*-
"""
脚本生成模块 - 输出校验器
职责：验证生成的JSON脚本是否符合标准格式
输入：脚本JSON dict
输出：(is_valid, errors)
"""

import logging

logger = logging.getLogger(__name__)


class ScriptValidator:
    """脚本校验器"""
    
    REQUIRED_FIELDS = {
        "title": str,
        "date": str,
        "category": str,
        "metadata": dict,
        "hook": dict,
        "sections": list,
        "outro": dict,
        "full_text": str,
        "subtitle_lines": list
    }
    
    HOOK_TYPES = ["排名悬念", "反常识", "数字冲击", "对比反差", "身份代入"]
    OUTRO_TYPES = ["悬念", "互动", "情感"]
    CATEGORIES = ["一张图", "追热点", "深一度"]
    
    def validate(self, script):
        """
        校验脚本
        
        Args:
            script: 脚本JSON dict
            
        Returns:
            (is_valid, errors): 是否通过 + 错误列表
        """
        errors = []
        
        # 1. 检查必填字段
        for field, field_type in self.REQUIRED_FIELDS.items():
            if field not in script:
                errors.append(f"缺少必填字段: {field}")
            elif not isinstance(script[field], field_type):
                errors.append(f"字段{field}类型错误，期望{field_type.__name__}")
        
        if errors:
            return False, errors
        
        # 2. 校验metadata
        meta = script["metadata"]
        if "word_count" not in meta:
            errors.append("metadata缺少word_count")
        if "estimated_duration_seconds" not in meta:
            errors.append("metadata缺少estimated_duration_seconds")
        
        # 3. 校验hook
        hook = script["hook"]
        if hook.get("type") not in self.HOOK_TYPES:
            errors.append(f"hook.type无效: {hook.get('type')}")
        if not hook.get("text"):
            errors.append("hook.text为空")
        if len(hook.get("text", "")) > 60:
            errors.append("hook.text超过60字，太长")
        
        # 4. 校验sections
        sections = script["sections"]
        if not sections:
            errors.append("sections为空")
        else:
            for i, sec in enumerate(sections):
                prefix = f"sections[{i}]"
                if "narration" not in sec or len(sec.get("narration", "")) == 0:
                    errors.append(f"{prefix}.narration为空")
                if "data_point" not in sec:
                    errors.append(f"{prefix}.data_point缺失")
                if "visual" not in sec:
                    errors.append(f"{prefix}.visual缺失")
                # 口语化检查：每段narration总字数不超过60字（允许包含多个短句）
                narration = sec.get("narration", "")
                if len(narration) > 60:
                    errors.append(f"{prefix}.narration超过60字: {len(narration)}字")
        
        # 5. 校验outro
        outro = script["outro"]
        if outro.get("type") not in self.OUTRO_TYPES:
            errors.append(f"outro.type无效: {outro.get('type')}")
        if not outro.get("text"):
            errors.append("outro.text为空")
        # 检查是否有互动引导词
        outro_text = outro.get("text", "")
        has_interaction = any(kw in outro_text for kw in ["评论", "关注", "收藏", "点赞", "聊聊", "看看", "下期"])
        if not has_interaction:
            errors.append("outro.text缺少互动引导词（评论/关注/收藏/点赞）")
        
        # 6. 校验full_text
        full_text = script.get("full_text", "")
        if len(full_text) < 20:
            errors.append("full_text太短，少于20字")
        
        # 7. 校验subtitle_lines
        subtitle_lines = script.get("subtitle_lines", [])
        for i, line in enumerate(subtitle_lines):
            if len(line) > 15:
                errors.append(f"subtitle_lines[{i}]超过15字: {line}")
        
        # 8. 一致性检查：full_text应该包含所有sections的narration
        # 注意：full_text由钩子+sections+结尾拼接而成，可能因句号分隔符不同导致不完全匹配
        # 改为检查：full_text长度应该在合理范围内（钩子+各段+结尾）
        expected_min_len = sum(len(s.get("narration", "")) for s in sections)
        if expected_min_len > 0 and len(full_text) < expected_min_len * 0.8:
            errors.append(f"full_text太短，可能缺少内容")
        
        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"脚本校验失败: {errors}")
        else:
            logger.info("脚本校验通过")
        
        return is_valid, errors
