from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.event import MessageChain
import astrbot.api.message_components as Comp
#from astrbot.core.star.context import Context
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import os
import json
from data.plugins.astrbot_plugin_SpeechStatistic.Visualization import Visualization

'''TODO 1.已开启群组的数据持久化 DONE
        2.优化轮询逻辑(reverseOrder = False#新->旧,轮询根据message_id进行不重复查询,提高速度和效率)***
        3.调度器没有任务后关闭调度器 DONE



''' 



@register('1','1','1','1')
class Speach_Statistics(Star):
    def __init__(self,context:Context):
        super().__init__(context)
        self.dingshi_send = AsyncIOScheduler()
        self.dingshi_send.start()
        self.curdir = os.path.dirname(os.path.abspath(__file__))
        # 避免在平台尚未加载时就恢复任务，改为在 on_platform_loaded 钩子中恢复
        self._restored = False

    @filter.on_platform_loaded()
    async def _restore_jobs_after_platform_ready(self):
        """平台加载完成后恢复已开启群组的定时任务"""
        if self._restored:
            return
        json_path = os.path.join(self.curdir, '已开启群组.json')
        if os.path.exists(json_path):
            with open(json_path, 'r+', encoding='utf-8') as j:
                try:
                    group_dict = json.load(j) or {}
                except json.JSONDecodeError:
                    logger.info('已开启群组.json 解析失败或为空，将忽略并重新生成。')
                    group_dict = {}
                for s_gid, value in group_dict.items():
                    # value: [uhour, uminute, gid, platform_name, platform_id]
                    if not isinstance(value, list) or len(value) < 5:
                        logger.warning(f'记录格式异常，跳过: {s_gid} -> {value}')
                        continue
                    self.AddJob(
                        s_gid,
                        value[0],
                        value[1],
                        value[2],
                        value[3],
                        value[4],
                    )
        self._restored = True
    

    async def get_history_msg(self,platform_name:str,uhour:int,uminute:int ,gid:int,client,date):
        if platform_name == "aiocqhttp":
            from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
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
                


    async def send_image(self,platform_name,s_gid:str,gid,uhour:int,uminute:int,platform_id:str):
        logger.info(f'{s_gid}')
        # 运行时根据 platform_id 获取平台实例与客户端，避免持久保存失效对象
        inst = self.context.get_platform_inst(platform_id)
        if not inst:
            logger.info(f'未找到平台实例: {platform_id}，本次任务跳过')
            return 0
        client = inst.get_client()
        date = datetime.datetime.now().date()
        try:
           gdict = await self.get_history_msg(platform_name,uhour,uminute,gid,client,date)
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
        
    def AddJob(self,s_gid,uhour,uminute,gid,platform_name,platform_id:str):
        self.dingshi_send.add_job(self.send_image,
                                'cron',
                                hour = uhour,
                                minute = uminute,
                                second = 0,
                                args = [platform_name,s_gid,gid,uhour,uminute,platform_id],
                                id = s_gid
                                )       

    @filter.command("开启记录任务")
    async def record(self,event: AstrMessageEvent,uhour:int,uminute:int):
        platform_id = event.get_platform_id()
        platform_name = event.get_platform_name() #str
        s_gid = event.unified_msg_origin#str
        gid = event.message_obj.group_id#str
        if os.path.exists(os.path.join(self.curdir,'已开启群组.json')):
            with open(os.path.join(self.curdir,'已开启群组.json'),'r+', encoding='utf-8') as j:
                try:
                    OpenedGroup = json.load(j) or {}
                except json.JSONDecodeError:
                    OpenedGroup = {}
                OpenedGroup[s_gid] = [uhour,uminute,gid,platform_name,platform_id]
                j.seek(0)
                j.truncate()
                json.dump(OpenedGroup,j, ensure_ascii=False)
        else:
            with open(os.path.join(self.curdir,'已开启群组.json'),'w+', encoding='utf-8') as j:
                json.dump({s_gid:[uhour,uminute,gid,platform_name,platform_id]},j, ensure_ascii=False)
        # 只传 platform_id，运行时再获取 client
        self.AddJob(s_gid,uhour,uminute,gid,platform_name,platform_id)
        yield event.plain_result('记录任务开启成功')
        yield event.plain_result(f'将在{uhour}:{uminute}进行发言总结')
        if not self.dingshi_send.running:
            self.dingshi_send.start()
    @filter.command('关闭记录任务')
    async def record_off(self,event:AstrMessageEvent):
        s_gid = event.unified_msg_origin
        try:
            self.dingshi_send.remove_job(s_gid)
            with open(os.path.join(self.curdir,'已开启群组.json'),'r+', encoding='utf-8') as j:
                try:
                    Tempdict = json.load(j) or {}
                except json.JSONDecodeError:
                    Tempdict = {}
                if s_gid in Tempdict:
                    del Tempdict[s_gid]
                j.seek(0)
                j.truncate()
                json.dump(Tempdict,j, ensure_ascii=False)
            yield event.plain_result('关闭记录任务成功')
        except Exception as e:
            yield event.plain_result(f'移除失败:{e}')
        finally:
            if not self.dingshi_send.get_jobs():
                self.dingshi_send.shutdown()
                yield event.plain_result('检测到无正在记录的任务，调度器已关闭')














