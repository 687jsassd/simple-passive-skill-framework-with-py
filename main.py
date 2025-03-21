#msg消息体格式:{exc:,acp:,typ:,val:,mng:,}分别表示执行者，接受者，类型，值，以及事件处理器对象。

import uuid,time
from collections import deque
from typing import Optional, Callable
#基本消息类型
DAMAGE = "dmg"
HEAL = "heal"
COMMAND_SKIP = 'command_skip'

# 使用数据类
from dataclasses import dataclass
@dataclass
class GameMessage:
    exc: Optional['Char']  #执行者，应为Char类的对象
    acp: Optional['Char']  #接受者
    typ: str  #事件类型
    val: int  #基本值
    spe: dict  #特殊值字典，用于拓展
    mng: 'Msgmanager'  #该消息归属的事件处理器
    
    def __post_init__(self):
        if not isinstance(self.spe,dict):
            self.spe={}
        if self.val<0:
            raise ValueError('事件值不能为负数')
        if not isinstance(self.typ,str):
            raise TypeError('消息类型必须为字符串')
        if not self.mng:
            raise ValueError('必须有指定的消息处理器')
        if not self.mng.handler:
            raise ValueError('消息处理器未绑定任何中心处理器')          
        if not self.mng.handler.is_reg(self.typ):
            raise ValueError('消息类型未在事件处理器注册')    
              
    @property
    def fingerprint(self):
        """生成唯一识别指纹"""
        return (
            self.typ,
            self.val,
            tuple(self.spe.items()),
            self.exc.uuid if self.exc else None,
            self.acp.uuid if self.acp else None,
            id(self.mng),    # 管理器实例标识
            )
   
#角色类
class Char:
    def __init__(self,name,team,hp=100):
        self.name=name
        self.team=team
        self.hp=hp
        self.uuid=uuid.uuid4()
    def __str__(self):
        return self.name
    def __hash__(self):
        return hash(self.uuid)
    def __eq__(self,other):
        return self.uuid==other.uuid
        
#中心事件处理器，统一处理基本事件如受伤，加血。
#角色和技能应该由这个处理器注册和统一管理。处理的对象仅限于已经被注册的对象。
class Handler:
    def __init__(self,father:Optional['Handler'] =None):
        #允许继承父管理器的值
        if father:
            self.chars=father.chars
            self.skills=father.skills
            self._registered_types=father._registered_types
            self.ev_handlers=father.ev_handlers
        else:    
            self.chars=[]
            self.skills=[]
            self._registered_types=set()
            self.ev_handlers = {}

    def register_type(self, msg_type: str, handler: Callable):
        '''
           注册新事件类型 并绑定其函数
           
           参数：msg_type:事件类型，handler:事件函数
           
           使用示例：
           def poison2(xxx):
               pass
           xxx.register_type('poison',poison2)
           
        '''
        if msg_type in self._registered_types:
            raise ValueError('已有该事件类型，不能重复注册。\n使用replace_type(msg_type,handler)以替换某事件类型的处理器;或者先移除后再重新注册.')  
        self.ev_handlers[msg_type] = handler
        self._registered_types.add(msg_type)
        print(f'已经注册{msg_type}的处理器')
        
    def remove_type(self,msg_type:str):
        '''
           移除已经注册的事件及其函数
           
           参数：msg_type:事件类型
           
           使用示例：
           xxx.remove_type('poison')
               
           注意：不建议移除核心消息类型如DAMAGE的函数，除非你知道这样做的后果。
        '''
        if msg_type in self._registered_types:
            self._registered_types.remove(msg_type)
            del self.ev_handlers[msg_type]
            print(f'已经移除{msg_type}的处理器')
        else:
            raise ValueError('事件类型未注册,不能删除.')    
             
    def replace_type(self,msg_type:str,handler:Callable):
        '''
           替换已经注册的事件的函数
           
           参数：msg_type:事件类型，handler:替换函数
           
           使用示例：
           def poison2(xxx):
               pass
           xxx.replace_type('poison',poison2)
               
           注意：不建议替换核心消息类型如DAMAGE的函数，除非你知道这样做的后果。
        '''
        if msg_type in self._registered_types:
            self.ev_handlers[msg_type] = handler
            print(f'已经替换{msg_type}的处理器')
        else:
            raise ValueError('事件类型未注册,不能替换')
    
            
    def handles(self,msg_type:str):
        '''
           装饰器模式注册事件
           区别于直接调用register_type,该方法提供了采用装饰器模式直接在定义函数时绑定其消息类型的方案。
           
           参数：msg_type:事件类型
           
           使用示例：
           @xxx.handles('poison')
           def poisondmg(xxxxxx):
               pass
               
           注意：如你有多个事件处理器，且没有继承关系，那么只使用装饰器来注册并不能覆盖到除了代码指定的事件处理器之外的其他事件处理器；因此建议在事件处理器少或者有继承关系的情况下使用。
        '''
        def decorator(func):
            self.register_type(msg_type,func)
            return func
        return decorator
    
    def is_reg(self,msg_type:str):
        '''
           判断是否已经注册了某个事件类型

           参数：msg_type:事件类型

           使用示例：
           xxx.is_reg('poison')
        '''
        return msg_type in self._registered_types
    
    def handle_message(self,msg:GameMessage):
        '''
           处理消息
           用于消息处理器调用，不建议单独使用。
        
           参数：msg:消息体         
        '''
        handler=self.ev_handlers.get(msg.typ)
        if handler:
            handler(msg)
        else:
            raise ValueError('待处理的事件的事件类型没有注册有效处理函数')                                
            

#基本的几个事件类型的基处理器，不建议修改
BASE_MSG_HANDLER=Handler()

@BASE_MSG_HANDLER.handles(DAMAGE)
def _handle_damage(msg: GameMessage):
        """具体伤害处理逻辑"""
        if msg.acp:  # 需要有接受者
            msg.acp.hp -= msg.val
            print(f"[伤害处理] {msg.acp.name} 受到 {msg.val} 点伤害，剩余HP: {msg.acp.hp}")

@BASE_MSG_HANDLER.handles(HEAL)
def _handle_heal(msg: GameMessage):
        """治疗处理逻辑（示例）"""
        if msg.acp and msg.val > 0:
            msg.acp.hp += msg.val
            print(f"[治疗处理] {msg.acp.name} 恢复 {msg.val} 点生命，当前HP: {msg.acp.hp}")

@BASE_MSG_HANDLER.handles(COMMAND_SKIP)
def _handle_command_skip(msg: GameMessage):
        """命令：跳过事件处理逻辑（示例）"""
        if msg.val > 0:
            msg.mng.command_skip(msg.val)
            print(f"[命令处理] 跳过{msg.val}件事件")


#默认直接定义一个主处理器,继承自基本消息类型的基处理器  
mainhandler=Handler(BASE_MSG_HANDLER) 



#消息处理器，需要绑定中心事件处理器对象使用。
class Msgmanager:
    def __init__(self,handler:Handler=mainhandler):
        self.listener=[]
        self.msgs=deque()
        self.handler=handler
        self.uuid=uuid.uuid4()
        
    def register(self,objec):
        '''
           注册监听器
           
           参数：objec:可监听对象(含update方法)
           
           使用示例：
           xxx.register(man1)
               
           注意:不是可监听对象不能注册;
        '''
        if hasattr(objec,'update') and callable(getattr(objec,'update')):
                self.listener.append(objec)
                if hasattr(objec,'reg') and callable(getattr(objec,'reg')) and hasattr(objec,'reg_type') and not self.handler.is_reg(objec.reg_type):
                    objec.reg(self.handler)
                print(f'成功注册{objec},UUID:{objec.uuid}')
        else:
            raise ValueError('对象没有update方法,不是能够接受消息的对象,不能注册.')
            
    def remove(self,objec):
        '''移除监听器'''
        self.listener.remove(objec)
        print(f'移除{objec}')
        
    def acceptmsg(self, msg:GameMessage): #一般消息左插入
        '''
           接受一般消息，并插入到队列左端
           
           参数：msg:消息体
           
           使用示例：
           new_msg = GameMessage(
                    exc=aqqqq,
                    acp=qqqqa,
                    typ=COMMAND_SKIP,
                    val=1,
                    mng=mng
                )
                mng.acceptmsg(new_msg)       
           注意:必须是完整合法的消息体
        '''
        self.msgs.appendleft(msg)
        print(f"接收消息")
          
    def acceptmsgp(self, msg:GameMessage): #优先消息右插入
        '''接受优先消息，插入到队列右端'''
        self.msgs.append(msg)
        print(f"\n接收优先消息")

    def broadcast(self,msg):
        '''广播消息'''
        print(f'广播消息')
        for i in self.listener:
            i.update(msg)

    def handle(self, msg: GameMessage):
        '''处理消息'''
        print(f"处理 {msg.typ} 类型消息")
        self.handler.handle_message(msg)
        
    def command_skip(self,val):
        '''COMMAND_SKIP的实际实现'''
        #print(self.msgs)
        for i in range(val):
            if self.msgs:
                self.msgs.pop()
            else:
                break
        #print(self.msgs)

    def clear(self):
        '''清空消息链'''
        self.msgs=deque()
        print('消息链已经清空')
       

    def exect(self):
        '''
           事件执行
           当发送完消息后，需要发送xxx.exect()以开始事件执行。
           但是，对于在执行过程中产生的消息，一般不需要再发送执行指令。
           
           参数：无
           返回值
           1：如顺利执行完所有消息（即消息链最终为空）
           0：未能执行完所有消息（中止）
           
           使用示例：
           xxx.exect()
               
           注意:
               有以下限制：
               单次exect执行，最长消息链大小为100，达到上限则中止。
               某消息多次重复出现，疑似死循环，则中止。
               单条事件执行时间超过400ms则超时中止。
        '''
        print('处理开始')
        max_exect_num = 100
        loop_possible_count = 20
        time_window=0.4
        appeared = set()
        lst_msg_time=time.time()
    
        while self.msgs and max_exect_num > 0:
            current_msg = self.msgs.pop()
        
            # 生成消息指纹
            msg_fingerprint = current_msg.fingerprint
            #print(f'处理消息指纹: {msg_fingerprint}')
        
            # 广播和处理
            self.broadcast(current_msg)
            self.handle(current_msg)
        
            # 计数器管理
            max_exect_num -= 1
        
            # 死循环检测逻辑
            if msg_fingerprint in appeared:
                if len(self.msgs) >= 4:  # 队列持续增长
                    loop_possible_count -= 2
                else:
                    loop_possible_count -= 1
            else:
                loop_possible_count = 20
                appeared.add(msg_fingerprint)
        
            # 终止条件判断
            if max_exect_num <= 0:
                print(f'\n长消息链中止: 剩余消息 {len(self.msgs)} 条')
            elif loop_possible_count <= 0:
                print(f'\n疑似死循环中止: 剩余消息 {len(self.msgs)} 条')
                break
            if time.time() -lst_msg_time >time_window:
                print(f'\n处理超时中止: 剩余消息 {len(self.msgs)} 条')
                break
            lst_msg_time=time.time()
            print('\n下一条消息')
        print('处理结束')
        
        if not self.msgs:
            return 1
        return 0


#技能类
class Skill:
    def __init__(self,name:str,owner:Optional[Char],reg_type:Optional[str]=None):
        self.name=name
        self.owner=owner
        self.reg_type=reg_type
        self.uuid=uuid.uuid4()
    def reg(self,handl:Handler):
        '''(被动技能)注册事件'''
        if self.reg_type:
            handl.register_type(self.reg_type,self.type_effect)
    def update(self,msg:GameMessage):
        '''(被动技能)更新(接受消息)'''
        pass
    def type_effect(self,msg:GameMessage):
        '''(被动技能)技能事件效果'''
        pass
        
    def __str__(self):
        return self.name
    def __hash__(self):
        return hash(self.uuid)
    def __eq__(self,other):
        return self.uuid==other.uuid


                

