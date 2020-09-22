from PIL import Image
from PIL import ImageFilter
import math
import numpy
import sys
from stl import mesh
def main():
    #Get commandline arguments
    if(len(sys.argv)<2):
        sys.exit("file required, exiting")
        
    elif(len(sys.argv)<3):
        filename = sys.argv[1];
        smoothingFactor = 2
        blurFactor = 3
    else:
        filename = sys.argv[1]
        smoothingFactor = sys.argv[2]
        blurFactor = sys.argv[3]
    #Open image
    givenImage = Image.open(filename)
    #Resize image if needed
    dimensions = width,height = givenImage.size;
    totalSize = width*height
    maxSize = 1000000
    print(str(dimensions)+":  "+ str(totalSize))
    if totalSize>maxSize:
        print("file very large, rescaling...")
        width,height = math.ceil(width/2),math.ceil(height/2)
        
        fileImage = givenImage.resize((width,height),Image.ANTIALIAS)
        fileImage.save("resize.png")
        
        print("done")
    else:
        fileImage = givenImage
    fileImage.save("testimage.png")
    #Create new image
    newImage = Image.new(fileImage.mode,fileImage.size)
    newImagePixels = newImage.load()
    coordinate = 0,0
    black = (0,0,0,255)
    white = (255,255,255,255)
    #convert to pure black white
    thresh = 140;
    lam = lambda x: 255 if x> thresh else 0
    image = fileImage.convert('L').point(lam, mode = '1')
    imgFil = ImageFilter.ModeFilter(2)
    print("smoothing image...")
    for i in range(smoothingFactor):
        image = image.filter(imgFil)
    print("done")
    heightList = [[0]* height for i in range(width)]
    visitedList = [[0]*height for i in range(width)]
    horizontal = 1
    vertical = 1
    
    heightCount = 0
    print("identify loops...")
    for y in range(height):
        for x in range(width):           
            coordinate = x,y
            pixel = image.getpixel(coordinate)
            
            #find first black pixel
            if(pixel == 0 and visitedList[x][y]==0):
                #identify boundary
                heightCount= heightCount+1
                checkLoop(visitedList, image,x,y,heightCount, width,height)
    print("done")
    fillVisits = [[False]*height for i in range(width)]
    fillValues = [[0]*height for i in range(width)]
    print("shade regions...")
    #fill image with greyscale for heightmap
    numColors = fillImage(fillValues, fillVisits, visitedList,width,height)+1
    print("done")
    colors = createColors(black,white,numColors)
    print("draw image")
    for y in range(height):
        for x in range(width):
            newImagePixels[x,y] = colors[fillValues[x][y]]
    print("done")
    print("blurring height map...")
    #smooth out heightmap
    imgFil = ImageFilter.GaussianBlur(math.sqrt(math.sqrt(totalSize))/2)
    for i in range(blurFactor):        
        newImage = newImage.filter(imgFil)
    print("done")
    newImage.save('newImage.png')
    #Generate 3d file
    newImagePixels = newImage.load()
    print("generating stl file...")
    vertices = [[(0,0,0)]for i in range(height*width)]
    faces = [[(0,0,0)]for i in range(((height-1)*(width-1)*2))]
    
    for y in range(height):
        for x in range(width):
            vertices[y*width+x] = (x,y,newImagePixels[(x,y)][0])
   
    for y in range(height-1):
        for x in range(width-1):
            faces[2*y*(width-1)+(2*x)] = (x+(y*width),x+1+(y*width),(((y+1)*width)+x)) 
            faces[2*y*(width-1)+(2*x)+1] = (x+1+(y*width),(y+1)*width+x,(y+1)*width+x+1)
    meshFile = mesh.Mesh(numpy.zeros(len(faces),dtype = mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            meshFile.vectors[i][j] = vertices[f[j]]
    image.close()
    meshFile.save("mesh.stl")
    print("done and done")


def fillImage(filled, visits, heights,maxX,maxY):
   
    this_level = []
    visits[0][0] = True
    nextLevel = [(0,0)]
    validAreas = set([])
    height =-1
    while(len(nextLevel)>0):
        height=height +1
        for i in nextLevel:
            validAreas.add(heights[i[0]][i[1]])
            this_level.append(i)
        nextLevel.clear()
        while(len(this_level)>0):
            x,y = this_level[0][0],this_level[0][1]
            #up
            absorb(this_level,nextLevel,visits,(x,y-1), height, filled, maxX,maxY,heights,validAreas)
            #down                              
            absorb(this_level,nextLevel,visits,(x,y+1), height, filled, maxX,maxY,heights,validAreas)
            #left                             
            absorb(this_level,nextLevel,visits,(x-1,y), height, filled, maxX,maxY,heights,validAreas)
            #right                           
            absorb(this_level,nextLevel,visits,(x+1,y), height, filled, maxX,maxY,heights,validAreas)
            this_level.pop(0)
    return height




def absorb(levelList,nextLevel, visits, point,height, filled, maxX, maxY, heightMaps, validAreas):
    x,y = point[0],point[1]
    if(x>=0 and x<maxX and y>=0 and y<maxY):
        if(not visits[x][y]):
            #check if line
            if(heightMaps[x][y]in validAreas):
                visits[x][y] = True
                levelList.append((x,y))
                filled[x][y] = height
            else:
                nextLevel.append((x,y))

                    
def notTouching(visited,x,y):
    for i in range(2):
        for j in range(2):
            if(visited[x+i-1][y+j-1]!=0):
                visited[x][y]=visited[x+i-1][y+j-1]
                return False
    return True
def checkLoop(visited, image,x,y,height,maxX,maxY):
    #setup
    visited[x][y] = height
    loopList = [(x,y)]
    while(len(loopList)>0):
        point = loopList[0]
        loopList.pop(0)
        for i in range(-1,2):
            for j in range(-1,2):
                neighbor = (point[0]+i,point[1]+j)
                
                if(neighbor[0]>=0 and neighbor[0]<maxX and neighbor[1]>=0 and neighbor[1]<maxY):
                    if(image.getpixel(neighbor) < 50 and visited[neighbor[0]][neighbor[1]] == 0):
                        visited[neighbor[0]][neighbor[1]] = height
                        loopList.append(neighbor)



def createColors(start,end,iterations):
    if(iterations == 1):
        return [start,end]
    delta_r = float(end[0]-start[0]) / (iterations-1)
    delta_g = float(end[1]-start[1]) / (iterations-1)
    delta_b = float(end[2]-start[2]) / (iterations-1)
    returnList = []
    for i in range(0, iterations):
        returnList.append((int(math.floor(start[0]+delta_r*i)),int(math.floor(start[1]+delta_g*i)),int(math.floor(start[2]+delta_b*i)),255))
    return returnList

if(__name__ == "__main__"):
    main()

