import socket
import threading
import time
import pickle
import configparser
import traceback
from GameMap import *

def pack(data):
    return pickle.dumps(data)

def unpack(data):
    try:
        return pickle.loads(data)
    except:
        return None
    
def mpack(action,info):
    return pickle.dumps({'action':action,'info':info})+b'^&'

class Log:
    console=True
    @classmethod
    def setConsole(cls,flag):
        cls.console=flag
    
    @staticmethod
    def print(text):
        Log.log(text)
    @staticmethod
    def log(text):
        Log.write(text)
        if Log.console:
            text=Log.format(text)
            print(text)
    @staticmethod
    def write(log):
        with open('server.log','a') as logfile:
            logfile.write(Log.format(log)+'\n')
    @staticmethod
    def format(text):
        return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())+'  '+text

class Server:
    def __init__(self):
        Log.print('========================')
        Log.print('Server initializing')
        Log.print('Server started')
        self.server_ip='0.0.0.0'
        self.server_port=8888
        self.loadConfig()
        Log.print('Server config loaded')
        self.server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.bind((self.server_ip,self.server_port))
        self.server.listen(2)
        Log.print('Server started at '+self.server_ip+':'+str(self.server_port))
        self.clients=[]
        self.client_threads=[]
        self.game=None
        Log.print('Server initialized successfully')
        Log.print('========================')
        Log.print('Golden Miner Server v1.0')
        Log.print('========================')
        
    def loadConfig(self):
        config=configparser.ConfigParser()
        if not config.read('config.ini'):
            config['SERVER']={'IP':'0.0.0.0','PORT':'8888'}
            config['MAP']={'MAX_COUNT':'32','BLOCK_SIZE':'35'}
            with open('config.ini','w') as configfile:
                config.write(configfile)
        else:
            config.read('config.ini')
        self.server_ip=config['SERVER']['IP']
        self.server_port=int(config['SERVER']['PORT'])
        Map.max_count=int(config['MAP']['MAX_COUNT'])
        Map.BlockSize=int(config['MAP']['BLOCK_SIZE'])
        
    def acceptClients(self):
        while True:
            client,addr=self.server.accept()
            Log.print('Client connected: '+str(addr[0]))
            client.send(pack((pack(Map),pack(Block),pack(Wall)))+b'^&')
            if len(self.clients)==0 and self.game==None:
                self.game=Game()
                Log.print('Game created')
            if len(self.clients)==2:
                Log.print('Client rejected: '+str(addr[0])+', full server')
                client.send(mpack('r_login','full'))
                client.close()
                continue
            self.clients.append(client)
            client_thread=threading.Thread(target=self.clientHandler,args=(client,addr))
            self.client_threads.append(client_thread)
            client_thread.start()
            
    def clientHandler(self,client,addr):
        mine=Player('Player',client)
        n=self.game.join(mine)
        if  n:
            mine.send('r_login',str(n))
        else:
            mine.send('r_login','fail')
            mine.close()
            self.clients.remove(client)
            self.client_threads.remove(threading.current_thread())
            return
        try:
            while True:
                data=client.recv(1024)
                if not data:
                    break
                ret=unpack(data)
                if ret:
                    self.game.parse(mine,ret)
        except Exception as e:
            self.clients.remove(client)
            self.client_threads.remove(threading.current_thread())
            Log.print('Player'+str(mine.me)+' '+str(mine.nick)+' disconnected')
            Log.print('--Client '+str(addr[0])+' disconnected')
            self.game.parse(mine,{'action':'quit','info':''})
            # Log.print('--Client '+str(addr[0])+' disconnected with error: '+str(traceback.format_exc()))
            
    def run(self):
        accept_thread=threading.Thread(target=self.acceptClients)
        accept_thread.start()
        accept_thread.join()
        
class Player:
    def __init__(self,nick,client):
        self.nick=nick
        self.score=0
        self.client=client
        self.me=0
        
    def setMe(self,num):
        self.me=num
        
    def setNick(self,nick):
        self.nick=nick
        
    def send(self,action,info):
        self.client.send(mpack(action,info))
        
    def close(self):
        self.client.close()
        
class Game:
    def __init__(self):
        self.player1=None
        self.player2=None
        #================================#
        self.player1_ready=False
        self.player2_ready=False
        #================================#
        self.map=None
        self.status=0   #0:waiting 1:playing 2:game over
    def join(self,player):
        if self.player1==None:
            self.player1=player
            return 1
        elif self.player2==None:
            self.player2=player
            return 2
        else:
            return False
    def which(self,mine):
        if self.player1==mine:
            return 1
        elif self.player2==mine:
            return 2
        else:
            return 0
    
    def mePlayer(self,mine):
        if self.player1==mine:
            return self.player1
        elif self.player2==mine:
            return self.player2
        else:
            return None
    
    def notMePlayer(self,mine):
        if self.player1==mine:
            return self.player2
        elif self.player2==mine:
            return self.player1
        else:
            return None
    
    def start(self):
        self.map=Map()
        self.status=1
        return self.map
        
    def parse(self,mine,actions):
        if actions['action']=='login':
            Log.print('Player'+str(self.which(mine))+' '+str(mine.nick)+' logged in')
            mine.setNick(actions['info'])
            mine.setMe(self.which(mine))
            if self.which(mine)==1:
                if self.player2!=None:
                    mine.send('otherlogin',self.player2.nick)
                    self.player2.send('otherlogin',mine.nick)
                    if self.player2_ready:
                        mine.send('r_ready','2')
            elif self.which(mine)==2:
                if self.player1!=None:
                    mine.send('otherlogin',self.player1.nick)
                    self.player1.send('otherlogin',mine.nick)
                    if self.player1_ready:
                        mine.send('r_ready','1')
            return True
        elif actions['action']=='ready':
            Log.print('Player'+str(self.which(mine))+' '+str(mine.nick)+' ready')
            if self.which(mine)==1:
                self.player1_ready=True
                if self.player2!=None:
                    self.player2.send('r_ready','1')
            elif self.which(mine)==2:
                self.player2_ready=True
                if self.player1!=None:
                    self.player1.send('r_ready','2')
            if self.player1_ready and self.player2_ready:
                Log.print('Both players ready, game start')
                map_source=self.start()
                self.player1.send('r_start',pack(map_source))
                self.player2.send('r_start',pack(map_source))
            return True
        elif actions['action']=='cancel ready':
            Log.print('Player'+str(self.which(mine))+' '+str(mine.nick)+' cancel ready')
            if self.which(mine)==1:
                self.player1_ready=False
                if self.player2!=None:
                    self.player2.send('r_c_ready','1')
            elif self.which(mine)==2:
                self.player2_ready=False
                if self.player1!=None:
                    self.player1.send('r_c_ready','2')
            return True
        elif actions['action']=='quit':
            Log.print('Player'+str(self.which(mine))+' '+str(mine.nick)+' quit')
            if self.which(mine)==1:
                self.player1=None
                if self.player2!=None:
                    self.player2.send('r_quit','1')
            elif self.which(mine)==2:
                self.player2=None
                if self.player1!=None:
                    self.player1.send('r_quit','2')
            if self.status==1:
                self.status=0
                self.player1_ready=False
                self.player2_ready=False
                if self.player1!=None:
                    self.player1.send('r_over','0') #0:quit 1:player1 win 2:player2 win
                    self.player1.send('r_c_ready','1')
                    self.player1.send('r_c_ready','2')
                if self.player2!=None:
                    self.player2.send('r_over','0') #0:quit 1:player1 win 2:player2 win
                    self.player2.send('r_c_ready','1')
                    self.player2.send('r_c_ready','2')
            return True
        elif actions['action']=='swing':
            Log.print('Player'+str(self.which(mine))+' '+str(mine.nick)+' > swing: '+str(actions['info']))
            self.notMePlayer(mine).send('r_swing',actions['info'])
            return True
        elif actions['action']=='shooting':
            Log.print('Player'+str(self.which(mine))+' '+str(mine.nick)+' > shooting: '+str(actions['info']))
            self.notMePlayer(mine).send('r_shooting',actions['info'])
            return True
        elif actions['action']=='pulling':
            Log.print('Player'+str(self.which(mine))+' '+str(mine.nick)+' > pulling: '+str(actions['info']))
            self.notMePlayer(mine).send('r_pulling',actions['info'])
            return True
        elif actions['action']=='catchpulling':
            Log.print('Player'+str(self.which(mine))+' '+str(mine.nick)+' > catch pulling: '+str(actions['info']))
            self.notMePlayer(mine).send('r_catchpulling',actions['info'])
            return True
        elif actions['action']=='over':
            Log.print('Player'+str(self.which(mine))+' '+str(mine.nick)+' > over: '+str(actions['info']))
            Log.print('Winner is Player'+str(actions['info']))
            self.mePlayer(mine).send('r_over',actions['info'])
            self.notMePlayer(mine).send('r_over',actions['info'])
            self.status=2
            return True
        
        return False
        
if __name__=='__main__':
    server=Server()
    server.run()
