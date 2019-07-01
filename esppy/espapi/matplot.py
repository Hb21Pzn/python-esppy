import matplotlib.animation as animation
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

import esppy.espapi.connections as connections

import ipywidgets as widgets

import logging

import esppy.espapi.tools as tools

#print(plt.style.available)

class Charts(object):

    def __init__(self,**kwargs):
        self._options = tools.Options(**kwargs)
        self._charts = []

        self._jupyter = False

        try:
            get_ipython
            self._jupyter = True
        except:
            pass

        plt.ioff()

        style = self._options.get("style","seaborn-pastel")
        matplotlib.style.use(style)

    def display(self):
        plt.show()

    def createChart(self,type,datasource,**kwargs):

        datasource.addDelegate(self)

        chart = Chart(self,type,datasource,**kwargs)
        self._charts.append(chart)

        return(chart)

    def createDashboard(self,**kwargs):
        dashboard = Dashboard(self,**kwargs)
        return(dashboard)

    def createControlPanels(self):
        panels = ControlPanels()
        return(panels)

    def dataChanged(self,datasource):
        for chart in self._charts:
            if chart._datasource == datasource:
                chart.draw()

    def infoChanged(self,datasource):
        pass

    def clear(self):
        self._charts = []
        plt.close()

class Chart(object):
    def __init__(self,charts,type,datasource,**kwargs):
        self._charts = charts
        self._type = type
        self._datasource = datasource
        self._dashboard = None
        self._options = tools.Options(**kwargs)
        self._figure = None
        self._axis = None

    def display(self):
        self.clear()
        width = self.getOption("width",10)
        height = self.getOption("height",5)

        name = self._options.get("name")
        if name != None:
            self._figure = plt.figure(num=name,figsize=(width,height));
        else:
            self._figure = plt.figure(figsize=(width,height));

        self._axis = self._figure.add_subplot(111)
        self.draw()
        if self._charts._jupyter:
            plt.show()

    def displayInDashboard(self,dashboard,dim,coordinate,rowspan,colspan):
        self.clear()
        self._dashboard = dashboard
        plt.figure(self._dashboard._figure.number);
        self._figure = self._dashboard._figure
        self._axis = plt.subplot2grid(dim,coordinate,rowspan=rowspan,colspan=colspan);
        name = self._options.get("name")
        if name != None:
            self._axis.set_title(name)
        self.draw()
        if self._charts._jupyter:
            plt.show()

    def clear(self):
        if self._dashboard == None:
            if self._figure != None:
                plt.figure(self._figure.number);
                plt.close()

        self._figure = None
        self._axis = None

    def draw(self):
        if self._axis == None:
            return

        self._axis.clear()

        ymin = self._options.get("ymin")
        ymax = self._options.get("ymax")

        if ymin != None:
            self._axis.set_ylim(bottom=ymin)
        if ymax != None:
            self._axis.set_ylim(top=ymax)

        if self._type == "vbar":
            x = self._datasource.getKeyTuple()
            values = self.getValues("y")
            tuples = self._datasource.getTuplesForFields(values)
            ind = np.arange(len(x))

            if len(tuples) == 0:
                return

            w = 0.8 / len(tuples)

            if len(tuples) == 1:
                num = 0
            else:
                num = -(w / len(tuples)) * (len(tuples) / 2)
                if len(tuples) % 2 != 0:
                    num -= w / 2

            for key,value in tuples.items():
                y = value
                self._axis.bar(ind + num,y,w,label=key)
                num += w
            self._axis.set_xticks(ind)
            self._axis.set_xticklabels(x)
            self._axis.legend(loc="upper center",bbox_to_anchor=(0.5,-0.05),fancybox=True,shadow=True,ncol=len(values))
        elif self._type == "hbar":
            x = self._datasource.getKeyTuple()
            values = self.getValues("y")
            tuples = self._datasource.getTuplesForFields(values)

            ind = np.arange(len(x))

            if len(tuples) == 0:
                return

            w = 0.8 / len(tuples)

            if len(tuples) == 1:
                num = 0
            else:
                num = -(w / len(tuples)) * (len(tuples) / 2)
                if len(tuples) % 2 != 0:
                    num -= w / 2

            for key,value in tuples.items():
                y = value
                self._axis.barh(ind + num,y,w,label=key)
                num += w
            self._axis.set_yticks(ind)
            self._axis.set_yticklabels(x)
            self._axis.legend(loc="upper center",bbox_to_anchor=(0.5,-0.05),fancybox=True,shadow=True,ncol=len(values))
        elif self._type == "pie":
            values = self.getValues("values")
            tuples = self._datasource.getTuplesForFields(values)
            keyTuple = self._datasource.getKeyTuple()
            for key,value in tuples.items():
                self._axis.pie(value,labels=keyTuple,shadow=True,autopct='%1.1f%%')
        elif self._type == "scatter":
            opt = self._options.get("x")
            xKeys = False
            if opt != None:
                x = self._datasource.getTuple(opt)
            else:
                x = self._datasource.getKeyValues()
                xKeys = True
            opt = self._options.get("y")
            if opt == None:
                raise Exception("must specify y")
            y = self._datasource.getTuple(opt)
            size = None
            opt = self._options.get("size")
            if opt != None:
                size = self._datasource.getTuple(opt)
            opt = self._options.get("color")
            if opt != None:
                color = self._datasource.getTuple(opt)

            if xKeys:

                ind = np.arange(len(x))
                self._axis.scatter(ind,y,s=size,c=color,alpha=.5)

                self._axis.set_xticks(ind)
                self._axis.set_xticklabels(x)

                labels = self.getValues("labels")

                if labels != None:

                    a = []

                    for i in range(0,len(x)):
                        a.append("")


                    for l in labels:
                        t = self._datasource.getTuple(l)
                        if t != None:
                            for i,label in enumerate(t):
                                a[i] += str(label)

                for i,label in enumerate(a):
                    logging.info("LABEL:  " + str(label))
                    self._axis.annotate(label,xy=(ind[i],t[i]),cmap=plt.cm.jet)

            else:
                self._axis.scatter(x,y,s=size,c=color,alpha=.5)
                keys = self._datasource.getKeyValues()
                for i,label in enumerate(keys):
                    logging.info("LABEL: " + label + " :: " + str((x[i],y[i])))
                    self._axis.annotate(label,xy=(x[i],y[i]))

        elif self._type == "series":
            lineWidth = self.getOption("linewidth",1)
            lineStyle = self.getOption("linestyle","solid")
            x = self._datasource.getKeyTuple()
            values = self.getValues("y")
            tuples = self._datasource.getTuplesForFields(values)
            logging.info(str(tuples))
            for key,value in tuples.items():
                y = value
                self._axis.plot(x,y,linewidth=lineWidth,linestyle=lineStyle,solid_joinstyle="round",label=key)
            self._axis.legend(loc="upper center",bbox_to_anchor=(0.5,-0.05),fancybox=True,shadow=True,ncol=len(values))
        elif self._type == "table":
            self._axis.axis("off")
            values = self.getValues("values")
            data = self._datasource.getTableData(values)
            if len(data["rows"]) > 0:
                table = self._axis.table(cellText=data["cells"],rowLabels=data["rows"],colLabels=data["columns"],loc="center")

        self._figure.canvas.draw()

    def getValues(self,name):
        values = []

        value = self._options.get(name)

        if value != None:
            if type(value) is list:
                for v in value:
                    values.append(v)
            else:
                values.append(value)

        return(values)

    def setOption(self,name,value):
        self._options.set(name,value)

    def getOption(self,name,dv):
        return(self._options.get(name,dv))

class Dashboard(object):

    def __init__(self,charts,**kwargs):
        self._charts = charts
        self._options = tools.Options(**kwargs)
        self._rows = []
        self._figure = None

    def addRow(self,height = 5):
        row = DashboardRow(height)
        self._rows.append(row)
        return(row)

    def display(self):

        height = 0
        maxcols = 0

        for row in self._rows:
            height += row.height
            if row.size > maxcols:
                maxcols = row.size

        name = self._options.get("name")
        width = self._options.get("width",16)

        if name != None:
            self._figure = plt.figure(num=name,figsize=(width,height));
        else:
            self._figure = plt.figure(figsize=(width,height));

        dim = (len(self._rows),maxcols)

        rownum = 0

        for row in self._rows:
            colnum = 0
            for chart in row._charts:
                coordinate = (rownum,colnum)
                colspan = 1
                if colnum == (row.size - 1):
                    if colnum < maxcols:
                        colspan = (maxcols - row.size + 1)
                chart.displayInDashboard(self,dim,coordinate,1,colspan)
                colnum += 1
            rownum += 1

class DashboardRow(object):
    def __init__(self,height):
        self._height = height;
        self._charts = []

    def add(self,chart):
        self._charts.append(chart)

    def get(self,index):
        chart = None
        if index < self.size:
            chart = self._charts[index]
        return(chart)

    @property
    def height(self):
        return(self._height)

    @property
    def size(self):
        return(len(self._charts))

class ControlPanels(object):
    def __init__(self):
        self._panels = []

    def addPanel(self,datasource):
        datasource.addDelegate(self)
        panel = ControlPanel(datasource)
        self._panels.append(panel)

    def dataChanged(self,datasource):
        for p in self._panels:
            if p._datasource == datasource:
                p.processInfo()

    def infoChanged(self,datasource):
        for p in self._panels:
            if p._datasource == datasource:
                p.processInfo()

    def display(self):
        components = []
        for p in self._panels:
            components.append(p._panel)
        box = widgets.VBox(components)
        return(box)
        
class ControlPanel(object):
    def __init__(self,datasource):
        self._datasource = datasource

        self._info = None

        if tools.supports(self._datasource,"getInfo"):
            self._info = self._datasource.getInfo()

        title = ""
        if isinstance(self._datasource,connections.EventCollection):
            title += "collection: "
        else:
            title += "stream: "
        title += self._datasource._path

        self._title = widgets.Label(value=title)

        components = []

        components.append(self._title)

        self._filter = widgets.Text(description="Filter")
        b = widgets.Button(description="Set Filter")
        b.on_click(self.filter)

        components.append(widgets.HBox([self._filter,b],layout=widgets.Layout(padding="5px 5px 20px 5px")))

        self._buttons = None

        if isinstance(self._datasource,connections.EventCollection):
            self._nextButton = widgets.Button(description="Next")
            self._prevButton = widgets.Button(description="Prev")
            self._firstButton = widgets.Button(description="First")
            self._lastButton = widgets.Button(description="Last")

            self._nextButton.on_click(self.next)
            self._prevButton.on_click(self.prev)
            self._firstButton.on_click(self.first)
            self._lastButton.on_click(self.last)

            self._buttons = widgets.HBox([self._nextButton,self._prevButton,self._firstButton,self._lastButton])

            components.append(self._buttons)

        self._panel = widgets.VBox(components)

        self._filter.value = self._datasource.getFilter()

    def next(self,b):
        self._datasource.next()

    def prev(self,b):
        self._datasource.prev()

    def first(self,b):
        self._datasource.first()

    def last(self,b):
        self._datasource.last()

    def filter(self,b):
        self._datasource.setFilter(self._filter.value)
        self._datasource.load()

    def processInfo(self):
        if isinstance(self._datasource,connections.EventCollection):
            self._info = self._datasource.getInfo()

            page = int(self._info["page"])
            pages = int(self._info["pages"])

            if pages == 1:
                self._buttons.layout.display = "none"
            else:
                self._buttons.layout.display = "block"

            self._nextButton.disabled = (page == (pages - 1))
            self._prevButton.disabled = (page == 0)

            title = ""
            title += "collection: "
            title += self._datasource._path

            if pages > 1:
                title += " (Page " + str(page + 1) + " of " + str(pages) + ")"

            self._title.value = title

