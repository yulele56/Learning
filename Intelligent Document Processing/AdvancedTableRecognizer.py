import camelot
import pandas as pd
import cv2
import numpy as np
import os
import tempfile
import shutil

class AdvancedTableRecognizer:
    def __init__(self):
        pass
    
    def extract_tables_from_pdf(self, pdf_path, method='lattice'):
        """从PDF中提取表格"""
        try:
            # 检查文件是否存在
            if not os.path.exists(pdf_path):
                return {'error': 'PDF文件不存在'}
            
            # 创建自定义临时目录
            temp_dir = tempfile.mkdtemp(prefix='camelot_')
            
            try:
                # 尝试多次提取，处理文件锁定问题
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        # 使用camelot提取表格
                        tables = camelot.read_pdf(
                            pdf_path, 
                            pages='all',
                            flavor=method,
                            tempdir=temp_dir
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
                    except PermissionError as e:
                        if attempt < max_attempts - 1:
                            import time
                            time.sleep(1)  # 等待1秒后重试
                            continue
                        else:
                            return {'error': f'文件访问错误: {str(e)}'}
                    except Exception as e:
                        return {'error': str(e)}
            finally:
                # 清理临时目录
                if os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception as e:
                        print(f"清理临时目录失败: {str(e)}")
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
            # 检查文件是否存在
            if not os.path.exists(image_path):
                return {'error': '图像文件不存在'}
            
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
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 检查tables是否为空
            if not tables:
                return {'error': '表格数据为空'}
            
            # 过滤有效的表格数据
            valid_tables = []
            for table in tables:
                if isinstance(table, dict) and 'data' in table and table['data']:
                    valid_tables.append(table)
            
            if not valid_tables:
                return {'error': '没有有效的表格数据'}
            
            # 创建ExcelWriter
            try:
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    for i, table in enumerate(valid_tables):
                        try:
                            # 确保data是列表
                            if isinstance(table['data'], list):
                                # 检查列表是否为空
                                if not table['data']:
                                    continue
                                
                                # 检查第一个元素是否为字典
                                if isinstance(table['data'][0], dict):
                                    df = pd.DataFrame(table['data'])
                                else:
                                    # 尝试将其他格式转换为DataFrame
                                    df = pd.DataFrame(table['data'])
                                
                                # 确保DataFrame不为空
                                if not df.empty:
                                    sheet_name = f'Table_{i+1}_Page_{table.get("page", "N/A")}'
                                    # 确保sheet名称不超过31个字符
                                    sheet_name = sheet_name[:31]
                                    # 确保sheet名称有效
                                    sheet_name = sheet_name.replace('/', '_').replace('\\', '_')
                                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                        except Exception as e:
                            print(f"处理表格 {i+1} 时出错: {str(e)}")
                            continue
            except Exception as e:
                # 尝试使用不同的引擎
                try:
                    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                        for i, table in enumerate(valid_tables):
                            try:
                                if isinstance(table['data'], list) and table['data']:
                                    if isinstance(table['data'][0], dict):
                                        df = pd.DataFrame(table['data'])
                                    else:
                                        df = pd.DataFrame(table['data'])
                                    
                                    if not df.empty:
                                        sheet_name = f'Table_{i+1}_Page_{table.get("page", "N/A")}'
                                        sheet_name = sheet_name[:31]
                                        sheet_name = sheet_name.replace('/', '_').replace('\\', '_')
                                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                            except Exception as e:
                                print(f"处理表格 {i+1} 时出错: {str(e)}")
                                continue
                except Exception as e:
                    return {'error': f'创建Excel文件失败: {str(e)}'}
            
            # 检查文件是否生成
            if not os.path.exists(output_path):
                return {'error': 'Excel文件未生成'}
            
            # 检查文件大小
            if os.path.getsize(output_path) < 100:
                return {'error': 'Excel文件可能损坏（文件大小过小）'}
            
            return True
        except Exception as e:
            print(f"保存表格时出错: {str(e)}")
            return {'error': str(e)}