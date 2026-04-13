import os
import json
from AdvancedDocumentParser import AdvancedDocumentParser as DocumentParser
from AdvancedOCRProcessor import AdvancedOCRProcessor as OCRProcessor
from AdvancedTableRecognizer import AdvancedTableRecognizer as TableRecognizer
from AdvancedInformationExtractor import AdvancedInformationExtractor as InformationExtractor
from datetime import datetime

class ComprehensiveIDPSystem:
    def __init__(self, config):
        # 初始化各个模块
        self.parser = DocumentParser()
        self.ocr_processor = OCRProcessor(config.get('tesseract_path'))
        self.table_recognizer = TableRecognizer()
        self.extractor = InformationExtractor()
        
        # 初始化输出目录
        self.output_dir = config.get('output_dir', 'output')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_document(self, file_path):
        """处理文档的完整流程"""
        try:
            # 1. 检查文件是否存在
            if not os.path.exists(file_path):
                return {'error': '文件不存在'}
            
            # 2. 提取文件信息
            filename = os.path.basename(file_path)
            filetype = os.path.splitext(filename)[1].lower()
            size = os.path.getsize(file_path)
            
            # 3. 解析文档
            parsed_result = self.parser.parse_document(file_path)
            if 'error' in parsed_result:
                return parsed_result
            
            # 4. 提取文本、标题、正文和表格
            text = '\n'.join(parsed_result.get('text', []))
            headings = parsed_result.get('headings', [])
            body_text = parsed_result.get('body_text', [])
            tables = parsed_result.get('tables', [])
            
            # 5. 处理图片（如果有）
            if filetype in ['.jpg', '.jpeg', '.png', '.bmp']:
                # 对图片进行OCR
                ocr_result = self.ocr_processor.ocr_image(file_path)
                if 'text' in ocr_result:
                    text = ocr_result['text']
            elif 'images' in parsed_result:
                for image_info in parsed_result['images']:
                    # 处理图片中的文字
                    if 'path' in image_info:
                        ocr_result = self.ocr_processor.ocr_image(
                            image_info['path']
                        )
                        if 'text' in ocr_result:
                            text += '\n' + ocr_result['text']
            
            # 6. 提取表格（如果是PDF）
            if filetype == '.pdf':
                table_result = self.table_recognizer.extract_tables_from_pdf(file_path)
                if not isinstance(table_result, dict) or 'error' not in table_result:
                    tables.extend(table_result)
            
            # 7. 提取结构化信息
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
            
            # 8. 生成结果
            result = {
                'filename': filename,
                'file_path': file_path,
                'file_type': filetype,
                'file_size': size,
                'processed_at': datetime.now().isoformat(),
                'text': text,
                'headings': headings,
                'body_text': body_text,
                'structured_data': structured_data,
                'tables': tables
            }
            
            # 9. 保存结果
            output_file = os.path.join(
                self.output_dir, 
                f"{os.path.splitext(filename)[0]}_result.json"
            )
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 10. 保存提取的文本
            text_output_file = os.path.join(
                self.output_dir, 
                f"{os.path.splitext(filename)[0]}_text.txt"
            )
            with open(text_output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # 11. 保存表格数据
            if tables:
                table_output_file = os.path.join(
                    self.output_dir, 
                    f"{os.path.splitext(filename)[0]}_tables.xlsx"
                )
                table_result = self.table_recognizer.save_tables_to_excel(tables, table_output_file)
                if isinstance(table_result, dict) and 'error' in table_result:
                    print(f"保存表格时出错: {table_result['error']}")
                else:
                    print(f"表格已保存到: {table_output_file}")
            
            return result
            
        except Exception as e:
            return {'error': str(e)}


if __name__ == "__main__":
    # 配置
    config = {
        'tesseract_path': r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        'output_dir': 'output'
    }
    
    # 创建IDP系统实例
    idp_system = ComprehensiveIDPSystem(config)
    
    # 处理文档
    document_path = "D:/能源评估/1.天泓电镀清洁生产审核资料收集清单.pdf"
    result = idp_system.process_document(document_path)
    
    if 'error' in result:
        print(f"处理失败: {result['error']}")
    else:
        print("处理成功！")
        print(f"提取的文本: {result['text'][:500]}")
        print(f"提取的标题数量: {len(result['headings'])}")
        if result['headings']:
            print("提取的标题:")
            for i, heading in enumerate(result['headings'][:5]):  # 只显示前5个标题
                print(f"  {i+1}. {heading['text']}")
            if len(result['headings']) > 5:
                print(f"  ... 等{len(result['headings'])-5}个标题")
        print(f"提取的结构化数据: {result['structured_data']}")
        print(f"提取的表格数量: {len(result['tables'])}")
        print(f"结果已保存到: {os.path.join(config['output_dir'], f"{os.path.splitext(os.path.basename(document_path))[0]}_result.json")}")