import random

class Map:
    max_count=32
    BlockSize=35
    def __init__(self):
        self.map=[]
        self.max_count=Map.max_count
        self.BlockSize=Map.BlockSize
        self.genMap()
        
    def __getitem__(self,id):
        return self.find(id)
    
    def genMap(self):
        for id in range(self.max_count):
            self.map.append(Block(id,self.map,self.BlockSize))
            
    def find(self,id):
        for block in self.map:
            if block.id==id:
                return block
        return None
    
    def remove(self,id):
        for block in self.map:
            if block.id==id:
                self.map.remove(block)
                return True
        return False
        
class Block:
    def __init__(self,id,map,blocksize=35):
        self.map=map
        self.id=id
        self.pos_range=(100,1820,400,980)
        self.type=random.choices(['stone','gold','diamond','boom'],weights=[0.45,0.3,0.1,0.15],k=1)[0]
        self.size=random.randint(1,3)
        self.cost=0
        self.calcCost()
        self.pos=[0,0]
        self.actual_size=self.size*blocksize
        self.half_a_size=self.actual_size//2
        self.createRandomPos()
        self.offset_pos=[self.pos[0]-self.half_a_size,self.pos[1]-self.half_a_size]
        self.area_rect=None
        self.touch_able=True
    
    def __all__(self):
        return (self.pos,self.offset_pos,self.actual_size,self.type,self.cost,self.area_rect,self.touch_able,self.id,self.setAreaRect,self.updatePos)
    
    def setAreaRect(self,area_rect):
        self.area_rect=area_rect
        
    def getPos(self,pos):
        return tuple(self.offset_pos)
        
    def updatePos(self,pos):
        self.pos=pos
        self.offset_pos=[self.pos[0]-self.half_a_size,self.pos[1]-self.half_a_size]
    
    def randomPos(self):
        x=random.randint(self.pos_range[0],self.pos_range[1])
        y=random.randint(self.pos_range[2],self.pos_range[3])
        return [x,y]
    
    def createRandomPos(self):
        self.pos=self.randomPos()
        for block in self.map:
            if block!=self:
                if self.is_overlap(self.pos,self.actual_size,block.pos,block.actual_size):
                    self.createRandomPos()
                    break
    
    def is_overlap(self,pos1,size1,pos2,size2):
        if self.is_inArea(pos1[0],pos1[1],pos2[0],pos2[1],size2) or self.is_inArea(pos1[0]+size1,pos1[1],pos2[0],pos2[1],size2) or self.is_inArea(pos1[0],pos1[1]+size1,pos2[0],pos2[1],size2) or self.is_inArea(pos1[0]+size1,pos1[1]+size1,pos2[0],pos2[1],size2):
            return True
        else:
            return False
        
    def is_inArea(self,pos_x,pos_y,px,py,size):
        if pos_x >= px and pos_x <= px+size and pos_y >= py and pos_y <= py+size:
            return True
        else:
            return False
    
    def calcCost(self):
        if self.type=='stone':
            self.cost=1*self.size
        elif self.type=='gold':
            self.cost=3*self.size
        elif self.type=='diamond':
            self.cost=20
            self.size=1
        elif self.type=='boom':
            self.cost=-10
            self.size=2
            
class Wall:
    ...