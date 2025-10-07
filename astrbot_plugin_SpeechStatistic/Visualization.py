def Visualization(name,data):
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties

    # 指定项目下的字体文件路径
    font_path = r'STXINGKA.TTF'
    my_font = FontProperties(fname=font_path)

    plt.rcParams['font.sans-serif'] = [my_font.get_name()]  # 使用自定义字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    # 3. 定义你的原始数据，使用字典非常方便，键是名称，值是分数
    '''
    data = {
        '李拜天': ['08814721424',88],
        '玩家B': ['id2',92],
        '玩家C': ['id3',75],
        '玩家D': ['id4',98],
        '玩家E': ['id5',85],
    }
'''
    # 4. 对数据进行排序（这是最关键的一步）
    #    sorted() 函数可以对任何可迭代对象进行排序
    #    data.items() 会将字典转换为 [('玩家A', 88), ('玩家B', 92), ...] 这样的元组列表
    #    key=lambda item: item[1] 告诉 sorted() 函数，请按照每个元组的第二个元素 (item[1]，也就是分数) 来排序
    #    默认是升序，结果是从小到大排列
    sorted_data = sorted(data.items(), key=lambda item: item[1][1])

    # 5. 将排序后的数据拆分成两个独立的列表：玩家列表和分数列表
    #    因为 Matplotlib 的绘图函数通常需要接收这样的独立列表
    #    这是 Python 的列表推导式，高效地从 sorted_data 中提取数据
    sorted_players = [f'{item[0]} ID:{item[1][0]}' for item in sorted_data]
    sorted_scores = [item[1][1] for item in sorted_data]

    # 6. 创建一个图形(figure)和一组坐标轴(axes)
    #    fig 是整个图片窗口，ax 是图片里的那块绘图区域
    #    这是官方推荐的绘图方式，因为它让你能更精细地控制图表的每一个部分
    #    figsize=(10, 6) 设置了图片的大小，单位是英寸
    fig, ax = plt.subplots(figsize=(10, 6))

    #    第一个参数是 Y 轴的刻度标签 (玩家)
    #    第二个参数是每个条形的长度 (分数)
    #    color 设置了所有条形的颜色
    #    这个函数会返回一个包含所有条形图对象的列表，我们用 bars 变量接收它，后面要用
    bars = ax.barh(sorted_players, sorted_scores, color='skyblue', height=0.4)  # 调整条形厚度

    # 8. 遍历我们刚刚创建的每一个条形图对象 (bar)
    for bar in bars:
        # 9. 获取当前条形的宽度，也就是它的数据值 (分数)
        width = bar.get_width()
        
        # 10. 在条形的右侧指定位置添加文本
        #     ax.text() 函数用于在图表的任意位置添加文字
        ax.text(
            x=width + 1,  # X坐标：在条形末端再往右一点(+1)的位置，留出空隙
            y=bar.get_y() + bar.get_height() / 2,  # Y坐标：在条形垂直方向的中心位置
                                                # bar.get_y()是条形下边缘y坐标，bar.get_height()是条形高度
            s=f'{width}', # 要显示的文本内容，这里就是分数
            va='center',  # 垂直对齐方式：居中对齐
            ha='left'     # 水平对齐方式：左对齐
        )

    # 11. 设置图表标题，并可以指定字体大小和粗细
    ax.set_title('游戏得分排行榜', fontsize=18, fontweight='bold')

    # 12. 设置 X 轴和 Y 轴的标签
    ax.set_xlabel('得分', fontsize=12)
    ax.set_ylabel('玩家', fontsize=12)

    # 13. 优化坐标轴边框，让图表更简洁
    #     一个图表有四条边框(spines): top, bottom, left, right
    ax.spines['top'].set_visible(False)   # 隐藏顶部边框
    ax.spines['right'].set_visible(False) # 隐藏右侧边框

    # 14. 调整X轴的范围，给右侧的数值标签留出足够的空间
    #     否则，最高的得分 "98" 可能会被截断
    ax.set_xlim(right=max(sorted_scores) * 1.1)  # 将X轴的右边界设置为最大分数的1.1倍

    # 15. 自动调整布局，防止标签等元素重叠或被遮挡
    plt.tight_layout()

    plt.savefig(name,dpi =300,bbox_inches = 'tight')
