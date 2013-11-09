from AppKit import NSCircularSlider, NSColor, NSRegularControlSize
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.extensions import getExtensionDefault, setExtensionDefault, getExtensionDefaultColor, setExtensionDefaultColor
from mojo.events import addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView
from mojo.drawingTools import *
from vanilla import *

def getPointsOnCurve(n, (x0, y0), (x1, y1), (x2, y2), (x3, y3)):
    
    points = []
    
    for t in range(1, n):
        t = t/n
        
        ax = x0 + t * (x1 - x0)
        ay = y0 + t * (y1 - y0)
        bx = x1 + t * (x2 - x1)
        by = y1 + t * (y2 - y1)
        cx = x2 + t * (x3 - x2)
        cy = y2 + t * (y3 - y2)
        dx = ax + t * (bx - ax)
        dy = ay + t * (by - ay)
        ex = bx + t * (cx - bx)
        ey = by + t * (cy - by)
        fx = dx + t * (ex - dx)
        fy = dy + t * (ey - dy)
                        
        points.append((fx, fy))

    return points

def getPointsOnLine(n, (x0, y0), (x1, y1)):
    
    points = []
    
    for t in range(1, n):
        t = t/n
        
        fx = x0 + t * (x1 - x0)
        fy = y0 + t * (y1 - y0)
        
        points.append((fx, fy))
    
    return points
    

class SliderGroup(Group):
    def __init__(self, posSize, text, minValue, maxValue, value, callback):
        Group.__init__(self, posSize)
        self.text = TextBox((0, 0, -0, 20), text)
        self.slider = Slider((2, 20, -60, 17), minValue=minValue, maxValue=maxValue, value=value, sizeStyle="small", callback=self.sliderChanged)
        self.edit = EditText((-40, 15, -0, 22), text=str(value), placeholder=str(value), callback=self.editChanged)
        self.callback = callback
        
    def sliderChanged(self, sender):
        self.edit.set(str(int(self.slider.get())))
        self.callback(sender)
        
    def editChanged(self, sender):
        try:
            value = int(float(self.edit.get()))
        except ValueError:
            value = int(self.edit.getPlaceholder())
            self.edit.set(value)
        self.slider.set(value)
        self.callback(sender)
        

BroadNibBackgroundDefaultKey = "com.asaumierdemers.BroadNibBackground"

class BroadNibBackground(BaseWindowController):
    
    def __init__(self):
        
        self.font = CurrentFont()
        if self.font is None:
            from vanilla.dialogs import message
            message("Oops!", "You need a font to use this tool.")
            return
        
        x = 10
        y = 10
        h = 40
        w = -10
        
        layers = self.font.layerOrder
        if len(layers) < 1:
            from vanilla.dialogs import message
            message("Oops!", "You need two layers to use this tool.")
            return
        
        lh = len(layers)*20+20
        
        self.layerName = layers[0]
        self.pointList = []
                
        self.w = FloatingWindow((200, 330), "Broad Nib Background")
        
        
        stepValue = getExtensionDefault("%s.%s" %(BroadNibBackgroundDefaultKey, "step"), 20)
        self.w.step = SliderGroup((x, y, w, h), "Steps :", 0, 60, stepValue, callback=self.stepChanged)
        
        y+=h
        
        widthValue = getExtensionDefault("%s.%s" %(BroadNibBackgroundDefaultKey, "width"), 50)        
        self.w.width = SliderGroup((x, y, w, h), "Width :", 0, 200, widthValue, callback=self.widthChanged)
        
        y+=h
        
        heightValue = getExtensionDefault("%s.%s" %(BroadNibBackgroundDefaultKey, "height"), 10)
        self.w.height = SliderGroup((x, y, w, h), "Height :", 0, 100, heightValue, callback=self.heightChanged)
        
        y+=h
        
        angleValue = getExtensionDefault("%s.%s" %(BroadNibBackgroundDefaultKey, "angle"), 30)
        self.w.angle = SliderGroup((x, y, w, h), "Angle :", 0, 360, angleValue, callback=self.angleChanged)
        self.w.angle.slider.getNSSlider().cell().setSliderType_(NSCircularSlider)
        self.w.angle.text.setPosSize((0, 15, -0, 20))
        self.w.angle.slider.setPosSize((60, 10, 30, 30))
        self.w.angle.slider._nsObject.cell().setControlSize_(NSRegularControlSize)
        
        y+=h + 20
                
        shapeValue = getExtensionDefault("%s.%s" %(BroadNibBackgroundDefaultKey, "shape"), 0)
        self.w.shapetext = TextBox((x, y, -0, 20), "Shape :")
        self.w.shape = RadioGroup((74, y, -0, 20), ["oval", "rect"], isVertical=False, callback=self.shapeChanged)
        self.w.shape.set(shapeValue)
        
        y+=h + 5
                
        color = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 0, 0, .5)
        colorValue = getExtensionDefaultColor("%s.%s" %(BroadNibBackgroundDefaultKey, "color"), color)
        self.w.colortext = TextBox((x, y, -0, 20), "Color :")
        self.w.color = ColorWell((70, y-5, w, 30), callback=self.colorChanged, color=colorValue)
        
        y+=h
        
        self.w.layer = List((x, y, w, lh), layers, allowsMultipleSelection=False, selectionCallback=self.layerChanged)
        
        y+=lh+15
        
        self.w.setPosSize((100, 100, 200, y))
        
        addObserver(self, "drawBroadNibBackground", "drawBackground")
        
        # needed for windowCloseCallback
        self.setUpBaseWindowBehavior()
        
        self.w.open()
    
    def windowCloseCallback(self, sender):
        # remove the observer to stop getting notifications
        removeObserver(self, "drawBackground")
        super(BroadNibBackground, self).windowCloseCallback(sender)
    
    def stepChanged(self, sender):
        setExtensionDefault("%s.%s" %(BroadNibBackgroundDefaultKey, "step"), int(sender.get()))
        self.updateView()
    
    def widthChanged(self, sender):
        setExtensionDefault("%s.%s" %(BroadNibBackgroundDefaultKey, "width"), int(sender.get()))
        self.updateView()
    
    def heightChanged(self, sender):
        setExtensionDefault("%s.%s" %(BroadNibBackgroundDefaultKey, "height"), int(sender.get()))
        self.updateView()
    
    def angleChanged(self, sender):
        setExtensionDefault("%s.%s" %(BroadNibBackgroundDefaultKey, "angle"), int(sender.get()))
        self.updateView()
    
    def shapeChanged(self, sender):
        setExtensionDefault("%s.%s" %(BroadNibBackgroundDefaultKey, "shape"), sender.get())
        self.updateView()
    
    def colorChanged(self, sender):
        setExtensionDefaultColor("%s.%s" %(BroadNibBackgroundDefaultKey, "color"), sender.get())
        self.updateView()

    def getColor(self):
        color = self.w.color.get()
        return color.getRed_green_blue_alpha_(None, None, None, None)
    
    def layerChanged(self, sender):
        self.layerName = sender.get()[sender.getSelection()[0]]
        self.updateView()
    
    def updateView(self, sender=None):
        UpdateCurrentGlyphView()
    
    def drawBroadNibBackground(self, info):
        
        g = info["glyph"].getLayer(self.layerName)
        
        # update the point list only if drawing on the selected layer
        if info["glyph"].layerName == self.layerName:
                        
            self.pointList = []
        
            step = int(self.w.step.slider.get())
                
            for contour in g.contours:
            
                # if path is open get first point
                if contour.segments[0].type == "move":
                    startingPoint = contour.segments[0][0]
                else: # get last point
                    startingPoint = contour.segments[-1][-1]
            
                for segment in contour.segments:

                    if segment.type == "curve":
                    
                        p0 = (startingPoint.x, startingPoint.y)
                        p1 = (segment[0].x, segment[0].y)
                        p2 = (segment[1].x, segment[1].y)
                        p3 = (segment[2].x, segment[2].y)
                    
                        points = getPointsOnCurve(step, p0, p1, p2, p3)   
                                         
                        # set next starting point
                        startingPoint = segment[2]
                    
                    else: # line
                
                        p0 = (startingPoint.x, startingPoint.y)
                        p1 = (segment[0].x, segment[0].y)
                    
                        points = getPointsOnLine(step, p0, p1)
                        
                        # set next starting point
                        startingPoint = segment[0]
                    
                    self.pointList.extend(points)
                
        width = int(self.w.width.slider.get())
        height = int(self.w.height.slider.get())
        angle = int(self.w.angle.slider.get())
        
        if self.w.shape.get() == 0:
            shape = oval
        else:
            shape = rect
        
        r,g,b,a = self.getColor()
        fill(r,g,b,a)
                 
        for point in self.pointList:
            x, y = point
            save()
            translate(x, y)
            rotate(angle)
            translate(-width/2, -height/2)
            shape(0, 0, width, height)
            restore()
        
        
BroadNibBackground()