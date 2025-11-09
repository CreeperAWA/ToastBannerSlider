"""关键字替换处理器模块

该模块负责处理通知消息中的关键字替换，支持正则表达式匹配，
可以选择性地修改内容和/或字体样式。
"""

import regex as re
import html
from typing import List, Dict, Any, Tuple, Optional, Union
from PySide6.QtGui import QFont
from config import load_config
from logger_config import logger


class KeywordRule:
    """关键字替换规则类"""
    
    def __init__(self, pattern: str, replacement: str = "", font_settings: Optional[Dict[str, Any]] = None, 
                 use_regex: bool = False, replace_content: bool = True, replace_font: bool = False) -> None:
        """
        初始化关键字替换规则
        
        Args:
            pattern: 匹配模式（可以是普通字符串或正则表达式）
            replacement: 替换文本（仅在replace_content为True时有效）
            font_settings: 字体设置（仅在replace_font为True时有效）
            use_regex: 是否使用正则表达式
            replace_content: 是否替换内容
            replace_font: 是否替换字体
        """
        self.pattern = pattern
        self.replacement = replacement
        self.font_settings = font_settings or {}
        self.use_regex = use_regex
        self.replace_content = replace_content
        self.replace_font = replace_font
        self._compiled_pattern: Optional[re.Pattern] = None  # type: ignore
        
        # 如果使用正则表达式，则编译它以提高性能
        if self.use_regex:
            try:
                self._compiled_pattern = re.compile(pattern)
            except re.error as e:
                logger.error(f"无效的正则表达式 '{pattern}': {e}")
                self._compiled_pattern = None
    
    def match(self, text: str) -> bool:
        """
        检查文本是否匹配此规则
        
        Args:
            text: 要检查的文本
            
        Returns:
            bool: 如果匹配返回True，否则返回False
        """
        if self.use_regex and self._compiled_pattern:
            return bool(self._compiled_pattern.search(text))
        elif self.use_regex:
            try:
                return bool(re.search(self.pattern, text))
            except re.error:
                return False
        else:
            return self.pattern in text
    
    def apply_content_replacement(self, text: str) -> str:
        """
        应用内容替换
        
        Args:
            text: 原始文本
            
        Returns:
            str: 替换后的文本
        """
        if not self.replace_content:
            return text
            
        # 处理Unicode转义序列（仅当包含反斜杠时才处理）
        processed_replacement = self.replacement
        if '\\' in self.replacement:
            try:
                processed_replacement = self.replacement.encode().decode('unicode_escape')
            except Exception as e:
                logger.warning(f"处理Unicode转义序列失败 '{self.replacement}': {e}")
                processed_replacement = self.replacement
            
        if self.use_regex and self._compiled_pattern:
            try:
                return self._compiled_pattern.sub(processed_replacement, text)
            except re.error as e:
                logger.error(f"正则表达式替换失败 '{self.pattern}' -> '{processed_replacement}': {e}")
                return text
        elif self.use_regex:
            try:
                return re.sub(self.pattern, processed_replacement, text)
            except re.error as e:
                logger.error(f"正则表达式替换失败 '{self.pattern}' -> '{processed_replacement}': {e}")
                return text
        else:
            return text.replace(self.pattern, processed_replacement)
    
    def apply_font_replacement(self, font: QFont) -> QFont:
        """
        应用字体替换
        
        Args:
            font: 原始字体
            
        Returns:
            QFont: 修改后的字体
        """
        if not self.replace_font or not self.font_settings:
            return font
            
        new_font = QFont(font)  # 创建副本以避免修改原始字体
        
        # 应用字体设置
        if 'size' in self.font_settings:
            new_font.setPointSizeF(float(self.font_settings['size']))
            
        if 'bold' in self.font_settings:
            new_font.setBold(bool(self.font_settings['bold']))
            
        if 'italic' in self.font_settings:
            new_font.setItalic(bool(self.font_settings['italic']))
            
        if 'underline' in self.font_settings:
            new_font.setUnderline(bool(self.font_settings['underline']))
            
        if 'weight' in self.font_settings:
            new_font.setWeight(QFont.Weight(int(self.font_settings['weight'])))
            
        # 确保字体族名正确设置
        if 'family' in self.font_settings and self.font_settings['family']:
            new_font.setFamily(str(self.font_settings['family']))
            
        return new_font
    
    def get_html_style(self) -> str:
        """
        获取HTML样式字符串
        
        Returns:
            str: HTML样式字符串
        """
        styles: List[str] = []
        
        if not self.replace_font or not self.font_settings:
            return ""
            
        # 应用字体设置到HTML样式
        if 'size' in self.font_settings:
            styles.append(f"font-size: {self.font_settings['size']}pt")
            
        if 'bold' in self.font_settings and self.font_settings['bold']:
            styles.append("font-weight: bold")
            
        if 'italic' in self.font_settings and self.font_settings['italic']:
            styles.append("font-style: italic")
            
        if 'underline' in self.font_settings and self.font_settings['underline']:
            styles.append("text-decoration: underline")
            
        # 确保字体族名正确设置，即使在HTML中也要用引号包围
        if 'family' in self.font_settings and self.font_settings['family']:
            # 确保字体名称用双引号包围，以处理包含空格的字体名称
            font_family = str(self.font_settings['family']).replace('"', '').replace("'", "")
            styles.append(f'font-family: "{font_family}"')
            
        return "; ".join(styles)


class KeywordReplacer:
    """关键字替换处理器"""
    
    def __init__(self) -> None:
        """初始化关键字替换处理器"""
        self.rules: List[KeywordRule] = []
        self._load_rules_from_config()
    
    def _load_rules_from_config(self) -> None:
        """从配置中加载规则"""
        config = load_config()
        rules_data = config.get("keyword_replacements")
        
        self.rules = []
        if isinstance(rules_data, list):
            for rule_dict in rules_data:
                if isinstance(rule_dict, dict):
                    try:
                        rule = KeywordRule(
                            pattern=str(rule_dict.get("pattern", "")),
                            replacement=str(rule_dict.get("replacement", "")),
                            font_settings=rule_dict.get("font_settings"),
                            use_regex=bool(rule_dict.get("use_regex", False)),
                            replace_content=bool(rule_dict.get("replace_content", True)),
                            replace_font=bool(rule_dict.get("replace_font", False))
                        )
                        self.rules.append(rule)
                    except Exception as e:
                        logger.error(f"加载关键字替换规则失败: {e}")
    
    def process(self, text: str, font: Optional[QFont] = None) -> Tuple[str, Optional[QFont]]:
        """
        处理文本和字体的关键字替换
        
        Args:
            text: 原始文本
            font: 原始字体（可选）
            
        Returns:
            tuple: (处理后的文本, 处理后的字体)
        """
        processed_text = text
        processed_font = QFont(font) if font else None
        
        # 应用每条规则
        for rule in self.rules:
            # 检查是否匹配
            if rule.match(processed_text):
                # 应用内容替换
                if rule.replace_content:
                    processed_text = rule.apply_content_replacement(processed_text)
                
                # 应用字体替换
                if rule.replace_font:
                    if processed_font:
                        processed_font = rule.apply_font_replacement(processed_font)
                    elif rule.font_settings:
                        # 如果没有传入字体但需要替换字体，则创建一个新字体
                        processed_font = rule.apply_font_replacement(QFont())
        
        return processed_text, processed_font
    
    def process_with_html(self, text: str) -> str:
        """
        处理文本并生成HTML格式输出，支持对匹配部分应用独立样式
        
        Args:
            text: 原始文本
            
        Returns:
            str: HTML格式的文本
        """
        if not self.rules:
            return html.escape(text)
        
        # 创建一个副本用于处理
        processed_text: str = text
        
        # 按顺序处理规则
        for rule in self.rules:
            if not processed_text:
                break
                
            # 如果规则既不替换内容也不替换字体，则跳过
            if not rule.replace_content and not rule.replace_font:
                continue
                
            # 查找所有匹配项
            matches: List[Union[re.Match, Any]] = []
            if rule.use_regex and rule._compiled_pattern:
                matches = list(rule._compiled_pattern.finditer(processed_text))
            elif rule.use_regex:
                try:
                    matches = list(re.finditer(rule.pattern, processed_text))
                except re.error:
                    continue
            else:
                # 处理普通字符串匹配
                start = 0
                while True:
                    pos = processed_text.find(rule.pattern, start)
                    if pos == -1:
                        break
                    # 创建一个模拟match对象
                    class SimpleMatch:
                        def __init__(self, start: int, end: int, group: str):
                            self._start = start
                            self._end = end
                            self._group = group
                            
                        def start(self) -> int:
                            return self._start
                            
                        def end(self) -> int:
                            return self._end
                            
                        def group(self) -> str:
                            return self._group
                    
                    match_obj = SimpleMatch(pos, pos + len(rule.pattern), rule.pattern)
                    matches.append(match_obj)
                    start = pos + len(rule.pattern)
            
            # 对每个匹配项进行处理
            # 从后往前替换，避免位置偏移问题
            for match in reversed(matches):
                # 处理匹配的文本
                matched_text: str = str(match.group())
                replacement_text: str = matched_text
                
                # 应用内容替换
                if rule.replace_content:
                    # 处理Unicode转义序列
                    processed_replacement = rule.replacement
                    if '\\' in rule.replacement:
                        try:
                            processed_replacement = rule.replacement.encode().decode('unicode_escape')
                        except Exception as e:
                            logger.warning(f"处理Unicode转义序列失败 '{rule.replacement}': {e}")
                            processed_replacement = rule.replacement
                    
                    # 执行替换
                    if rule.use_regex:
                        try:
                            replacement_text = str(match.expand(processed_replacement))
                        except re.error:
                            replacement_text = processed_replacement
                    else:
                        replacement_text = processed_replacement
                
                # 应用字体样式（通过HTML）
                if rule.replace_font:
                    style = rule.get_html_style()
                    if style:
                        # 先对内容进行HTML转义，再包裹span标签
                        escaped_text: str = html.escape(replacement_text)
                        replacement_text = f"<span style='{style}'>{escaped_text}</span>"
                    else:
                        replacement_text = html.escape(replacement_text)
                else:
                    replacement_text = html.escape(replacement_text)
                
                # 替换文本
                processed_text = (
                    processed_text[:match.start()] + 
                    replacement_text + 
                    processed_text[match.end():]
                )
        
        return processed_text
    
    def reload_rules(self) -> None:
        """重新加载规则"""
        self._load_rules_from_config()


# 全局关键字替换器实例
_replacer: Optional[KeywordReplacer] = None


def get_replacer() -> KeywordReplacer:
    """
    获取全局关键字替换器实例
    
    Returns:
        KeywordReplacer: 关键字替换器实例
    """
    global _replacer
    if _replacer is None:
        _replacer = KeywordReplacer()
    return _replacer


def process_text_and_font(text: str, font: Optional[QFont] = None) -> Tuple[str, Optional[QFont]]:
    """
    处理文本和字体的关键字替换（便捷函数）
    
    Args:
        text: 原始文本
        font: 原始字体（可选）
        
    Returns:
        tuple: (处理后的文本, 处理后的字体)
    """
    replacer = get_replacer()
    return replacer.process(text, font)


def process_text_with_html(text: str) -> str:
    """
    处理文本并生成HTML格式输出（便捷函数）
    
    Args:
        text: 原始文本
        
    Returns:
        str: HTML格式的文本
    """
    replacer = get_replacer()
    return replacer.process_with_html(text)


def reload_keyword_rules() -> None:
    """重新加载关键字替换规则（当配置发生变化时调用）"""
    replacer = get_replacer()
    replacer.reload_rules()