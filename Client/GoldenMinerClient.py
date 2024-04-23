import socket
import pygame
import math
import pickle
import queue
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
import threading
import traceback

Map=None
Block=None
Wall=None

def pack(data):
    return pickle.dumps(data)

def unpack(data):
    try:
        return pickle.loads(data)
    except Exception as e:
        traceback.print_exc()
        return None
    
def safe_getattr(obj,value,default='default'):
    try:
        if obj==None:
            return default
        else:
            return getattr(obj,value)
    except:
        return default

class ServerInterface:
    def __init__(self):
        self.server_ip=''
        self.server_port=-1
        
    def setServerIP(self,ip,port=None):
        self.server_ip=ip
        if port!=None:
            self.server_port=port
    
    def setServerPort(self,port):
        self.server_port=port
        
    def connect(self):
        self.client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.client.connect((self.server_ip,self.server_port))
        except Exception as e:
            messagebox.showerror("Error",f"Cannot connect to server: {e}")
            return None
        return self.client
    
    def listenServer(self,gameQueue):
        try:
            while self.client:
                data=self.client.recv(10240)
                if not data:
                    break
                _tmp=data.split(b'^&')
                for i in _tmp:
                    if i:
                        gameQueue.put(i)
                
        except:
            return
    
    def send(self,**data):
        self.client.send(pack(data))

        
class MainGame():
    def __init__(self):
        pygame.init()
        self.serverInterface=ServerInterface()
        self.server=None
        self.gameQueue=queue.Queue()
        self.nick=''
        self.width=pygame.display.Info().current_w
        self.height=pygame.display.Info().current_h
        self.window=None
        self.running=False
        self.base_height=self.height//2-200
        self.FPS=60
        self.tick=pygame.time.Clock()
        self.gametime=60
        self.gameRule=None
        
    def __call__(self):
        self.login()
        
    def login(self):
        self.root=Tk()
        self.root.title("Golden Miner")
        self.root.geometry(f"300x180+{self.root.winfo_screenwidth()//2-150}+{self.root.winfo_screenheight()//2-90}")
        self.root.resizable(False,False)
        _frame=LabelFrame(self.root,text="Connect",width=280,height=160,)
        _frame.place(anchor=CENTER,relx=0.5,rely=0.5,x=0,y=0)
        _offset_x=10
        _offset_y=0
        self.nickname=Entry(_frame,width=20)
        self.server_ip=Entry(_frame,width=20)
        self.server_port=Entry(_frame,width=20)
        self.nickname_label=Label(_frame,text="Nickname:")
        self.server_ip_label=Label(_frame,text="Server IP:")
        self.server_port_label=Label(_frame,text="Server Port:")
        self.connect_button=Button(_frame,text="Connect",command=self.connect,width=32)
        self.nickname_label.place(x=10+_offset_x,y=10++_offset_y)
        self.nickname.place(x=100+_offset_x,y=10++_offset_y)
        self.server_ip_label.place(x=10+_offset_x,y=40++_offset_y)
        self.server_ip.place(x=100+_offset_x,y=40++_offset_y)
        self.server_port_label.place(x=10+_offset_x,y=70++_offset_y)
        self.server_port.place(x=100+_offset_x,y=70++_offset_y)
        self.connect_button.place(x=12+_offset_x,y=100++_offset_y)
        
        self.server_port.bind('<Return>',self.connect)
        
        self.nickname.insert(0,"Player")
        self.server_ip.insert(0,"127.0.0.1")
        self.server_port.insert(0,"8888")
        
        self.root.mainloop()
        
    def connect(self,*event):
        if self.nickname.get()=='':
            messagebox.showerror("Error","Nickname cannot be empty!")
            return
        if self.server_ip.get()=='':
            messagebox.showerror("Error","Server IP cannot be empty!")
            return
        if self.server_port.get()=='':
            messagebox.showerror("Error","Server Port cannot be empty!")
            return
        self.nick=self.nickname.get()
        self.serverInterface.setServerIP(self.server_ip.get(),int(self.server_port.get()))
        self.server=self.serverInterface.connect()
        self.root.destroy()
        if self.server==None:
            return
        self.build()
        self.exit()
        
    def exit(self):
        self.client=None
        self.server.close()
        self.thread.join()
        exit()
        
    def build(self):
        global Map,Block,Wall
        self.thread=threading.Thread(target=self.serverInterface.listenServer,args=(self.gameQueue,))
        self.thread.start()
        try:
            ClassPack=self.gameQueue.get()
            ClassPack=ClassPack.split(b'^&')
            for i in ClassPack[1:]:
                self.gameQueue.put(i)
            ClassPack=ClassPack[0]
        except queue.Empty:
            pass
        else:
            try:
                ClassContent=unpack(ClassPack)
                Map,Block,Wall=list(map(unpack,ClassContent))
            except Exception as e:
                traceback.print_exc()
                messagebox.showerror("Error","Cannot get Map class from server!")
                self.exit()
        self.serverInterface.send(action='login',info=self.nick)
        self.window=pygame.display.set_mode((self.width,self.height) ,pygame.FULLSCREEN)        
        pygame.display.set_caption("Golden Miner")
        self.mainloop()
        
    def rebuild(self):
        pygame.init()
        self.build()
        
    def update(self):
        pygame.display.flip()
        
    def pytext(self,text,x,y,size=36,color=(255,255,255)):
        _font=pygame.font.Font(None,size)
        _text=_font.render(text,True,color)
        _text_rect=_text.get_rect()
        _text_rect.center=(x,y)
        return _text,_text_rect
        
    def buttonArea(self):
        self.button_ready1=pygame.Rect(self.width//4+100,self.height//4-80,140,35)
        self.button_quit1=pygame.Rect(self.width//4+100,self.height//4-20,140,35)
        self.button_ready2=pygame.Rect(self.width//4*3+100,self.height//4-80,140,35)
        self.button_quit2=pygame.Rect(self.width//4*3+100,self.height//4-20,140,35)
        
        self.button_r1_inArea=False
        self.button_q1_inArea=False
        self.button_r2_inArea=False
        self.button_q2_inArea=False
        
        self.button_r1_clicked=False
        self.button_q1_clicked=False
        self.button_r2_clicked=False
        self.button_q2_clicked=False
        
        self.button_r1_done=False
        self.button_q1_done=False
        self.button_r2_done=False
        self.button_q2_done=False
        
    def sourceLoad(self):
        self.source_pic={'miner':pygame.image.load('Miner.png').convert_alpha(),'stone':pygame.image.load('Stone.png').convert_alpha(),'gold':pygame.image.load('Gold.png').convert_alpha(),
            'diamond':pygame.image.load('Diamond.png').convert_alpha(),'boom':pygame.image.load('Boom.png').convert_alpha()}
        
    def _paintIndicator(self,mid_pos,distance):
        positive=pygame.draw.polygon(self.window,(255,255,255),[(mid_pos[0]-distance,mid_pos[1]),(mid_pos[0]-distance-20,mid_pos[1]-15),(mid_pos[0]-distance-20,mid_pos[1]+15)])
        negative=pygame.draw.polygon(self.window,(255,255,255),[(mid_pos[0]+distance,mid_pos[1]),(mid_pos[0]+distance+20,mid_pos[1]-15),(mid_pos[0]+distance+20,mid_pos[1]+15)])
        
    def paint(self):
        if not self.gameRule.player1:
            pygame.draw.rect(self.window,(60,60,60),(0,0,self.width//2,self.base_height))
        else:
            pygame.draw.rect(self.window,(80,80,80),(0,0,self.width//2,self.base_height))
            
            self.window.blit(self.source_pic['miner'],(self.width//4-100,self.height//4-50))
            name_text1=self.pytext(safe_getattr(self.gameRule.player1,'nick','Player1'),self.width//4-50,self.height//4-80)
            self.window.blit(*name_text1)
            score_text1=self.pytext('Score: '+str(safe_getattr(self.gameRule.player1,'score',0)),self.width//4-400,self.height//4-230)
            self.window.blit(*score_text1)
            
            if self.gameRule.me==1:
                self._paintIndicator((self.width//4-50,self.height//4-10),80)
        
        if self.gameRule.status==0:
            if self.gameRule.me==1:
                if self.button_r1_clicked:
                    pygame.draw.rect(self.window,(200,200,200),self.button_ready1)
                else:
                    pygame.draw.rect(self.window,(120,120,120),self.button_ready1)
                if self.button_r1_inArea:
                    pygame.draw.rect(self.window,(200,200,200),self.button_ready1,2)

                if self.button_q1_clicked:
                    pygame.draw.rect(self.window,(200,200,200),self.button_quit1)
                else:
                    pygame.draw.rect(self.window,(120,120,120),self.button_quit1)
                if self.button_q1_inArea:
                    pygame.draw.rect(self.window,(200,200,200),self.button_quit1,2)
                quit_text1=self.pytext('Quit Game',self.width//4+169,self.height//4-2)
                self.window.blit(*quit_text1)
            else:
                pygame.draw.rect(self.window,(200,200,200),self.button_ready1,2)
            ready_text1=self.pytext('Ready!' if self.gameRule.player1_ready else 'Not Ready',self.width//4+167,self.height//4-62)
            self.window.blit(*ready_text1)

        
        if not self.gameRule.player2:
            pygame.draw.rect(self.window,(60,60,60),(self.width//2,0,self.width,self.base_height))
        else:
            pygame.draw.rect(self.window,(80,80,80),(self.width//2,0,self.width,self.base_height))
            self.window.blit(self.source_pic['miner'],(self.width//4*3-100,self.height//4-50))
            name_text2=self.pytext(safe_getattr(self.gameRule.player2,'nick','Player2'),self.width//4*3-50,self.height//4-80)
            self.window.blit(*name_text2)
            score_text2=self.pytext('Score: '+str(safe_getattr(self.gameRule.player2,'score',0)),self.width//4*3+380,self.height//4-230)
            self.window.blit(*score_text2)
            if self.gameRule.me==2:
                self._paintIndicator((self.width//4*3-50,self.height//4-10),80)
        
        if self.gameRule.status==0:
            if self.gameRule.me==2:
                if self.button_r2_clicked:
                    pygame.draw.rect(self.window,(200,200,200),self.button_ready2)
                else:
                    pygame.draw.rect(self.window,(120,120,120),self.button_ready2)
                if self.button_r2_inArea:
                    pygame.draw.rect(self.window,(200,200,200),self.button_ready2,2)

                if self.button_q2_clicked:
                    pygame.draw.rect(self.window,(200,200,200),self.button_quit2)
                else:
                    pygame.draw.rect(self.window,(120,120,120),self.button_quit2)
                if self.button_q2_inArea:
                    pygame.draw.rect(self.window,(200,200,200),self.button_quit2,2)
                quit_text2=self.pytext('Quit Game',self.width//4*3+169,self.height//4-2)
                self.window.blit(*quit_text2)
            else:
                pygame.draw.rect(self.window,(200,200,200),self.button_ready2,2)
            ready_text2=self.pytext('Ready!' if self.gameRule.player2_ready else 'Not Ready',self.width//4*3+167,self.height//4-62)
            self.window.blit(*ready_text2)            
            
    def paintMap(self):
        for block in self.gameRule.map.map:
            size=block.size
            img=self.source_pic[block.type]
            img=pygame.transform.scale(img,(size*self.gameRule.map.BlockSize,size*self.gameRule.map.BlockSize))
            self.window.blit(img,block.offset_pos)
            
            # pygame.draw.rect(self.window,(255,0,0),(*block.offset_pos,block.actual_size,block.actual_size),2)            
            # pygame.draw.rect(self.window,(0,255,0),(*block.pos,1,1),5)
            
        self.costShowWindow()
        

    def paintClamp(self):
        self.gameRule.player1.clampPos=self.gameRule.calcClampPos(1)
        self.gameRule.player2.clampPos=self.gameRule.calcClampPos(2)
        if self.gameRule.me==1:
            color1=(0,255,255)
            color2=(255,0,0)
        elif self.gameRule.me==2:
            color1=(255,0,0)
            color2=(0,255,255)
        pygame.draw.rect(self.window,color1,(*self.gameRule.player1.clampPos,2,2),2)
        pygame.draw.rect(self.window,color2,(*self.gameRule.player2.clampPos,2,2),2)
        
        pygame.draw.line(self.window,(255,255,255),self.gameRule.player1_base_point,self.gameRule.player1.clampPos,2)
        pygame.draw.line(self.window,(255,255,255),self.gameRule.player2_base_point,self.gameRule.player2.clampPos,2)
        
        
        _clampPoints=self.calcClampPoint(self.gameRule.player1.clampPos,self.gameRule.player1.angle,'open' if self.gameRule.player1.status in (0,1) else 'close')
        pygame.draw.line(self.window,(255,255,255),self.gameRule.player1.clampPos,_clampPoints[0],2)
        pygame.draw.line(self.window,(255,255,255),_clampPoints[0],_clampPoints[1],2)
        pygame.draw.line(self.window,(255,255,255),self.gameRule.player1.clampPos,_clampPoints[2],2)
        pygame.draw.line(self.window,(255,255,255),_clampPoints[2],_clampPoints[3],2)
        
        _clampPoints=self.calcClampPoint(self.gameRule.player2.clampPos,self.gameRule.player2.angle,'open' if self.gameRule.player2.status in (0,1) else 'close')
        pygame.draw.line(self.window,(255,255,255),self.gameRule.player2.clampPos,_clampPoints[0],2)
        pygame.draw.line(self.window,(255,255,255),_clampPoints[0],_clampPoints[1],2)
        pygame.draw.line(self.window,(255,255,255),self.gameRule.player2.clampPos,_clampPoints[2],2)
        pygame.draw.line(self.window,(255,255,255),_clampPoints[2],_clampPoints[3],2)
            
    
    def calcClampPoint(self,basepos,angle,status):
        HookLong=20
        if status=='close':
            offsetAngle=50
        elif status=='open':
            offsetAngle=80
        left_pos_x_1=basepos[0]+HookLong*math.cos(math.radians(angle-offsetAngle))
        left_pos_x_2=left_pos_x_1+HookLong*math.cos(math.radians(angle-offsetAngle+90))
        left_pos_y_1=basepos[1]+HookLong*math.sin(math.radians(angle-offsetAngle))
        left_pos_y_2=left_pos_y_1+HookLong*math.sin(math.radians(angle-offsetAngle+90))
        right_pos_x_1=basepos[0]+HookLong*math.cos(math.radians(angle+offsetAngle))
        right_pos_x_2=right_pos_x_1+HookLong*math.cos(math.radians(angle+offsetAngle-90))
        right_pos_y_1=basepos[1]+HookLong*math.sin(math.radians(angle+offsetAngle))
        right_pos_y_2=right_pos_y_1+HookLong*math.sin(math.radians(angle+offsetAngle-90))
        return [left_pos_x_1,left_pos_y_1],[left_pos_x_2,left_pos_y_2],[right_pos_x_1,right_pos_y_1],[right_pos_x_2,right_pos_y_2]
            
    def costShowWindow(self):
        if self.showCost:
            _bg=pygame.draw.rect(self.window,(120,120,120),(self.showPos[0]+10,self.showPos[1]+10,150,35))
            _bg_outline=pygame.draw.rect(self.window,(255,255,255),(self.showPos[0]+10,self.showPos[1]+10,150,35),2)
            self.window.blit(*self.pytext(self.showBlock.type,self.showPos[0]+85,self.showPos[1]+28))
            self.window.blit(*self.pytext('Cost: '+str(self.showBlock.cost),self.showPos[0]+85,self.showPos[1]-10))
            
    def paintGameOver(self):
        _bg=pygame.draw.rect(self.window,(120,120,120),(self.width//2-200,self.height//2-80,400,160))
        _bg_outline=pygame.draw.rect(self.window,(255,255,255),(self.width//2-200,self.height//2-80,400,160),2)
        self.window.blit(*self.pytext(('Player1 Win!' if self.gameRule.winner==1 else 'Player2 Win!' if self.gameRule.winner==2 else 'Draw!' if self.gameRule.winner==3 else 'Other Player Quit'),self.width//2,self.height//2-20))
        self.window.blit(*self.pytext('Click To Restart',self.width//2,self.height//2+30))
            
    def buttonFunction(self):
        if self.gameRule.me==1:
            if self.gameRule.status==0:
                if self.button_r1_done:
                    self.gameRule.player1_ready=not self.gameRule.player1_ready
                    self.serverInterface.send(action='ready' if self.gameRule.player1_ready else 'cancel ready',info='1')
                    self.button_r1_done=False
                if self.button_q1_done:
                    self.serverInterface.send(action='quit',info='1')
                    self.button_q1_done=False
                    self.running=False
        elif self.gameRule.me==2:
            if self.gameRule.status==0:
                if self.button_r2_done:
                    self.gameRule.player2_ready=not self.gameRule.player2_ready
                    self.serverInterface.send(action='ready' if self.gameRule.player2_ready else 'cancel ready',info='2')
                    self.button_r2_done=False
                if self.button_q2_done:
                    self.serverInterface.send(action='quit',info='2')
                    self.button_q2_done=False 
                    self.running=False

    def buttonEvent(self,event,mod=0):
        if mod==0:
            if event.type == pygame.MOUSEMOTION:
                if self.gameRule.me==1:
                    self.button_r1_inArea=self.button_ready1.collidepoint(event.pos)
                    self.button_q1_inArea=self.button_quit1.collidepoint(event.pos)
                elif self.gameRule.me==2:
                    self.button_r2_inArea=self.button_ready2.collidepoint(event.pos)
                    self.button_q2_inArea=self.button_quit2.collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.gameRule.me==1:
                    if self.button_r1_inArea:
                        self.button_r1_clicked=True
                    if self.button_q1_inArea:
                        self.button_q1_clicked=True
                elif self.gameRule.me==2:
                    if self.button_r2_inArea:
                        self.button_r2_clicked=True
                    if self.button_q2_inArea:
                        self.button_q2_clicked=True
            if event.type == pygame.MOUSEBUTTONUP:
                if self.gameRule.me==1:
                    if self.button_r1_clicked==True:
                        self.button_r1_done=True
                    if self.button_q1_clicked==True:
                        self.button_q1_done=True
                    self.button_r1_clicked=False
                    self.button_q1_clicked=False
                elif self.gameRule.me==2:
                    if self.button_r2_clicked==True:
                        self.button_r2_done=True
                    if self.button_q2_clicked==True:
                        self.button_q2_done=True
                    self.button_r2_clicked=False
                    self.button_q2_clicked=False
        elif mod==1:
            if event.type == pygame.MOUSEMOTION:
                for b in self.gameRule.map.map:
                    if b.area_rect.collidepoint(event.pos):
                        self.showCost=True
                        self.showBlock=b
                        self.showPos=event.pos
                        break
                    else:
                        self.showCost=False
                        self.showBlock=None
                        self.showPos=(0,0)
        elif mod==2:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.gameRule.status==2:
                    self.gameRule.status=0
                    if self.gameRule.player1:
                        self.gameRule.playerInit(self.gameRule.player1)
                    if self.gameRule.player2:
                        self.gameRule.playerInit(self.gameRule.player2)
                    self.gameRule.player1_ready=False
                    self.gameRule.player2_ready=False
        
    def mainloop(self):
        self.gameRule=GameRule(Player(self.nick,self.serverInterface),self.width,self.height)
        #==================#
        self.showCost=False
        self.showBlock=None
        self.showPos=(0,0)
        #==================#
        self.sourceLoad()
        self.pic_dict={'stone':'Stone.png','gold':'Gold.png','diamond':'Diamond.png','boom':'Boom.png'}
        self.buttonArea()
        self.window.fill((30, 30, 30))

        self.running=True
        while self.running:
            self.tick.tick(self.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        
                    if self.gameRule.status==1:
                        if event.key == pygame.K_SPACE:
                            if self.gameRule.shoot():
                                player=self.gameRule.mePlayer()
                                self.serverInterface.send(action="shooting",info=(player.angle,player.swing_forward,player.g_forward,player.swing_speed))

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.gameRule.status==1:
                        if self.gameRule.shoot():
                            player=self.gameRule.mePlayer()
                            self.serverInterface.send(action="shooting",info=(player.angle,player.swing_forward,player.g_forward,player.swing_speed))

                self.buttonEvent(event,mod=self.gameRule.status)
                if self.gameRule.status==0:
                    self.buttonFunction()
            
            self.window.fill((30, 30, 30))
            self.paint()
            if self.gameRule.status==1 and self.gameRule.map!=None:
                try:
                    self.paintMap()
                    self.paintClamp()
                    self.gameRule.activeGroup()
                except:
                    pass
            elif self.gameRule.status==2:
                self.paintGameOver()
            try:
                ret=self.gameQueue.get(block=False)
            except queue.Empty:
                pass
            else:
                self.gameRule.ruleParse(ret)            
            
            self.update()
            
        pygame.quit()
        
class Player:
    def __init__(self,nick,client=None):
        self.nick=nick
        self.score=0
        self.client=client
        self.num=0
    def send(self,data):
        self.client.send(**data)
        
class GameRule:
    def __init__(self,mine,width,height):
        self.player1=None
        self.player2=None
        self.mine=mine
        
        self.width=width
        self.height=height
        #===================================#
        self.status=0   # 0: Ready, 1: Playing, 2: Game Over
        self.me=0       # 0: nobody,1: Player1, 2: Player2
        self.winner=-1  # 1: Player1, 2: Player2, 0: Quit, -1: Default
        self.player1_ready=False
        self.player2_ready=False
        #===================================#
        self.swing_speed=3
        self.g=0.01
        self.shoot_dis=5
        self.pull_dis=8
        self.catchpull_dis=4
        self.min_angle=10
        self.max_angle=170
        self.half_angle=(self.max_angle-self.min_angle)//2
        self.mid_angle=self.half_angle+self.min_angle
        self.min_length=50
        self.player1_base_point=(414,318)
        self.player2_base_point=(1374,318)
        #===================================#
        self.playerInit(self.mine)
        #===================================#
        self.map=None
    
    def playerInit(self,player):
        player.score=0
        player.angle=10
        player.swing_forward=1
        player.g_forward=1
        player.swing_speed=0
        player.length=self.min_length
        player.status=0      # 0: swing, 1: shooting, 2:pulling, 2:catchpulling
        player.clampPos=(0,0)
        player.clampBlock=None
    
    def activeGroup(self):
        if self.status==1:
            before=self.mePlayer().status
            self.swing()
            self.shooting()
            self.pulling()
            self.catchpulling()
            self.statusSwitch(before)
    
    def calcClampPos(self,num):
        if num==1:
            _pos_x=self.player1_base_point[0]+self.player1.length*math.cos(math.radians(self.player1.angle))
            _pos_y=self.player1_base_point[1]+self.player1.length*math.sin(math.radians(self.player1.angle))
        elif num==2:
            _pos_x=self.player2_base_point[0]+self.player2.length*math.cos(math.radians(self.player2.angle))
            _pos_y=self.player2_base_point[1]+self.player2.length*math.sin(math.radians(self.player2.angle))
        return (_pos_x,_pos_y)
    
    def shoot(self):
        player=self.mePlayer()
        if player.status==0:
            player.status=1
            return True
        return False
    
    def swing(self):
        if self.player1.status==0:
            self.player1.swing_speed+=self.g*self.player1.g_forward
            _before=self.player1.angle-self.mid_angle
            self.player1.angle+=self.player1.swing_speed
            _after=self.player1.angle-self.mid_angle
            if _before*_after<0:
                self.player1.g_forward=-self.player1.g_forward
            if self.player1.angle<self.min_angle:
                self.player1.angle=self.min_angle
                self.player1.swing_speed=0
            if self.player1.angle>self.max_angle:
                self.player1.angle=self.max_angle
                self.player1.swing_speed=0
            
        if self.player2.status==0:
            self.player2.swing_speed+=self.g*self.player2.g_forward
            _before=self.player2.angle-self.mid_angle
            self.player2.angle+=self.player2.swing_speed
            _after=self.player2.angle-self.mid_angle
            if _before*_after<0:
                self.player2.g_forward=-self.player2.g_forward
            if self.player2.angle<self.min_angle:
                self.player2.angle=self.min_angle
                self.player2.swing_speed=0
            if self.player2.angle>self.max_angle:
                self.player2.angle=self.max_angle
                self.player2.swing_speed=0            
                
    def shooting(self):
        mePlayer=self.mePlayer()
        notMePlayer=self.notMePlayer()
        if mePlayer.status==1:
            mePlayer.length+=self.shoot_dis
            ret=self.checkCollision(self.me)
            if isinstance(ret,Block):
                mePlayer.status=3
                mePlayer.clampBlock=ret
                mePlayer.clampBlock.touch_able=False
            elif isinstance(ret,Wall):
                mePlayer.status=2
            
        if notMePlayer.status==1:
            notMePlayer.length+=self.shoot_dis
        
    def checkCollision(self,num):
        if num==1:    
            self.player1.clampPos=self.calcClampPos(1)
            for block in self.map.map:
                if block.touch_able and block.area_rect.collidepoint(self.player1.clampPos):
                    return block
            if self.player1.clampPos[0]<0 or self.player1.clampPos[0]>self.width or self.player1.clampPos[1]>self.height:
                return Wall()
        elif num==2:
            self.player2.clampPos=self.calcClampPos(2)
            for block in self.map.map:
                if block.touch_able and block.area_rect.collidepoint(self.player2.clampPos):
                    return block
            if self.player2.clampPos[0]<0 or self.player2.clampPos[0]>self.width or self.player2.clampPos[1]>self.height:
                return Wall()
        return None
                    
    def pulling(self):
        if self.player1.status==2:
            self.player1.length-=self.pull_dis
            if self.player1.length<=self.min_length:
                self.player1.status=0
        if self.player2.status==2:
            self.player2.length-=self.pull_dis
            if self.player2.length<=self.min_length:
                self.player2.status=0
        
    def catchpulling(self):
        mePlayer=self.mePlayer()
        notMePlayer=self.notMePlayer()
        
        if mePlayer.status==3:
            mePlayer.length-=self.catchpull_dis/(mePlayer.clampBlock.size**2)
            mePlayer.clampPos=self.calcClampPos(self.me)
            mePlayer.clampBlock.updatePos([mePlayer.clampPos[0],mePlayer.clampPos[1]+15])
            if mePlayer.length<=self.min_length:
                self.settlement(self.me,mePlayer.clampBlock)
                
        if notMePlayer.status==3:
            notMePlayer.length-=self.catchpull_dis/(notMePlayer.clampBlock.size**2)
            notMePlayer.clampPos=self.calcClampPos(self.notMe(self.me))
            notMePlayer.clampBlock.updatePos([notMePlayer.clampPos[0],notMePlayer.clampPos[1]+15])
        
    def settlement(self,num:int,block):
        if num==1:
            self.player1.status=0
            self.player1.score+=block.cost
            self.map.remove(block.id)
            self.player1.clampBlock=None
        elif num==2:
            self.player2.status=0
            self.player2.score+=block.cost
            self.map.remove(block.id)
            self.player2.clampBlock=None
    
    def checkGameOver(self):
        for block in self.map.map:
            if block.type!='boom':
                return False
        return True
    
    def checkWinner(self):
        if self.player1.score>self.player2.score:
            return 1
        elif self.player1.score<self.player2.score:
            return 2
        else:
            return 3
    
    def statusSwitch(self,before):
        player=self.mePlayer()
        if self._statusSwtichCheck(before):
            if player.status==0:
                over=self.checkGameOver()
                if over:
                    self.mine.send({"action":"swing","info":(player.angle,player.swing_forward,player.g_forward,player.swing_speed)})
                    self.mine.send({"action":"over","info":self.checkWinner()})
                else:
                    self.mine.send({"action":"swing","info":(player.angle,player.swing_forward,player.g_forward,player.swing_speed)})
            elif player.status==1:
                ...
            elif player.status==2:
                self.mine.send({"action":"pulling","info":(player.length,player.angle)})
            elif player.status==3:
                self.mine.send({"action":"catchpulling","info":(player.clampBlock.id,player.length,player.angle)})
    
    def _statusSwtichCheck(self,before):
        status=self.mePlayer().status
        if before!=status:
            return True
        return False
            
    def which(self,mine):
        if self.player1==mine:
            return 1
        elif self.player2==mine:
            return 2
        else:
            return 0
    
    def notMe(self,num):
        if num==1:
            return 2
        elif num==2:
            return 1
        
    def mePlayer(self):
        return self.mine
        
    def notMePlayer(self):
        if self.me==1:
            return self.player2
        elif self.me==2:
            return self.player1
    
    def updateme(self,num):
        self.me=num
    
    def join(self,num,player):
        if num==1:
            self.player1=player
            self.playerInit(self.player1)
        elif num==2:
            self.player2=player
            self.playerInit(self.player2)
        else:
            return False
        return True
    
    def ready(self):
        if self.me==1:
            self.player1_ready=True
        elif self.me==2:
            self.player2_ready=True
        else:
            return False
        return True
    
    def mapDeal(self,map):
        self.map=map
        for block in self.map.map:
            block.setAreaRect(pygame.Rect(block.offset_pos[0],block.offset_pos[1],block.actual_size,block.actual_size))
    
    def ruleParse(self,msg):
        msg=unpack(msg)
        if msg['action']=='r_login':
            if msg['info']=='fail':
                messagebox.showerror("Error","加入失败")
                return False
            elif msg['info']=='full':
                messagebox.showerror("Error","房间已满")
                return False
            elif msg['info'] in ('1','2'):
                self.updateme(int(msg['info']))
                self.join(int(msg['info']),self.mine)
                return True
        elif msg['action']=='otherlogin':
            self.join(self.notMe(self.me),Player(msg['info']))
            return True
        elif msg['action']=='r_ready':
            if msg['info']=='1':
                self.player1_ready=True
            elif msg['info']=='2':
                self.player2_ready=True
            return True
        elif msg['action']=='r_c_ready':
            if msg['info']=='1':
                self.player1_ready=False
            elif msg['info']=='2':
                self.player2_ready=False
            return True
        elif msg['action']=='r_start':
            self.mapDeal(unpack(msg['info']))
            self.status=1
            return True
        elif msg['action']=='r_quit':
            if msg['info']=='1':
                self.player1=None
            elif msg['info']=='2':
                self.player2=None
            return True
        elif msg['action']=='r_over':
            self.status=2
            self.winner=int(msg['info'])
            self.map=None
            return True
        elif msg['action']=='r_swing':
            if self.notMePlayer().status==3:
                self.settlement(self.notMe(self.me),self.notMePlayer().clampBlock)
            self.notMePlayer().status=0
            self.notMePlayer().angle=msg['info'][0]
            self.notMePlayer().swing_forward=msg['info'][1]
            self.notMePlayer().g_forward=msg['info'][2]
            self.notMePlayer().swing_speed=msg['info'][3]
            self.notMePlayer().length=self.min_length
            
            return True
        elif msg['action']=='r_shooting':
            self.notMePlayer().status=1
            self.notMePlayer().angle=msg['info'][0]
            self.notMePlayer().swing_forward=msg['info'][1]
            self.notMePlayer().g_forward=msg['info'][2]
            self.notMePlayer().swing_speed=msg['info'][3]
            self.notMePlayer().length=self.min_length
            
            return True
        elif msg['action']=='r_pulling':
            self.notMePlayer().status=2
            self.notMePlayer().length=msg['info'][0]
            self.notMePlayer().angle=msg['info'][1]
            return True
        elif msg['action']=='r_catchpulling':
            self.notMePlayer().status=3
            self.notMePlayer().clampBlock=self.map[int(msg['info'][0])]
            self.notMePlayer().length=msg['info'][1]
            self.notMePlayer().angle=msg['info'][2]
            self.notMePlayer().clampBlock.touch_able=False
            return True
                

if __name__ == '__main__':
    try:
        main=MainGame()
        main()
    except:
        with open('error.log','w') as f:
            traceback.print_exc(file=f)
        raise SystemExit
