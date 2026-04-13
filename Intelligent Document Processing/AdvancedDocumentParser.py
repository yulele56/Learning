import docx
import PyPDF2
from tika import parser
import os
import cv2
import numpy as np

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
            
            # 提取图片
            # 这里使用python-docx的图片提取功能
            # 注意：这需要额外的处理
            
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
            
            # 集成Camelot提取表格
            try:
                import camelot
                tables = camelot.read_pdf(file_path, pages='all', flavor='lattice')
                for table in tables:
                    content['tables'].append(table.df.to_dict('records'))
            except ImportError:
                pass  # 如果没有安装Camelot，跳过表格提取
            
            return content
        except Exception as e:
            return {'error': str(e)}
    
    def parse_image(self, file_path):
        """解析图片文档"""
        try:
            # 读取图像
            image = cv2.imread(file_path)
            if image is None:
                return {'error': '无法读取图像'}
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 简单的图像信息
            return {
                'text': [],
                'image_info': {
                    'width': image.shape[1],
                    'height': image.shape[0],
                    'channels': image.shape[2] if len(image.shape) == 3 else 1
                }
            }
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