"""
王者荣耀战力查询插件

查询王者荣耀英雄战力
"""

import aiohttp
from loguru import logger
import tomllib
from utils.decorators import *
from utils.plugin_base import PluginBase
from WechatAPI import WechatAPIClient


class WangZhePowerPlugin(PluginBase):
    """王者荣耀战力查询插件类"""
    description = "王者荣耀战力查询插件：使用'查战力[平台类型][英雄名]'来查询英雄战力"
    author = "鸿菇"
    version = "1.0.0"

    # API地址
    API_URL = "https://api.dragonlongzhu.cn//api/wzcx_zhanli.php"

    # 平台映射关系
    PLATFORM_MAP = {
        "安卓微信": "wx",
        "安卓QQ": "qq",
        "ios微信": "ios_wx",
        "iosQQ": "ios_qq"
    }

    def __init__(self):
        super().__init__()
        try:
            with open("plugins/WangZhePowerPlugin/config.toml", "rb") as f:
                config = tomllib.load(f)
            plugin_config = config["WangZhePowerPlugin"]
            self.enable = plugin_config["enable"]
            logger.info(f"[WangZhePowerPlugin] 插件初始化完成")
        except Exception as e:
            logger.error(f"[WangZhePowerPlugin] 加载配置文件失败: {e}")
            self.enable = False

    @on_text_message(priority=50)
    async def handle_text(self, bot: WechatAPIClient, message: dict):
        """处理文本消息"""
        if not self.enable:
            return True  # 插件未启用，允许后续插件处理

        content = message.get("Content", "").strip()
        from_wxid = message.get("FromWxid", "")
        
        if not content or not from_wxid:
            return True  # 消息内容或发送者ID为空，允许后续插件处理

        # 处理查战力请求
        if content.startswith("查战力"):
            logger.info(f"[WangZhePowerPlugin] 收到战力查询请求: {content}")
            
            # 解析平台和英雄名
            platform_type = None
            hero_name = None
            
            for platform in self.PLATFORM_MAP.keys():
                if platform in content:
                    platform_type = self.PLATFORM_MAP[platform]
                    hero_name = content.replace(f"查战力{platform}", "").strip()
                    break
                    
            if not platform_type or not hero_name:
                platforms = "、".join(self.PLATFORM_MAP.keys())
                await bot.send_text_message(from_wxid, f"格式错误，请使用：查战力[平台类型][英雄名]\n支持的平台：{platforms}")
                return False  # 阻止后续插件处理
            
            result = await self.query_power(hero_name, platform_type)
            if result:
                await bot.send_text_message(from_wxid, result)
            else:
                await bot.send_text_message(from_wxid, f"未找到英雄 {hero_name} 的战力信息，请确认英雄名称是否正确")
            return False  # 阻止后续插件处理
            
        # 处理帮助请求
        if content == "王者战力" or content == "查战力":
            platforms = "、".join(self.PLATFORM_MAP.keys())
            help_text = f"使用 '查战力[平台类型][英雄名]' 来查询英雄战力\n支持的平台类型：{platforms}\n示例：查战力安卓QQ妲己"
            await bot.send_text_message(from_wxid, help_text)
            return False  # 阻止后续插件处理
        
        return True  # 不是战力查询请求，允许后续插件处理

    async def query_power(self, hero_name, platform_type):
        """查询英雄战力
        
        Args:
            hero_name: 英雄名称
            platform_type: 平台类型
            
        Returns:
            str: 返回战力查询结果，失败返回None
        """
        try:
            params = {
                'msg': hero_name,
                'type': platform_type,
                'kind': '',
                'moban': ''
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.API_URL, params=params, timeout=10) as response:
                    if response.status == 200:
                        result = await response.text()
                        result = result.strip()
                        if result and "没有找到" not in result:
                            return result
                        else:
                            logger.warning(f"[WangZhePowerPlugin] 未找到英雄: {hero_name}")
                            return None
                    else:
                        logger.error(f"[WangZhePowerPlugin] API请求失败，状态码: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"[WangZhePowerPlugin] 查询战力异常: {e}")
            return None


def get_plugin_class():
    return WangZhePowerPlugin