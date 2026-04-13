import spacy
import re
import json
from fuzzywuzzy import fuzz
import pandas as pd

class AdvancedInformationExtractor:
    def __init__(self):
        # 加载spaCy模型
        try:
            self.nlp = spacy.load('zh_core_web_sm')
        except Exception:
            # 如果模型不存在，使用英文模型
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except Exception:
                # 如果都不存在，使用简单的正则提取
                self.nlp = None
        
        # 定义常用实体类型
        self.entity_types = {
            'date': r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
            'number': r'\d+(\.\d+)?',
            'percentage': r'\d+(\.\d+)?%',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'\d{3,4}-?\d{7,8}'
        }
    
    def extract_entities(self, text):
        """提取命名实体"""
        entities = {}
        
        # 使用spaCy提取实体
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                entities[ent.label_].append(ent.text)
        
        # 使用正则表达式提取额外实体
        for entity_type, pattern in self.entity_types.items():
            matches = re.findall(pattern, text)
            if matches:
                if entity_type not in entities:
                    entities[entity_type] = []
                entities[entity_type].extend(matches)
        
        return entities
    
    def extract_key_value(self, text, key_patterns):
        """提取键值对信息"""
        results = {}
        
        for key, patterns in key_patterns.items():
            if isinstance(patterns, str):
                patterns = [patterns]
            
            for pattern in patterns:
                # 尝试不同的模式匹配
                regex_patterns = [
                    f'{pattern}[:：]\s*(.*?)\n',
                    f'{pattern}[:：]\s*(.*?)\n\s*\n',
                    f'{pattern}[:：]\s*(.*?)(?=\n\w+:)',
                    f'{pattern}[:：]\s*(.*?)$'
                ]
                
                for regex_pattern in regex_patterns:
                    matches = re.findall(regex_pattern, text, re.DOTALL)
                    if matches:
                        results[key] = matches[0].strip()
                        break
        
        return results
    
    def extract_table_info(self, tables, keywords):
        """从表格中提取信息"""
        results = {}
        
        for table in tables:
            if isinstance(table, dict) and 'data' in table:
                df = pd.DataFrame(table['data'])
                
                # 查找包含关键字的行
                for keyword in keywords:
                    for i, row in df.iterrows():
                        for j, cell in enumerate(row):
                            if isinstance(cell, str) and fuzz.partial_ratio(keyword, cell) > 70:
                                # 提取该行或相关行的信息
                                results[keyword] = row.to_dict()
                                break
        
        return results
    
    def extract_structured_data(self, text, tables=None, key_patterns=None):
        """提取结构化数据"""
        results = {
            'entities': self.extract_entities(text),
            'key_values': {},
            'table_info': {}
        }
        
        if key_patterns:
            results['key_values'] = self.extract_key_value(text, key_patterns)
        
        if tables:
            # 从表格中提取信息
            keywords = list(key_patterns.keys()) if key_patterns else []
            results['table_info'] = self.extract_table_info(tables, keywords)
        
        return results