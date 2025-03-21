from main import *
from sample_skill import *
#测试(假设这里在某个事件中)
hero=Char(name="测试主角",team=1,hp=100)
sk=Fireball(owner=hero)
enemy=Char(name="一个小怪",team=2,hp=250)
sk2=Skip(owner=enemy)
sk3=Fireball(owner=enemy)
msgm=Msgmanager()
msgm.register(sk)
msgm.register(sk2)
msgm.register(sk3)
#某时刻，小怪打了一下主角，于是事件发送消息给管理器
# 创建消息时使用规范格式
msg = GameMessage(
    exc=enemy,
    acp=hero,
    typ=DAMAGE,
    val=7,
    spe={},  
    mng=msgm
)

msgm.acceptmsg(msg)
try:
    msgm.exect()
except Exception as e:
    print(f'发生错误：{str(e)}')
finally:
    print(f'统计:主角受伤{100-hero.hp},小怪受伤{250-enemy.hp}')