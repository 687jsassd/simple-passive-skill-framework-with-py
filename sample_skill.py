from main import *
class Fireball(Skill):
    def __init__(self,owner=None):
        super().__init__(name='被动火球术(受到伤害时，如果伤害来源为敌人，则自己回复9hp,对伤害来源释放火球扣除10hp，cd6事件)',owner=owner,reg_type='Fireball')
        self.cd=0
    
    def type_effect(self,msg:GameMessage):
        '''技能事件效果'''
        print(f'[Fireball]{self.owner}的Fireball技能发动！')
        if msg.exc:
            msg.exc.hp+=9
            print(f'执行者{msg.exc}回复9hp！ 剩余hp:{msg.exc.hp}')
        if msg.acp:
            msg.acp.hp-=10
            print(f'目标{msg.acp}扣除10hp！ 剩余hp:{msg.acp.hp}')
        print('[Fireball]技能发动完毕！')
        
        
    
    def update(self, msg: GameMessage):
        self.cd-=1
        # 使用模式匹配语法（Python 3.10+）
        match msg:
            case GameMessage(
                exc=attacker,
                acp=defender,
                typ=DAMAGE,
                val=dmg_val,
                spe=spec,
                mng=mng
            ) if defender == self.owner and defender and attacker and attacker.team != defender.team and self.cd<=0:
                print(f'{self.owner}的被动火球术将会触发！')
                new_msg = GameMessage(
                    exc=self.owner,
                    acp=attacker,
                    typ='Fireball',
                    val=1,
                    spe={},
                    mng=mng
                )
                mng.acceptmsgp(new_msg)
                self.cd=6
                

class Skip(Skill):
    def __init__(self,owner=None):
        super().__init__(name='跳过(受到伤害时，跳过下一个事件,cd6个事件)',owner=owner)
        self.cd=0
    def update(self, msg: GameMessage):
        self.cd-=1
        # 使用模式匹配语法（Python 3.10+）
        match msg:
            case GameMessage(
                exc=attacker,
                acp=defender,
                typ=DAMAGE,
                val=dmg_val,
                spe=spec,
                mng=mng
            ) if defender == self.owner and self.cd<=0:
                print(f'{self.owner}的被动跳过将会触发！')
                new_msg = GameMessage(
                    exc=self.owner,
                    acp=attacker,
                    typ=COMMAND_SKIP,
                    val=1,
                    spe=spec,
                    mng=mng
                )
                mng.acceptmsgp(new_msg)
                self.cd=6