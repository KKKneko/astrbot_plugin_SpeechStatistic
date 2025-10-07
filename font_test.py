#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体测试脚本 - 用于诊断Linux服务器上的中文字体显示问题
"""

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import platform

def test_font_display():
    """测试中文字体显示"""
    print(f"操作系统: {platform.system()}")
    print(f"Python版本: {platform.python_version()}")
    print(f"Matplotlib版本: {matplotlib.__version__}")
    
    # 获取当前目录下的字体文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, 'STXINGKA.TTF')
    
    print(f"\n检查字体文件:")
    print(f"字体路径: {font_path}")
    print(f"文件存在: {os.path.exists(font_path)}")
    
    if os.path.exists(font_path):
        print(f"文件大小: {os.path.getsize(font_path)} bytes")
        print(f"文件权限: {oct(os.stat(font_path).st_mode)[-3:]}")
    
    # 测试可用字体
    print(f"\n可用的中文字体:")
    fonts = fm.findSystemFonts()
    chinese_fonts = []
    for font in fonts[:20]:  # 限制数量避免输出过多
        try:
            font_prop = fm.FontProperties(fname=font)
            font_name = font_prop.get_name()
            if any(char in font_name.lower() for char in ['chinese', 'sim', 'hei', 'kai', 'song']):
                chinese_fonts.append(font)
                print(f"  {font_name}: {font}")
        except:
            continue
    
    if not chinese_fonts:
        print("  未找到明显的中文字体")
    
    # 创建测试图表
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 测试数据
    test_data = {
        '张三': ['123456', 100],
        '李四': ['234567', 85],
        '王五': ['345678', 92],
        '赵六': ['456789', 78]
    }
    
    # 尝试不同的字体设置方法
    font_configs = [
        ("自定义字体文件", font_path if os.path.exists(font_path) else None),
        ("SimHei", "SimHei"),
        ("DejaVu Sans", "DejaVu Sans"),
        ("默认字体", None)
    ]
    
    for i, (config_name, font_setting) in enumerate(font_configs):
        try:
            plt.clf()  # 清除之前的图
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if font_setting and os.path.exists(font_setting):
                # 使用字体文件
                font_prop = fm.FontProperties(fname=font_setting)
                plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
            elif font_setting:
                # 使用字体名称
                plt.rcParams['font.sans-serif'] = [font_setting]
            else:
                # 使用默认设置
                plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
            
            plt.rcParams['axes.unicode_minus'] = False
            
            # 绘制测试图表
            names = [f"{name} ID:{data[0]}" for name, data in test_data.items()]
            values = [data[1] for data in test_data.values()]
            
            bars = ax.barh(names, values, color='lightblue')
            ax.set_title(f'中文字体测试 - {config_name}', fontsize=16)
            ax.set_xlabel('数值', fontsize=14)
            ax.set_ylabel('用户名', fontsize=14)
            
            # 保存测试图片
            output_path = os.path.join(current_dir, f'font_test_{i}_{config_name.replace(" ", "_")}.png')
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"\n✓ {config_name} 测试成功，保存为: {output_path}")
            
        except Exception as e:
            print(f"\n✗ {config_name} 测试失败: {e}")
            plt.close()
    
    print(f"\n字体测试完成！请检查生成的图片文件中中文显示是否正常。")

if __name__ == "__main__":
    test_font_display()