import cv2
import pytesseract
from easyocr import Reader
import numpy as np
import os

class AdvancedOCRProcessor:
    def __init__(self, tesseract_path=None):
        # 配置Tesseract路径
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # 尝试初始化EasyOCR
        try:
            self.reader = Reader(['ch_sim', 'en'], gpu=False)
            self.use_easyocr = True
        except Exception as e:
            print(f"EasyOCR初始化失败，将使用Tesseract: {str(e)}")
            self.use_easyocr = False
    
    def preprocess_image(self, image):
        """增强版图像预处理"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 去噪
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # 对比度增强
        alpha = 1.5  # 对比度增益
        beta = 0     # 亮度增益
        enhanced = cv2.convertScaleAbs(denoised, alpha=alpha, beta=beta)
        
        # 自适应阈值二值化
        thresh = cv2.adaptiveThreshold(
            enhanced, 255, 
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
            # 检查文件是否存在
            if not os.path.exists(image_path):
                return {'error': '图像文件不存在'}
            
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
            # 检查文件是否存在
            if not os.path.exists(image_path):
                return {'error': '图像文件不存在'}
            
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
    
    def ocr_image(self, image_path, engine='auto'):
        """统一OCR接口"""
        # 检查文件是否存在
        if not os.path.exists(image_path):
            return {'error': '图像文件不存在'}
        
        # 自动选择引擎
        if engine == 'auto':
            if self.use_easyocr:
                result = self.ocr_with_easyocr(image_path)
                # 如果EasyOCR失败，尝试Tesseract
                if 'error' in result:
                    return self.ocr_with_tesseract(image_path)
                return result
            else:
                return self.ocr_with_tesseract(image_path)
        elif engine == 'tesseract':
            return self.ocr_with_tesseract(image_path)
        elif engine == 'easyocr':
            return self.ocr_with_easyocr(image_path)
        else:
            return {'error': '不支持的OCR引擎'}