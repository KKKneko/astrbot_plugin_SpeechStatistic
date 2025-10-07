from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.event import MessageChain
import astrbot.api.message_components as Comp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import os

def Visualization(name,data):
    # 使用非交互后端，避免服务器/容器无显示导致渲染失败（需在导入 pyplot 前设置）
    import matplotlib
    try:
        matplotlib.use("Agg", force=True)
    except Exception:
        pass
    import matplotlib.pyplot as plt
    try:
        # 如果在其它地方已导入 pyplot，尝试切换到 Agg
        if 'agg' not in matplotlib.get_backend().lower():
            plt.switch_backend('Agg')
    except Exception as _:
        pass
    from matplotlib.font_manager import FontProperties
    from matplotlib import font_manager as fm
    import platform

    # 智能字体配置 - 根据操作系统和可用字体
    system = platform.system()
    if system == 'Linux':
        # Linux：优先加载插件自带字体，保证即使系统未安装中文字体也能渲染
        preferred_fonts = []
        try:
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            local_font = os.path.join(plugin_dir, 'STXINGKA.TTF')

            def try_add_font(path):
                if os.path.exists(path):
                    fm.fontManager.addfont(path)
                    return FontProperties(fname=path).get_name()
                return None

            # 1) 插件随包字体
            stx_name = try_add_font(local_font)
            if stx_name:
                preferred_fonts.append(stx_name)

            # 2) 常见系统中文字体（按存在情况动态添加，便于统一渲染风格）
            candidates = [
                '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            ]
            for c in candidates:
                n = try_add_font(c)
                if n and n not in preferred_fonts:
                    preferred_fonts.append(n)
        except Exception as _:
            pass

        # 设置字体族：将已注册字体名称放在最前，并保留若干通用候选
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = preferred_fonts + [
            'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',
            'Source Han Sans SC', 'Noto Sans SC', 'Droid Sans Fallback',
            'DejaVu Sans', 'sans-serif'
        ]
        try:
            logger.info(f"Linux 字体优先级: {plt.rcParams['font.sans-serif']}")
        except Exception:
            pass

    elif system == 'Windows':
        # Windows 系统字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans', 'sans-serif']
    elif system == 'Darwin':  # macOS
        # macOS 系统字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Hiragino Sans GB', 'PingFang SC', 'DejaVu Sans', 'sans-serif']
    else:
        # 其他系统的通用配置
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
    
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    # 3. 定义你的原始数据，使用字典非常方便，键是名称，值是分数
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
    fig, ax = plt.subplots(figsize=(12, 7))

    #    第一个参数是 Y 轴的刻度标签 (玩家)
    #    第二个参数是每个条形的长度 (分数)
    #    color 设置了所有条形的颜色
    #    这个函数会返回一个包含所有条形图对象的列表，我们用 bars 变量接收它，后面要用
    bars = ax.barh(sorted_players, sorted_scores, color='skyblue', height=0.3)  # 调整条形厚度

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
            ha='left',     # 水平对齐方式：左对齐
            fontsize=20 
        )

    # 11. 设置图表标题，并可以指定字体大小和粗细
    ax.set_title('群发言统计排行', fontsize=30, fontweight='bold')

    # 12. 设置 X 轴和 Y 轴的标签
    ax.set_xlabel('发言数', fontsize=30)
    ax.set_ylabel('用户', fontsize=30)
    
    # 设置Y轴标签（sorted_players）的字体大小
    ax.tick_params(axis='y', labelsize=16)
    ax.tick_params(axis='x', labelsize=14)

    # 13. 优化坐标轴边框，让图表更简洁
    #     一个图表有四条边框(spines): top, bottom, left, right
    ax.spines['top'].set_visible(False)   # 隐藏顶部边框
    ax.spines['right'].set_visible(False) # 隐藏右侧边框

    # 14. 调整X轴的范围，给右侧的数值标签留出足够的空间
    #     否则，最高的得分 "98" 可能会被截断
    ax.set_xlim(right=max(sorted_scores) * 1.1)  # 将X轴的右边界设置为最大分数的1.1倍

    # 15. 自动调整布局，防止标签等元素重叠或被遮挡
    plt.tight_layout()

    # 获取当前插件目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 创建图片保存目录
    images_dir = os.path.join(current_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # 构建完整的保存路径
    save_path = os.path.join(images_dir, name)
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()  # 关闭图形以释放内存



@register('1','1','1','1')
class Speach_Statistics(Star):
    def __init__(self,context:Context):
        super().__init__(context)
        self.dingshi_send = AsyncIOScheduler()
        self.dingshi_send.start()
    @filter.command('test')
    async def get_history_msg(self,event:AstrMessageEvent,uhour:int,uminute:int ,gid:int,client,date):
        if event.get_platform_name() == "aiocqhttp":
            from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
            assert isinstance(event, AiocqhttpMessageEvent)
            # 统一用日期对象
            if isinstance(date, int):
                date = datetime.datetime.now().date()

            userid_to_number = {}
            seen_ids = set()  # 新增：去重
            step = 50
            count = step

            while True:
                payloads = {
                    'group_id': gid,
                    'count': count,
                    'reverseOrder': True  # 旧->新（以是否已跨过零点为提前停止条件）
                }
                ret = await client.api.call_action('get_group_msg_history', **payloads)
                msgs = ret.get('messages', []) or []
                if not msgs:
                    logger.info(f'历史消息为空或接口无更多数据: {ret}')
                    return userid_to_number

                reached_older = False  # 只要看到“早于今天”的消息，就说明本页已覆盖到零点
                for r in msgs:
                    mid = r.get('message_id')  # OneBot v11 一般有 message_id
                    if mid in seen_ids:
                        continue
                    seen_ids.add(mid)

                    msg_dt = datetime.datetime.fromtimestamp(r['time']).date()
                    if msg_dt == date:
                        nickname = r.get('sender', {}).get('nickname') or str(r.get('user_id'))
                        uid = r.get('user_id')
                        cur = userid_to_number.get(nickname, [uid, 0])
                        userid_to_number[nickname] = [uid, cur[1] + 1]
                    elif msg_dt < date:
                        reached_older = True  # 已跨过零点，本页已包含今天的全部消息段
                        # 不立刻 break，保证把本页中所有“今天”的消息都统计完
                    else:
                        # msg_dt > date（跨时区等导致“未来”），忽略
                        pass

                if reached_older:
                    logger.info(f'成功获取历史消息:{userid_to_number}')
                    return userid_to_number

                count += step
                if count > 2000:
                    logger.info(f'超过最大拉取条数，提前返回: 统计={userid_to_number}')
                    return userid_to_number
                


    async def send_image(self,event,s_gid:str,gid,uhour:int,uminute:int,client):
        logger.info(f'{s_gid}')
        date = datetime.datetime.now().date()
        try:
           gdict = await self.get_history_msg(event,uhour,uminute,gid,client,date)
        except Exception as e:
            logger.info(f'{e}')
            return 0
        import os
        curdir = os.path.dirname(os.path.abspath(__file__))
        try:
            Visualization(f'{gid}.png',gdict)
        except Exception as e:
            logger.info(f'{e}')
        logger.info('成功生成可视化数据')
        
        # 修改图片路径，指向 images 文件夹
        image_path = os.path.join(curdir, 'images', f'{gid}.png')
        self.message_chain = MessageChain().file_image(image_path)
        logger.info(f'{s_gid}')
        await self.context.send_message(s_gid,self.message_chain)
        
        


    @filter.command("开启记录任务")
    async def record(self,event: AstrMessageEvent,uhour:int,uminute:int):
        client = event.bot 
        s_gid = event.unified_msg_origin
        gid = event.message_obj.group_id
        self.dingshi_send.add_job(self.send_image,
                                  'cron',
                                  hour = uhour,
                                  minute = uminute,
                                  second = 0,
                                  args = [event,s_gid,gid,uhour,uminute,client],
                                  id = s_gid
                                  )
        yield event.plain_result('记录任务开启成功')
        yield event.plain_result(f'将在{uhour}:{uminute}进行发言总结')

    @filter.command('关闭记录任务')
    async def record_off(self,event:AstrMessageEvent):
        s_gid = event.unified_msg_origin
        self.dingshi_send.remove_job(s_gid)
        if self.dingshi_send.get_job(s_gid):
            yield event.plain_result('移除任务失败')
        else:
            yield event.plain_result('移除任务成功')













