# IDP处理层与数据层实现详解

## IDP处理层Python实现详解

### 1. 文档解析模块深度实现

#### 增强版文档解析器

```python
import docx
import PyPDF2
from tika import parser
import os

class AdvancedDocumentParser:
    def __init__(self):
        pass
    
    def parse_word(self, file_path):
        """增强版Word文档解析"""
        try:
            doc = docx.Document(file_path)
            content = {
                'text': [],
                'tables': [],
                'images': []
            }
            
            # 提取文本
            for paragraph in doc.paragraphs:
                content['text'].append(paragraph.text)
            
            # 提取表格
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)
                content['tables'].append(table_data)
            
            # 提取图片（需要额外处理）
            # 这里可以添加图片提取逻辑
            
            return content
        except Exception as e:
            return {'error': str(e)}
    
    def parse_pdf(self, file_path):
        """增强版PDF文档解析"""
        try:
            content = {
                'text': [],
                'tables': []
            }
            
            # 使用PyPDF2提取文本
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    content['text'].append(page.extract_text())
            
            # 这里可以集成Camelot等库提取表格
            
            return content
        except Exception as e:
            return {'error': str(e)}
    
    def parse_image(self, file_path):
        """解析图片文档"""
        try:
            # 这里可以集成OCR处理
            return {'text': []}
        except Exception as e:
            return {'error': str(e)}
    
    def parse_document(self, file_path):
        """根据文件类型自动选择解析方法"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.docx':
            return self.parse_word(file_path)
        elif ext == '.pdf':
            return self.parse_pdf(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            return self.parse_image(file_path)
        else:
            # 使用Tika处理其他格式
            try:
                parsed = parser.from_file(file_path)
                return {'text': [parsed.get('content', '')]}
            except Exception as e:
                return {'error': str(e)}
```

### 2. OCR处理模块深度实现

#### 增强版OCR处理器

```python
import cv2
import pytesseract
from easyocr import Reader
import numpy as np

class AdvancedOCRProcessor:
    def __init__(self):
        self.reader = Reader(['ch_sim', 'en'])
    
    def preprocess_image(self, image):
        """增强版图像预处理"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 去噪
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # 自适应阈值二值化
        thresh = cv2.adaptiveThreshold(
            denoised, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 2
        )
        
        # 膨胀操作，增强文字连接性
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        
        return dilated
    
    def ocr_with_tesseract(self, image_path):
        """使用Tesseract进行OCR"""
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return {'error': '无法读取图像'}
            
            # 预处理
            preprocessed = self.preprocess_image(image)
            
            # OCR识别
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(
                preprocessed, 
                lang='chi_sim+eng',
                config=custom_config
            )
            
            # 获取文本位置信息
            data = pytesseract.image_to_data(
                preprocessed, 
                lang='chi_sim+eng',
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # 整理结果
            result = {
                'text': text,
                'boxes': []
            }
            
            # 提取文本框
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 60:  # 置信度阈值
                    result['boxes'].append({
                        'text': data['text'][i],
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i]
                    })
            
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def ocr_with_easyocr(self, image_path):
        """使用EasyOCR进行OCR"""
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return {'error': '无法读取图像'}
            
            # 预处理
            preprocessed = self.preprocess_image(image)
            
            # OCR识别
            results = self.reader.readtext(preprocessed)
            
            # 整理结果
            text = ' '.join([result[1] for result in results if result[2] > 0.6])
            boxes = []
            
            for result in results:
                if result[2] > 0.6:  # 置信度阈值
                    boxes.append({
                        'text': result[1],
                        'points': result[0],
                        'confidence': result[2]
                    })
            
            return {
                'text': text,
                'boxes': boxes
            }
        except Exception as e:
            return {'error': str(e)}
    
    def ocr_image(self, image_path, engine='easyocr'):
        """统一OCR接口"""
        if engine == 'tesseract':
            return self.ocr_with_tesseract(image_path)
        else:
            return self.ocr_with_easyocr(image_path)
```

### 3. 表格识别模块深度实现

#### 增强版表格识别器

```python
import camelot
import pandas as pd
import cv2
import numpy as np

class AdvancedTableRecognizer:
    def __init__(self):
        pass
    
    def extract_tables_from_pdf(self, pdf_path, method='lattice'):
        """从PDF中提取表格"""
        try:
            # 使用camelot提取表格
            tables = camelot.read_pdf(
                pdf_path, 
                pages='all',
                flavor=method
            )
            
            # 整理结果
            result = []
            for i, table in enumerate(tables):
                # 转换为DataFrame
                df = table.df
                
                # 清理数据
                df = self.clean_table_data(df)
                
                # 添加表格信息
                table_info = {
                    'page': table.page,
                    'coordinates': table.cells,
                    'data': df.to_dict('records'),
                    'shape': df.shape
                }
                result.append(table_info)
            
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def clean_table_data(self, df):
        """清理表格数据"""
        # 去除空行
        df = df.replace('', np.nan)
        df = df.dropna(how='all')
        
        # 去除空列
        df = df.dropna(axis=1, how='all')
        
        # 去除首尾空格
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        
        return df
    
    def extract_tables_from_image(self, image_path):
        """从图像中提取表格"""
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return {'error': '无法读取图像'}
            
            # 预处理
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(
                gray, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 
                11, 2
            )
            
            # 检测水平线和垂直线
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            horizontal_lines = cv2.morphologyEx(
                thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2
            )
            vertical_lines = cv2.morphologyEx(
                thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2
            )
            
            # 合并线条
            table_mask = cv2.add(horizontal_lines, vertical_lines)
            
            # 查找轮廓
            contours, _ = cv2.findContours(
                table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # 处理表格
            tables = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # 过滤小轮廓
                    x, y, w, h = cv2.boundingRect(contour)
                    tables.append({
                        'coordinates': (x, y, w, h),
                        'area': area
                    })
            
            return tables
        except Exception as e:
            return {'error': str(e)}
    
    def save_tables_to_excel(self, tables, output_path):
        """将提取的表格保存为Excel文件"""
        try:
            with pd.ExcelWriter(output_path) as writer:
                for i, table in enumerate(tables):
                    if isinstance(table, dict) and 'data' in table:
                        df = pd.DataFrame(table['data'])
                        sheet_name = f'Table_{i+1}_Page_{table.get("page", "N/A")}'
                        # 确保sheet名称不超过31个字符
                        sheet_name = sheet_name[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            return True
        except Exception as e:
            return {'error': str(e)}
```

### 4. 信息提取模块深度实现

#### 增强版信息提取器

```python
import spacy
import re
import json
from fuzzywuzzy import fuzz

class AdvancedInformationExtractor:
    def __init__(self):
        # 加载spaCy模型
        try:
            self.nlp = spacy.load('zh_core_web_sm')
        except Exception:
            # 如果模型不存在，使用英文模型
            self.nlp = spacy.load('en_core_web_sm')
        
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
        doc = self.nlp(text)
        entities = {}
        
        # 使用spaCy提取实体
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
```

## IDP数据层设计与实现

### 1. 数据层架构设计

```
数据层
├── 结构化数据存储
│   ├── 关系型数据库（MySQL/PostgreSQL）
│   ├── 非关系型数据库（MongoDB）
│   └── 缓存（Redis）
├── 文档元数据管理
│   ├── 文档索引
│   ├── 处理状态跟踪
│   └── 版本控制
└── 模型存储
    ├── OCR模型
    ├── NLP模型
    └── 表格识别模型
```

### 2. 数据存储实现

#### 关系型数据库设计

**`documents`表**

| 字段名              | 数据类型           | 描述       |
| ---------------- | -------------- | -------- |
| `id`             | `INT`          | 文档ID（主键） |
| `filename`       | `VARCHAR(255)` | 文件名      |
| `filepath`       | `VARCHAR(512)` | 文件路径     |
| `filetype`       | `VARCHAR(50)`  | 文件类型     |
| `size`           | `BIGINT`       | 文件大小（字节） |
| `upload_time`    | `DATETIME`     | 上传时间     |
| `status`         | `VARCHAR(50)`  | 处理状态     |
| `processed_time` | `DATETIME`     | 处理完成时间   |
| `error_message`  | `TEXT`         | 错误信息     |

**`extracted_data`表**

| 字段名              | 数据类型           | 描述          |
| ---------------- | -------------- | ----------- |
| `id`             | `INT`          | 数据ID（主键）    |
| `document_id`    | `INT`          | 关联的文档ID（外键） |
| `data_type`      | `VARCHAR(50)`  | 数据类型        |
| `data_key`       | `VARCHAR(255)` | 数据键         |
| `data_value`     | `TEXT`         | 数据值         |
| `confidence`     | `FLOAT`        | 置信度         |
| `extracted_time` | `DATETIME`     | 提取时间        |

**`tables`表**

| 字段名              | 数据类型       | 描述           |
| ---------------- | ---------- | ------------ |
| `id`             | `INT`      | 表格ID（主键）     |
| `document_id`    | `INT`      | 关联的文档ID（外键）  |
| `page_number`    | `INT`      | 页码           |
| `table_index`    | `INT`      | 表格索引         |
| `data`           | `JSON`     | 表格数据（JSON格式） |
| `extracted_time` | `DATETIME` | 提取时间         |

### 3. 数据层实现示例

#### 数据库操作模块

```python
import mysql.connector
import pymongo
import redis
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, config):
        # 初始化MySQL连接
        self.mysql_conn = mysql.connector.connect(
            host=config['mysql']['host'],
            user=config['mysql']['user'],
            password=config['mysql']['password'],
            database=config['mysql']['database']
        )
        self.mysql_cursor = self.mysql_conn.cursor()
        
        # 初始化MongoDB连接
        self.mongo_client = pymongo.MongoClient(config['mongodb']['uri'])
        self.mongo_db = self.mongo_client[config['mongodb']['database']]
        
        # 初始化Redis连接
        self.redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            db=config['redis']['db']
        )
    
    def insert_document(self, filename, filepath, filetype, size):
        """插入文档记录"""
        try:
            query = """
                INSERT INTO documents 
                (filename, filepath, filetype, size, upload_time, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (
                filename, 
                filepath, 
                filetype, 
                size, 
                datetime.now(), 
                'pending'
            )
            self.mysql_cursor.execute(query, values)
            self.mysql_conn.commit()
            return self.mysql_cursor.lastrowid
        except Exception as e:
            print(f"插入文档记录失败: {e}")
            return None
    
    def update_document_status(self, document_id, status, error_message=None):
        """更新文档状态"""
        try:
            query = """
                UPDATE documents 
                SET status = %s, processed_time = %s, error_message = %s
                WHERE id = %s
            """
            values = (
                status, 
                datetime.now() if status in ['completed', 'failed'] else None, 
                error_message, 
                document_id
            )
            self.mysql_cursor.execute(query, values)
            self.mysql_conn.commit()
            return True
        except Exception as e:
            print(f"更新文档状态失败: {e}")
            return False
    
    def insert_extracted_data(self, document_id, data_type, data_key, data_value, confidence=1.0):
        """插入提取的数据"""
        try:
            query = """
                INSERT INTO extracted_data 
                (document_id, data_type, data_key, data_value, confidence, extracted_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (
                document_id, 
                data_type, 
                data_key, 
                data_value, 
                confidence, 
                datetime.now()
            )
            self.mysql_cursor.execute(query, values)
            self.mysql_conn.commit()
            return True
        except Exception as e:
            print(f"插入提取数据失败: {e}")
            return False
    
    def insert_table(self, document_id, page_number, table_index, data):
        """插入提取的表格"""
        try:
            query = """
                INSERT INTO tables 
                (document_id, page_number, table_index, data, extracted_time)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (
                document_id, 
                page_number, 
                table_index, 
                json.dumps(data), 
                datetime.now()
            )
            self.mysql_cursor.execute(query, values)
            self.mysql_conn.commit()
            return True
        except Exception as e:
            print(f"插入表格数据失败: {e}")
            return False
    
    def get_document(self, document_id):
        """获取文档信息"""
        try:
            query = "SELECT * FROM documents WHERE id = %s"
            self.mysql_cursor.execute(query, (document_id,))
            return self.mysql_cursor.fetchone()
        except Exception as e:
            print(f"获取文档信息失败: {e}")
            return None
    
    def get_extracted_data(self, document_id):
        """获取文档提取的数据"""
        try:
            query = "SELECT * FROM extracted_data WHERE document_id = %s"
            self.mysql_cursor.execute(query, (document_id,))
            return self.mysql_cursor.fetchall()
        except Exception as e:
            print(f"获取提取数据失败: {e}")
            return []
    
    def cache_result(self, key, value, expire=3600):
        """缓存结果"""
        try:
            self.redis_client.setex(
                key, 
                expire, 
                json.dumps(value)
            )
            return True
        except Exception as e:
            print(f"缓存结果失败: {e}")
            return False
    
    def get_cached_result(self, key):
        """获取缓存结果"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"获取缓存结果失败: {e}")
            return None
    
    def close(self):
        """关闭数据库连接"""
        try:
            self.mysql_cursor.close()
            self.mysql_conn.close()
            self.mongo_client.close()
            self.redis_client.close()
        except Exception as e:
            print(f"关闭数据库连接失败: {e}")
```

### 4. 文档元数据管理

#### 元数据管理模块

```python
import os
import hashlib
import json
from datetime import datetime

class MetadataManager:
    def __init__(self, metadata_dir):
        self.metadata_dir = metadata_dir
        if not os.path.exists(self.metadata_dir):
            os.makedirs(self.metadata_dir)
    
    def generate_document_hash(self, file_path):
        """生成文档哈希值"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(65536)  # 64KB chunks
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()
    
    def create_metadata(self, document_id, file_path, file_type):
        """创建文档元数据"""
        metadata = {
            'document_id': document_id,
            'file_path': file_path,
            'file_type': file_type,
            'file_size': os.path.getsize(file_path),
            'hash': self.generate_document_hash(file_path),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'status': 'pending',
            'versions': []
        }
        
        # 保存元数据
        metadata_file = os.path.join(self.metadata_dir, f'{document_id}.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return metadata
    
    def update_metadata(self, document_id, updates):
        """更新文档元数据"""
        metadata_file = os.path.join(self.metadata_dir, f'{document_id}.json')
        if not os.path.exists(metadata_file):
            return None
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 更新字段
        for key, value in updates.items():
            metadata[key] = value
        metadata['updated_at'] = datetime.now().isoformat()
        
        # 保存更新后的元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return metadata
    
    def get_metadata(self, document_id):
        """获取文档元数据"""
        metadata_file = os.path.join(self.metadata_dir, f'{document_id}.json')
        if not os.path.exists(metadata_file):
            return None
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return metadata
    
    def add_version(self, document_id, version_info):
        """添加文档版本"""
        metadata = self.get_metadata(document_id)
        if not metadata:
            return None
        
        # 添加版本信息
        version_info['timestamp'] = datetime.now().isoformat()
        metadata['versions'].append(version_info)
        metadata['updated_at'] = datetime.now().isoformat()
        
        # 保存更新后的元数据
        metadata_file = os.path.join(self.metadata_dir, f'{document_id}.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return metadata
```

## IDP与RPA集成实践

### 1. 完整IDP系统实现

#### 综合IDP系统

```python
class ComprehensiveIDPSystem:
    def __init__(self, config):
        # 初始化各个模块
        self.parser = AdvancedDocumentParser()
        self.ocr_processor = AdvancedOCRProcessor()
        self.table_recognizer = AdvancedTableRecognizer()
        self.extractor = AdvancedInformationExtractor()
        self.db_manager = DatabaseManager(config['database'])
        self.metadata_manager = MetadataManager(config['metadata_dir'])
    
    def process_document(self, file_path):
        """处理文档的完整流程"""
        try:
            # 1. 提取文件信息
            filename = os.path.basename(file_path)
            filetype = os.path.splitext(filename)[1].lower()
            size = os.path.getsize(file_path)
            
            # 2. 插入文档记录
            document_id = self.db_manager.insert_document(
                filename, file_path, filetype, size
            )
            if not document_id:
                return {'error': '无法创建文档记录'}
            
            # 3. 创建元数据
            self.metadata_manager.create_metadata(
                document_id, file_path, filetype
            )
            
            # 4. 更新状态为处理中
            self.db_manager.update_document_status(document_id, 'processing')
            
            # 5. 解析文档
            parsed_result = self.parser.parse_document(file_path)
            if 'error' in parsed_result:
                self.db_manager.update_document_status(
                    document_id, 'failed', parsed_result['error']
                )
                return parsed_result
            
            # 6. 提取文本和表格
            text = '\n'.join(parsed_result.get('text', []))
            tables = parsed_result.get('tables', [])
            
            # 7. 处理图片（如果有）
            if 'images' in parsed_result:
                for image_info in parsed_result['images']:
                    # 处理图片中的文字
                    ocr_result = self.ocr_processor.ocr_image(
                        image_info['path']
                    )
                    if 'text' in ocr_result:
                        text += '\n' + ocr_result['text']
            
            # 8. 提取结构化信息
            key_patterns = {
                'project_name': ['项目名称', 'Project Name'],
                'report_date': ['报告日期', 'Report Date'],
                'energy_consumption': ['能源消耗', 'Energy Consumption'],
                'emissions': ['排放量', 'Emissions'],
                'recommendations': ['建议', 'Recommendations']
            }
            
            structured_data = self.extractor.extract_structured_data(
                text, tables, key_patterns
            )
            
            # 9. 存储提取的数据
            for entity_type, entities in structured_data['entities'].items():
                for entity in entities:
                    self.db_manager.insert_extracted_data(
                        document_id, 'entity', entity_type, entity
                    )
            
            for key, value in structured_data['key_values'].items():
                self.db_manager.insert_extracted_data(
                    document_id, 'key_value', key, value
                )
            
            for i, table in enumerate(tables):
                self.db_manager.insert_table(
                    document_id, 1, i, table
                )
            
            # 10. 更新状态为完成
            self.db_manager.update_document_status(document_id, 'completed')
            
            # 11. 缓存结果
            result = {
                'document_id': document_id,
                'text': text,
                'structured_data': structured_data,
                'tables': tables
            }
            self.db_manager.cache_result(
                f'document:{document_id}', result
            )
            
            # 12. 更新元数据
            self.metadata_manager.update_metadata(
                document_id, {'status': 'completed'}
            )
            
            return result
            
        except Exception as e:
            # 处理异常
            if document_id:
                self.db_manager.update_document_status(
                    document_id, 'failed', str(e)
                )
                self.metadata_manager.update_metadata(
                    document_id, {'status': 'failed', 'error': str(e)}
                )
            return {'error': str(e)}
    
    def get_processed_result(self, document_id):
        """获取处理结果"""
        # 先尝试从缓存获取
        cached_result = self.db_manager.get_cached_result(
            f'document:{document_id}'
        )
        if cached_result:
            return cached_result
        
        # 从数据库获取
        document = self.db_manager.get_document(document_id)
        if not document:
            return {'error': '文档不存在'}
        
        if document[6] != 'completed':  # status字段
            return {'error': f'文档状态：{document[6]}'}
        
        # 构建结果
        result = {
            'document_id': document_id,
            'filename': document[1],
            'file_path': document[2],
            'status': document[6],
            'extracted_data': [],
            'tables': []
        }
        
        # 获取提取的数据
        extracted_data = self.db_manager.get_extracted_data(document_id)
        for data in extracted_data:
            result['extracted_data'].append({
                'type': data[2],
                'key': data[3],
                'value': data[4],
                'confidence': data[5]
            })
        
        # TODO: 获取表格数据
        
        return result
    
    def close(self):
        """关闭系统"""
        self.db_manager.close()
```

### 2. RPA集成实现

#### RPA调用IDP服务

```python
import requests
import json
import os

class RPAClient:
    def __init__(self, idp_service_url):
        self.idp_service_url = idp_service_url
    
    def process_document(self, file_path):
        """调用IDP服务处理文档"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f'{self.idp_service_url}/process',
                    files=files
                )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'请求失败：{response.status_code}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_result(self, document_id):
        """获取处理结果"""
        try:
            response = requests.get(
                f'{self.idp_service_url}/result/{document_id}'
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'请求失败：{response.status_code}'}
        except Exception as e:
            return {'error': str(e)}
    
    def batch_process(self, directory):
        """批量处理目录中的文档"""
        results = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                result = self.process_document(file_path)
                results.append({
                    'filename': filename,
                    'result': result
                })
        return results
```

#### RPA流程示例

```python
# 能源清洁审核报告自动化流程

def energy_audit_report_automation():
    # 初始化RPA客户端
    rpa_client = RPAClient('http://localhost:5000')
    
    # 1. 收集文档
    source_folder = 'C:\\EnergyAudit\\SourceDocuments'
    results = rpa_client.batch_process(source_folder)
    
    # 2. 处理结果
    for item in results:
        if 'error' not in item['result']:
            document_id = item['result']['document_id']
            structured_data = item['result']['structured_data']
            
            # 3. 提取关键信息
            project_name = structured_data['key_values'].get('project_name', '')
            report_date = structured_data['key_values'].get('report_date', '')
            energy_consumption = structured_data['key_values'].get('energy_consumption', '')
            emissions = structured_data['key_values'].get('emissions', '')
            
            # 4. 填入报告模板
            template_path = 'C:\\EnergyAudit\\Templates\\AuditReportTemplate.docx'
            output_path = f'C:\\EnergyAudit\\Output\\{project_name}_{report_date}.docx'
            
            # 这里可以使用python-docx等库填充模板
            fill_report_template(
                template_path, 
                output_path, 
                {
                    'project_name': project_name,
                    'report_date': report_date,
                    'energy_consumption': energy_consumption,
                    'emissions': emissions,
                    # 其他字段...
                }
            )
            
            # 5. 归档原始文档
            archive_folder = 'C:\\EnergyAudit\\Archive'
            os.makedirs(archive_folder, exist_ok=True)
            os.rename(
                os.path.join(source_folder, item['filename']),
                os.path.join(archive_folder, item['filename'])
            )
    
    print('能源清洁审核报告自动化流程完成')

def fill_report_template(template_path, output_path, data):
    """填充报告模板"""
    # 使用python-docx填充模板
    # 这里需要根据实际模板结构实现
    pass
```

## 部署与集成最佳实践

### 1. 系统部署架构

```
部署架构
├── 前端层
│   ├── Web界面
│   └── API接口
├── 应用层
│   ├── IDP服务
│   └── RPA机器人
├── 数据层
│   ├── 数据库
│   ├── 缓存
│   └── 存储
└── 基础设施层
    ├── 服务器
    ├── 网络
    └── 安全
```

### 2. Docker容器化部署

#### Docker Compose配置

```yaml
version: '3.8'
services:
  idp-service:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    environment:
      - DATABASE_URL=mysql://user:password@db:3306/idp
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=root
      - MYSQL_DATABASE=idp
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql-data:/var/lib/mysql
  
  redis:
    image: redis:6.0
    volumes:
      - redis-data:/data
  
  rpa-worker:
    build: ./rpa
    volumes:
      - ./rpa/data:/app/data
    environment:
      - IDP_SERVICE_URL=http://idp-service:5000
    depends_on:
      - idp-service

volumes:
  mysql-data:
  redis-data:
```

### 3. API接口设计

#### Flask API示例

```python
from flask import Flask, request, jsonify
from comprehensive_idp_system import ComprehensiveIDPSystem
import config

app = Flask(__name__)
idp_system = ComprehensiveIDPSystem(config)

@app.route('/process', methods=['POST'])
def process_document():
    """处理文档"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    # 保存文件
    import os
    upload_dir = 'uploads'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)
    
    # 处理文档
    result = idp_system.process_document(file_path)
    
    return jsonify(result)

@app.route('/result/<int:document_id>', methods=['GET'])
def get_result(document_id):
    """获取处理结果"""
    result = idp_system.get_processed_result(document_id)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## 性能优化与监控

### 1. 性能优化策略

1. **并行处理**
   - 使用多线程或多进程处理文档
   - 利用消息队列进行任务分发
2. **缓存优化**
   - 缓存常用模型和处理结果
   - 使用Redis进行缓存管理
3. **资源管理**
   - 合理分配系统资源
   - 监控资源使用情况
4. **批处理优化**
   - 批量处理文档，减少系统开销
   - 优化数据库查询

### 2. 监控与日志

1. **系统监控**
   - 监控CPU、内存、磁盘使用情况
   - 监控处理队列和任务状态
2. **日志管理**
   - 结构化日志记录
   - 错误日志分析
   - 性能指标记录
3. **告警机制**
   - 设置性能阈值告警
   - 错误率监控告警

## 思考与反馈

1. 你对IDP处理层和数据层的实现有了更清晰的理解吗？
2. 你认为在你的能源清洁审核报告项目中，如何应用这些技术？
3. 你对IDP与RPA集成的具体实现有什么疑问？
4. 你希望在后续学习中了解IDP的哪些具体技术细节或应用场景？

````markdown
反馈：
我有疑问IDP如何实现对文档的处理，包括解析、OCR识别、表格识别、结构化数据提取等。  到目前为止好像只实现了解析和OCR识别，其他功能还没有实现。
``OCR识别也一直失败，不知道原因。
```特别是结构化数据的提取和表格识别好像比较重要，这样才能提取文档中的特定文字和表格数据。
```
````

