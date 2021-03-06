# -*- coding: utf-8 -*-
"""
 ***************************************************************************
    MGB

    Processing
                             -------------------
        begin                : 2017-07-01
        updated              : 2019-10-28 by Leonardo Laipelt
        copyright            : (C) 2017 by HGE-IPH
        email                : martinbiancho@hotmail.com
 ***************************************************************************

 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************
"""


import os, sys, datetime
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import numpy as np

from . import resources
from . import shapefile
from matplotlib.ticker import FuncFormatter
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, Qt
from qgis.core import *
from qgis.gui import *
from pylab import *
from .MGBWidget import Widget
from .MGBWidget import Widget2
from os import path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSettings, QTranslator, QVersionNumber, QCoreApplication, Qt, QObject, pyqtSignal 




class MapToolEmitPoint(QgsMapToolEmitPoint):
    canvasDoubleClicked = pyqtSignal()
    


class MGB:

    def __init__(self, iface):

        #Save reference to the QGIS interface
        self.iface = iface
        # a reference to our map canvas
        self.canvas = self.iface.mapCanvas()
        self.dockwidget = Widget()
        
        # this QGIS tool emits as QgsPoint after each click on the map canvas
        self.toolchso = QgsMapToolEmitPoint(self.canvas)
        self.toolvhs = QgsMapToolEmitPoint(self.canvas)
        self.toolcfdso = QgsMapToolEmitPoint(self.canvas)
        self.toolvfds = QgsMapToolEmitPoint(self.canvas)
        self.toolvwdts = QgsMapToolEmitPoint(self.canvas)

        self.plugin_dir = os.path.dirname(__file__)
        self.toolbar = self.iface.addToolBar('MGB')
        self.toolbar.setObjectName('MGB')
        self.pluginIsActive = False
        self.dockwidget.treeWidget_2.activated.connect(self.process)
        self.action = None

        self.ax = None
        self.fig = None
        self.txt = None

        self.flag = 0
        self.days = None
        self.simpercent = None
        self.obspercent = None
        self.obs = None
        self.sim = None

        self.simpoints = None
        self.simxpts = list()
        self.simypts = list()

        self.dlg = Widget2()
        self.dlg.pushButton.clicked.connect(self.input)
        self.dlg.pushButton_4.clicked.connect(self.input2)
        self.dlg.pushButton_2.clicked.connect(self.output)
        self.dlg.pushButton_3.clicked.connect(self.add)

        os.chdir('C:')
        self.dir = 'C:/'
        self.plugdir = os.path.dirname(__file__)
        for i in self.plugdir:
            if i == '\\':
                self.plugdir = self.plugdir.replace('\\', '/')

    def initGui(self):

        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.action = QAction(QIcon(self.plugdir + '/icon.png'), 'MGB', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu('&IPH - Plugins', self.action)


        #self.canvasClicked=pyqtSignal('QgsPointXY')
        #triggered=pyqtSignal()

        self.toolchso.canvasClicked.connect(self.chso) #Certo
        self.toolvhs.canvasClicked.connect(self.vhs)
        self.toolcfdso.canvasClicked.connect(self.cfdso)
        self.toolvfds.canvasClicked.connect(self.vfds)
        self.toolvwdts.canvasClicked.connect(self.vwdts)

        #self.canvas.setMapTool(self.teste_function)
        #self.canvas.setMapTool(self.teste_function)
        #self.canvas.setMapTool(self.teste_function)
        #self.canvas.setMapTool(self.teste_function)
        #self.canvas.setMapTool(self.teste_function)


        
       # QObject.connect(self.toolchso, SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"), self.chso)
        #QObject.connect(self.toolvhs, SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"), self.vhs)
        #QObject.connect(self.toolcfdso, SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"), self.cfdso)
       # QObject.connect(self.toolvfds, SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"), self.vfds)
       # QObject.connect(self.toolvwdts, SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"), self.vwdts)

        #QObject.connect(self.actionChangeFeedbackController, QtCore.SIGNAL("triggered()"), self.changeFeedbackController)
        # self.actionChangeFeedbackController.triggered.connect(self.changeFeedbackController)

    def close(self):

        self.dockwidget.closingPlugin.disconnect(self.close)
        self.pluginIsActive = False

    def unload(self):

        self.iface.removePluginMenu('&IPH - Plugins', self.action)
        self.iface.removeToolBarIcon(self.action)

    def add(self):

        # self.dlg2.label_4 = 'Processing...'
        inputpoly = self.dlg.lineEdit.text()
        inputmini = self.dlg.lineEdit_3.text()
        output = self.dlg.lineEdit_2.text()
        self.dlg.lineEdit.clear()
        self.dlg.lineEdit_2.clear()
        self.dlg.lineEdit_3.clear()

        miniarq = open(inputmini, 'r')
        minidata = miniarq.read()
        miniarq.close()
        mini = minidata.split('\n')

        shp = shapefile.Reader(str(inputpoly))

        attbs = list()
        catchs = list()
        minis = list()
        xs = list()
        ys = list()
        subs = list()
        areas = list()
        uareas = list()
        rlens = list()
        rslos = list()
        alens = list()
        aslos = list()
        minijuss = list()
        orders = list()

        for i in shp.shapeRecords():
            attbs.append(i.record[0])

        lenght = len(attbs)

        auxxs = [0]*lenght
        auxys = [0]*lenght
        auxsubs = [0]*lenght
        auxareas = [0]*lenght
        auxuareas = [0]*lenght
        auxrlens = [0]*lenght
        auxrslos = [0]*lenght
        auxalens = [0]*lenght
        auxaslos = [0]*lenght
        auxminijuss = [0]*lenght
        auxorders = [0]*lenght

        for i in range(1, len(mini)-1):
            catchs.append(int(mini[i][:8]))

        for i in range(1, len(mini)-1):
            minis.append(int(mini[i][8:16])) #era mini[i][10:16]

        for i in range(1, len(mini)-1):
            xs.append(float(mini[i][16:31]))

        for i in range(1, len(mini)-1):
            ys.append(float(mini[i][31:46]))

        for i in range(1, len(mini)-1):
            subs.append(int(mini[i][46:54]))

        for i in range(1, len(mini)-1):
            areas.append(float(mini[i][54:69]))

        for i in range(1, len(mini)-1):
            uareas.append(float(mini[i][69:84]))

        for i in range(1, len(mini)-1):
            rlens.append(float(mini[i][84:99]))

        for i in range(1, len(mini)-1):
            rslos.append(float(mini[i][99:114]))

        for i in range(1, len(mini)-1):
            alens.append(float(mini[i][114:129]))

        for i in range(1, len(mini)-1):
            aslos.append(float(mini[i][129:144]))

        for i in range(1, len(mini)-1):
            minijuss.append(int(mini[i][144:152]))

        for i in range(1, len(mini)-1):
            orders.append(int(mini[i][152:160]))

        # aux = 0
        if 0 in attbs:
            # attbs.pop(0) # o primeiro valor é '0', ver se é sempre assim
            attbs[attbs.index(0)] = 1
            # aux = 1
        else:
            pass

        try:
            for i in range(len(attbs)):
                index = catchs.index(attbs[i])

                idmini = minis[index]
                x = xs[index]
                y = ys[index]
                sub = subs[index]
                area = areas[index]
                uarea = uareas[index]
                rlen = rlens[index]
                rslo = rslos[index]
                alen = alens[index]
                aslo = aslos[index]
                minijus = minijuss[index]
                order = orders[index]

                attbs[i] = idmini
                auxxs[i] = x
                auxys[i] = y
                auxsubs[i] = sub
                auxareas[i] = area
                auxuareas[i] = uarea
                auxrlens[i] = rlen
                auxrslos[i] = rslo
                auxalens[i] = alen
                auxaslos[i] = aslo
                auxminijuss[i] = minijus
                auxorders[i] = order
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Catchments polygon and MINI.gtp file don\'t match')
            return

        # if aux:
        #     attbs.insert(0, 0) # o primeiro valor é '0', ver se é sempre assim
        # else:
        #     pass

        outputarq = shapefile.Writer(shapefile.POLYGON)

        fields = shp.fields[1:]
        # fields[0][0] = 'ID_Catch'
        fields2 = [fields[0], ['ID_Mini', 'N', 10, 0], ['X_Cen', 'R', 10, 0], ['Y_Cen', 'R', 10, 0], ['Sub_Basin', 'N', 10, 0], ['Area(km²)', 'R', 10, 0], ['Upst_Area(km²)', 'R', 10, 0], ['Reach_Lenght', 'R', 10, 0], ['Reach_Slope', 'R', 10, 0], ['Acum_Lenght', 'R', 10, 0], ['Acum_Slope', 'R', 10, 0], ['Mini_Jus', 'N', 10, 0], ['Order', 'N', 10, 0]]

        outputarq.fields = fields2

        k = 0

        if len(shp.shapeRecords()) != lenght:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Catchments polygon and MINI.gtp file don\'t match')
            return
        else:
            pass

        for i in shp.shapeRecords():
            if i.record[0] == 0:
                i.record[0] = 1
            else:
                pass

            outputarq.records.append([i.record[0], attbs[k], auxxs[k], auxys[k], auxsubs[k], auxareas[k], auxuareas[k], auxrlens[k], auxrslos[k], auxalens[k], auxaslos[k], auxminijuss[k], auxorders[k]])
            outputarq._shapes.append(i.shape)
            k = k + 1

        outputarq.save(str(output))

        # self.dlg.label_4 = '-'

        QMessageBox.information(self.iface.mainWindow(), 'Done', 'Geometries successfully generated')

    def input(self):

        name = QFileDialog.getOpenFileName(parent=self.dlg, caption='Input', filter='Shapefiles (*.shp)', directory=self.dir)
        name=name[0]
        
        self.dir = os.path.dirname(name) + '/'

        for i in name:
            if i == '\\':
                name = name.replace('\\', '/')

        self.dlg.lineEdit.setText(name)

    def input2(self):

        name2 = QFileDialog.getOpenFileName(parent=self.dlg, caption='Input', filter='MINI files (*.gtp)', directory=self.dir)
        name2=name2[0]
        
        self.dir = os.path.dirname(name2) + '/'

        for i in name2:
            if i == '\\':
                name2 = name2.replace('\\', '/')

        self.dlg.lineEdit_3.setText(name2)

    def output(self):

        # name = QFileDialog.getExistingDirectory(self.dlg, 'select output')
        name = QFileDialog.getSaveFileName(parent=self.dlg, caption='Output', filter='Shapefiles (*.shp)', directory=self.dir)
        name=name[0]

        
        self.dir = os.path.dirname(name) + '/'

        for i in name:
            if i == '\\':
                name = name.replace('\\', '/')

        self.dlg.lineEdit_2.setText(name)

    def clickchso(self, event):

        # axes = plt.gca()
        # lines = axes.lines[0]
        # j = lines.get_xdata()
        # ji = j[0]
        # jf = j[len(j) - 1]
        # xmin, xmax = axes.get_xlim()
        # QMessageBox.information(self.iface.mainWindow(), 'Erro', str(a) + '   ' + str(type(a)) + '   ' + str(type(b)))
        # ttt = range(int(xmin), int(xmax))

        # self.line, = self.ax.plot(self.x_pts, self.y_pts, c='k', ms='3', marker='o')

        # plt.figtext(0.6, 0.8, 'ooo')

        # self.x_pts.append(tt)
        # self.y_pts.append(ss)
        # self.line.set_xdata(self.x_pts)
        # self.line.set_ydata(self.y_pts)
        # self.txt.set_text('x = %1.0f, y = %1.2f' %(tt, ss))

        if not event.inaxes:
            return

        try:
            self.txt.remove()
            self.fig.canvas.draw()
        except:
            pass

        temp = list()

        for i in range(len(self.days)):
            temp.append(dates.date2num(self.days[i]))

        index = (np.abs(temp - event.xdata)).argmin()
        obsdata = float(self.obs[int(index)])
        simdata = float(self.sim[int(index)])
        date = str(dates.num2date(float(temp[int(index)])))
        obs = str('%.2f' % obsdata)
        sim = str('%.2f' % simdata)
        diff = str('%.2f' % abs(simdata-obsdata))
        dateformat = date[8:10] + '/' + date[5:7] + '/' + date[:4]

        self.txt = self.ax.text(1.015, 0, '', fontsize='8.5', transform=self.ax.transAxes)
        self.txt.set_text('Date = ' + dateformat + '\nObserved flow = ' + obs + ' m3/s\nCalculated flow = ' + sim + ' m3/s\nDifference = ' + diff + ' m3/s')

        self.simxpts.append(float(temp[int(index)]))
        self.simypts.append(simdata)
        self.simxpts.append(float(temp[int(index)]))
        self.simypts.append(obsdata)
        self.simpoints.set_xdata(self.simxpts)
        self.simpoints.set_ydata(self.simypts)

        self.fig.canvas.draw()
        self.simxpts = []
        self.simypts = []

    def clickvhs(self, event):

        if not event.inaxes:
            return

        try:
            self.txt.remove()
            self.fig.canvas.draw()
        except:
            pass

        temp = list()

        for i in range(len(self.days)):
            temp.append(dates.date2num(self.days[i]))

        index = (np.abs(temp - event.xdata)).argmin()
        simdata = float(self.sim[int(index)])
        date = str(dates.num2date(float(temp[int(index)])))
        sim = str('%.2f' % simdata)
        dateformat = date[8:10] + '/' + date[5:7] + '/' + date[:4]

        self.txt = self.ax.text(1.015, 0, '', fontsize='8.5', transform=self.ax.transAxes)
        self.txt.set_text('Date = ' + dateformat + '\nCalculated flow = ' + sim + ' m3/s')

        self.simxpts.append(float(temp[int(index)]))
        self.simypts.append(simdata)
        self.simpoints.set_xdata(self.simxpts)
        self.simpoints.set_ydata(self.simypts)

        self.fig.canvas.draw()
        self.simxpts = []
        self.simypts = []

    def clickcfdso(self, event):

        if not event.inaxes:
            return

        try:
            self.txt.remove()
            self.fig.canvas.draw()
        except:
            pass

        temp = list()
        temptemp = list()

        for i in range(len(self.simpercent)):
            temp.append(float(self.simpercent[i]))

        for j in range(len(self.obspercent)):
            temptemp.append(float(self.obspercent[j]))

        index = (np.abs(temp - event.xdata)).argmin()
        indexindex = (np.abs(temptemp - event.xdata)).argmin()
        percentdata = float(temp[int(index)])
        obsdata = float(self.flc[int(indexindex)])
        simdata = float(self.sim[int(index)])
        diff = str('%.2f' % abs(simdata - obsdata))
        obs = str('%.2f' % obsdata)
        sim = str('%.2f' % simdata)
        percent = str('%.2f' % percentdata)

        self.txt = self.ax.text(1.01, 0, '', fontsize='8.5', transform=self.ax.transAxes)
        self.txt.set_text('Percentage = ' + percent + '%\nObserved flow = ' + obs + ' m3/s\nCalculated flow = ' + sim + ' m3/s\nDifference = ' + diff + ' m3/s')

        self.simxpts.append(float(temp[int(index)]))
        self.simypts.append(simdata)
        self.simxpts.append(float(temp[int(index)]))
        self.simypts.append(obsdata)
        self.simpoints.set_xdata(self.simxpts)
        self.simpoints.set_ydata(self.simypts)

        self.fig.canvas.draw()
        self.simxpts = []
        self.simypts = []

    def clickvfds(self, event):

        if not event.inaxes:
            return

        try:
            self.txt.remove()
            self.fig.canvas.draw()
        except:
            pass

        temp = list()

        for i in range(len(self.pct)):
            temp.append(float(self.pct[i]))

        index = (np.abs(temp - event.xdata)).argmin()
        percentdata = float(temp[int(index)])
        simdata = float(self.sim[int(index)])
        sim = str('%.2f' % simdata)
        percent = str('%.2f' % percentdata)

        self.txt = self.ax.text(1.015, 0, '', fontsize='8.5', transform=self.ax.transAxes)
        self.txt.set_text('Percentage = ' + percent + '%\nCalculated flow = ' + sim + ' m3/s')

        self.simxpts.append(float(temp[int(index)]))
        self.simypts.append(simdata)
        self.simpoints.set_xdata(self.simxpts)
        self.simpoints.set_ydata(self.simypts)

        self.fig.canvas.draw()
        self.simxpts = []
        self.simypts = []

    def clickvwdts(self, event):

        if not event.inaxes:
            return

        try:
            self.txt.remove()
            self.fig.canvas.draw()
        except:
            pass

        temp = list()

        for i in range(len(self.days)):
            temp.append(dates.date2num(self.days[i]))

        index = (np.abs(temp - event.xdata)).argmin()
        simdata = float(self.sim[int(index)])
        date = str(dates.num2date(float(temp[int(index)])))
        sim = str('%.2f' % simdata)
        dateformat = date[8:10] + '/' + date[5:7] + '/' + date[:4]

        self.txt = self.ax.text(1.015, 0, '', fontsize='8.5', transform=self.ax.transAxes)
        self.txt.set_text('Date = ' + dateformat + '\nWater Depth = ' + sim + ' m')

        self.simxpts.append(float(temp[int(index)]))
        self.simypts.append(simdata)
        self.simpoints.set_xdata(self.simxpts)
        self.simpoints.set_ydata(self.simypts)

        self.fig.canvas.draw()
        self.simxpts = []
        self.simypts = []

    def clickfats(self, event):

        if not event.inaxes:
            return

        try:
            self.txt.remove()
            self.fig.canvas.draw()
        except:
            pass

        temp = list()

        for i in range(len(self.days)):
            temp.append(dates.date2num(self.days[i]))

        index = (np.abs(temp - event.xdata)).argmin()
        simdata = float(self.sim[int(index)])
        date = str(dates.num2date(float(temp[int(index)])))
        sim = str('%.2f' % simdata)
        dateformat = date[8:10] + '/' + date[5:7] + '/' + date[:4]

        self.txt = self.ax.text(1.015, 0, '', fontsize='8.5', transform=self.ax.transAxes)
        self.txt.set_text('Date = ' + dateformat + '\nFlooded Area = ' + sim + ' km2')

        self.simxpts.append(float(temp[int(index)]))
        self.simypts.append(simdata)
        self.simpoints.set_xdata(self.simxpts)
        self.simpoints.set_ydata(self.simypts)

        self.fig.canvas.draw()
        self.simxpts = []
        self.simypts = []

    

    def chso(self, point, button):
        #Simulated and observed hydrographs
        
        # self.fig.canvas.mpl_connect('button_release_event', self.offpick)

        self.canvas.unsetMapTool(self.toolchso)
        idcatch = None

        #self.layer = self.iface.activeLayer()
        #self.features = self.layer.getFeatures()
        
        try:
            if self.iface.activeLayer().type() != 0:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select a vetorial layer')
                return
            elif self.iface.activeLayer().geometryType() != 2:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select a polygon vetorial layer')
                return

            for feature in self.iface.activeLayer().getFeatures():
                if QgsGeometry.fromPointXY(point).intersects(feature.geometry()):
                    try:
                        idcatch = str(feature.attribute("ID"))
                    except:
                        try:
                            idcatch = str(feature.attribute("DN"))
                        except:
                            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Field name isn\'t compatible')
                            return

            if idcatch is None:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Catchment shapefile wasn\'t intersected')
                return
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select layer')
            return

        try:
            infoarq = open('C:/MGB/Input/infoMGB.sim', 'r')
            infodata = infoarq.read()
            infoarq.close()
            infotemp = infodata.split('!CELLS THAT CORRESPONDS TO THOSE POINTS')
            # infotemp = infodata.split('!CELULAS QUE CORRESPONDEM A ESTES PONTOS')
            infotemporary = infotemp[1].split('!Number of cells where calculated flow must be substituted for the one read from file and filename')
            # infotemporary = infotemp[1].split('!Número de células onde a vazão calc deve ser subst. pela vazão lida de arquivo e nome do arquivo')
            info = infotemporary[0].split('\n')
            info.remove(' ')
            lista = list()
            for i in range(len(info)):
                if info[i] == '':
                    lista.append(i)

            for j in reversed(lista):
                del info[j]

            temp = info[len(info) - 1].split(' ')
            temp.remove('')
            info[len(info) - 1] = temp[0]

            infoo = list()

            for i in info:
                infoo.append(str(int(i)))
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'infoMGB.sim\' not found in directory \'C:/MGB/Input\'')
            return

        try:
            miniarq = open('C:/mgb/Input/MINI.gtp', 'r')
            minidata = miniarq.read()
            miniarq.close()
            mini = minidata.split('\n')

            string = str()

            for i in range(1, len(mini)):
                if mini[i][:8] == idcatch.rjust(8):
                    string = mini[i][10:16]
                    break

            stringtemp = string.split(' ')

            for k in range(len(stringtemp)):
                if stringtemp[0] == '':
                    stringtemp.remove('')

            idmini = stringtemp[0]
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'MINI.gtp\' not found in directory \'C:/MGB/Input\'')
            return

        # QMessageBox.information(self.iface.mainWindow(), 'Error', str(list(idmini)) + ' // ' + str(info))

        if idmini in infoo:
            value = infoo.index(idmini)
            # QMessageBox.information(self.iface.mainWindow(), 'Error', str(value))
            beg = 22 + (16 * value)
            end = 38 + (16 * value)
            if os.path.isfile('c:/mgb/flag/flag.txt'):
                arqsim = 'SIM_INERC_' + str(idmini) + '.TXT'
            else:
                arqsim = 'SIM_MC_' + str(idmini) + '.TXT'

            try:
                obsarq = open('C:/MGB/Input/QOBS.qob', 'r')
                obsdata = obsarq.read()
                obsarq.close()
                obstemp = obsdata.split('\n')
                vector = list()

                for j in range(1, len(obstemp) - 1):
                    vector.append(obstemp[j][beg:end])

                for i in range(len(vector)):
                    vectortemp = list(vector[i].split(' '))

                    for u in range(len(vectortemp)):
                        if vectortemp[0] == '':
                            vectortemp.remove('')

                    vector[i] = vectortemp[0]
            except:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'QOBS.qob\' not found in directory \'C:/MGB/Input\'')
                return

            try:
                simarq = open('C:/MGB/Output/' + arqsim, 'r')
                simdata = simarq.readlines()
                simarq.close()
            except:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \' ' + arqsim + ' \' not found in directory \'C:/MGB/Output\'')
                return

            try:
                ajusarq = open('C:/MGB/Output/AJUSTE.fob', 'r')
                ajusdata = ajusarq.readlines()
                ajusarq.close()
                nash = float(ajusdata[value][:10])
                nashlog = float(ajusdata[value][10:20])
                bias = float(ajusdata[value][20:])
            except:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \' AJUSTE.fob \' not found in directory \'C:/MGB/Output\'')
                return

            dayfirst = datetime.datetime(int(str(simdata[0][14:18])), int(str(simdata[0][10:12])), int(str(simdata[0][4:6])))
            self.days = [dayfirst + datetime.timedelta(days=i) for i in range(len(simdata))]
            dayarrayfirst = str(self.days[0])
            dayarraylast = str(self.days[len(self.days) - 1])
            datefirst = datetime.datetime(int(dayarrayfirst[:4]), int(dayarrayfirst[5:7]), int(dayarrayfirst[8:10]))
            datelast = datetime.datetime(int(dayarraylast[:4]), int(dayarraylast[5:7]), int(dayarraylast[8:10]))
            datedelta = datelast - datefirst
            datedeltatemp = datedelta.days + 1
            self.dayarraydelta = list(range(datedeltatemp))

            self.fig = plt.figure(figsize=(11.5, 5))
            self.ax = self.fig.add_subplot(111)
            format = dates.DateFormatter('%d/%m/%y')
            self.ax.xaxis.set_major_formatter(format)
            # self.fig.autofmt_xdate(rotation=10) #usamos matplotlib 2.0.2

            plt.title('Hydrograph - Unit Catchment ID: ' + str(idmini))
            plt.xlabel('Date')
            plt.ylabel('Flow (cubic meters/second)')
            plt.grid(True, axis='both')
            
            plt.figtext(.84, 0.75, 'Nash: ' + str(nash))
            plt.figtext(.84, 0.71, 'Nash-Log: ' + str(nashlog))
            plt.figtext(.84, 0.67, 'Bias: ' + str(bias) + ' %')

            plt.subplots_adjust(bottom=0.12)
            plt.subplots_adjust(right=0.83)
            plt.subplots_adjust(top=0.9)
            plt.subplots_adjust(left=0.1)

            #with open('C:/MGB/Output/' + arqsim, 'r') as raw_data:
                #data = [line.strip().split() for line in raw_data.readlines()]

            #self.sim = [record[3] for record in data]
            self.sim = [float('nan') if string[25:] == '-1.000000' else float(string[22:]) for string in simdata]
            self.obs = [float('nan') if string == '-1.000000' else float(string) for string in vector]
            
            #days=['jan','fev','mar']
            #sim2=[1,2,3]

            #ax.plot(self.days, self.sim, c='r', label='SIM', linewidth=0.45)

            self.ax.plot(self.days, self.sim, c='r', label='SIM', linewidth=0.45)
            self.ax.plot(self.days, self.obs, c='b', label='OBS', linewidth=0.45)
            self.simpoints, = self.ax.plot(self.simxpts, self.simypts, marker="o")
            
            plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)
            tit = plt.gcf()
            tit.canvas.set_window_title('MGB')
            plt.connect('button_press_event', self.clickchso)
            
            plt.show()
        else:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'No data available')

    def vhs(self, point, button):

        #Visualize Calculated Hydrographs only

        self.canvas.unsetMapTool(self.toolvhs)
        idcatch = None

        #self.layer = self.iface.activeLayer()
        #self.features = self.layer.getFeatures()

        #try:
        if self.iface.activeLayer().type() != 0:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select a vetorial layer')
            return
        elif self.iface.activeLayer().geometryType() != 2:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select a polygon vetorial layer')
            return

        for feature in self.iface.activeLayer().getFeatures():
            if QgsGeometry.fromPointXY(point).intersects(feature.geometry()):
                try:
                    idcatch = str(feature.attribute("ID"))
                except:
                    try:
                        idcatch = str(feature.attribute("DN"))
                    except:
                        QMessageBox.information(self.iface.mainWindow(), 'Error', 'Field name isn\'t compatible')
                        return

        if idcatch is None:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Catchment shapefile wasn\'t intersected')
            return
        #except:
            #QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select layer')
            #return

        try:
            infoarq = open('C:/MGB/Input/infoMGB.sim', 'r')
            infodata = infoarq.read()
            infoarq.close()
            infotemp = infodata.split('!CELLS THAT CORRESPONDS TO THOSE POINTS')
            infotemporary = infotemp[1].split('!Number of cells where calculated flow must be substituted for the one read from file and filename')
            info = infotemporary[0].split('\n')
            info.remove(' ')
            lista = list()
            for i in range(len(info)):
                if info[i] == '':
                    lista.append(i)

            for j in reversed(lista):
                del info[j]

            temp = info[len(info) - 1].split(' ')
            temp.remove('')
            info[len(info) - 1] = temp[0]

            infoo = list()

            for i in info:
                infoo.append(str(int(i)))
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'infoMGB.sim\' not found in directory \'C:/MGB/Input\'')
            return

        try:
            miniarq = open('C:/MGB/Input/MINI.gtp', 'r')
            minidata = miniarq.read()
            miniarq.close()
            mini = minidata.split('\n')
            string = str()

            for i in range(1, len(mini)):
                if mini[i][:8] == idcatch.rjust(8):
                    string = mini[i][10:16]
                    break

            minitemp = string.split(' ')

            for j in range(len(minitemp)):
                if minitemp[0] == '':
                    minitemp.remove('')

            idmini = minitemp[0]
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'MINI.gtp\' not found in directory \'C:/MGB/Input\'')
            return

        if idmini in infoo:
            value = infoo.index(idmini)
            if os.path.isfile('c:/mgb/flag/flag.txt'):
                arqsim = 'SIM_INERC_' + str(idmini) + '.TXT'
            else:
                arqsim = 'SIM_MC_' + str(idmini) + '.TXT'

            try:
                simarq = open('C:/MGB/Output/' + arqsim, 'r')
                simdata = simarq.readlines()
                simarq.close()
            except:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \' ' + arqsim + ' \' not found in directory \'C:/MGB/Output\'')
                return

            try:
                ajusarq = open('C:/MGB/Output/AJUSTE.fob', 'r')
                ajusdata = ajusarq.readlines()
                ajusarq.close()
                nash = float(ajusdata[value][:10])
                nashlog = float(ajusdata[value][10:20])
                bias = float(ajusdata[value][20:])
            except:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \' AJUSTE.fob \' not found in directory \'C:/MGB/Output\'')
                return

            dayfirst = datetime.datetime(int(str(simdata[0][14:18])), int(str(simdata[0][10:12])), int(str(simdata[0][4:6])))
            self.days = [dayfirst + datetime.timedelta(days=i) for i in range(len(simdata))]
            dayarrayfirst = str(self.days[0])
            dayarraylast = str(self.days[len(self.days) - 1])
            datefirst = datetime.datetime(int(dayarrayfirst[:4]), int(dayarrayfirst[5:7]), int(dayarrayfirst[8:10]))
            datelast = datetime.datetime(int(dayarraylast[:4]), int(dayarraylast[5:7]), int(dayarraylast[8:10]))
            datedelta = datelast - datefirst
            datedeltatemp = datedelta.days + 1
            self.dayarraydelta = list(range(datedeltatemp))

            format = dates.DateFormatter('%d/%m/%y')
            self.fig = plt.figure(figsize=(11.5, 5))
            self.ax = self.fig.add_subplot(111)
            self.ax.xaxis.set_major_formatter(format)
            # self.fig.autofmt_xdate(rotation=10)

            plt.title('Hydrograph - Unit Catchment ID: ' + str(idmini))
            plt.xlabel('Date')
            plt.ylabel('Flow (cubic meters/second)')
            plt.grid(True, axis='both')
            plt.figtext(.84, 0.75, 'Nash: ' + str(nash))
            plt.figtext(.84, 0.71, 'Nash-Log: ' + str(nashlog))
            plt.figtext(.84, 0.67, 'Bias: ' + str(bias) + ' %')

            plt.subplots_adjust(bottom=0.12)
            plt.subplots_adjust(right=0.83)
            plt.subplots_adjust(top=0.9)
            plt.subplots_adjust(left=0.1)

            self.sim = [float('nan') if string[25:] == '-1.000000' else float(string[22:]) for string in simdata]

            self.ax.plot(self.days, self.sim, c='r', label='SIM', linewidth=0.45)
            self.simpoints, = self.ax.plot(self.simxpts, self.simypts, marker="o")

            plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)
            tit = plt.gcf()
            tit.canvas.set_window_title('MGB')
            plt.connect('button_press_event', self.clickvhs)

            plt.show()
        else:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'No data available')

    def cfdso(self, point, button):

        #Compare Flow Duration Curves

        self.canvas.unsetMapTool(self.toolcfdso)
        idcatch = None

        #self.layer = self.iface.activeLayer()
        #self.features = self.layer.getFeatures()

        try:
            if self.iface.activeLayer().type() != 0:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select a vector layer')
                return
            elif self.iface.activeLayer().geometryType() != 2:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select a polygon vector layer')
                return

            for feature in self.iface.activeLayer().getFeatures():
                if QgsGeometry.fromPointXY(point).intersects(feature.geometry()):
                    try:
                        idcatch = str(feature.attribute("ID"))
                    except:
                        try:
                            idcatch = str(feature.attribute("DN"))
                        except:
                            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Field name isn\'t compatible')
                            return

            if idcatch is None:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Catchment shapefile wasn\'t intersected')
                return
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select layer')
            return

        try:
            infoarq = open('C:/MGB/Input/infoMGB.sim', 'r')
            infodata = infoarq.read()
            infoarq.close()
            infotemp = infodata.split('!CELLS THAT CORRESPONDS TO THOSE POINTS')
            infotemporary = infotemp[1].split('!Number of cells where calculated flow must be substituted for the one read from file and filename')
            info = infotemporary[0].split('\n')
            info.remove(' ')
            lista = list()
            for i in range(len(info)):
                if info[i] == '':
                    lista.append(i)

            for j in reversed(lista):
                del info[j]

            temp = info[len(info) - 1].split(' ')
            temp.remove('')
            info[len(info) - 1] = temp[0]

            infoo = list()

            for i in info:
                infoo.append(str(int(i)))
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'infoMGB.sim\' not found in directory \'C:/MGB/Input\'')
            return

        try:
            miniarq = open('C:/MGB/Input/MINI.gtp', 'r')
            minidata = miniarq.read()
            miniarq.close()
            mini = minidata.split('\n')
            string = str()

            for i in range(1, len(mini)):
                if mini[i][:8] == idcatch.rjust(8):
                    string = mini[i][10:16]
                    break

            stringtemp = string.split(' ')

            for j in range(len(stringtemp)):
                if stringtemp[0] == '':
                    stringtemp.remove('')

            idmini = stringtemp[0]
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'MINI.gtp\' not found in directory \'C:/MGB/Input\'')
            return

        if idmini in infoo:
            value = infoo.index(idmini)
            beg = 22 + (16 * value)
            end = 38 + (16 * value)
            if os.path.isfile('c:/mgb/flag/flag.txt'):
                arqsim = 'SIM_INERC_' + str(idmini) + '.TXT'
            else:
                arqsim = 'SIM_MC_' + str(idmini) + '.TXT'

            try:
                obsarq = open('C:/MGB/Input/QOBS.qob', 'r')
                obsdata = obsarq.read()
                obsarq.close()
                obs = obsdata.split('\n')
                vector = list()

                for i in range(1, len(obs) - 1):
                    vector.append(float(obs[i][beg:end]))
            except:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'QOBS.qob\' not found in directory \'C:/MGB/Input\'')
                return

            try:
                simarq = open('C:/MGB/Output/' + arqsim, 'r')
                simdata = simarq.readlines()
                simarq.close()
            except:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \' ' + arqsim + ' \' not found in directory \'C:/MGB/Output\'')
                return

            self.fig = plt.figure(figsize=(11.5, 5))
            self.ax = self.fig.add_subplot(111)
            plt.title('Flow Duration - Unit Catchment ID: ' + str(idmini))
            plt.xlabel('Percentage (%)')
            plt.ylabel('Flow (cubic meters/second)')
            plt.grid(True, axis='both')
            self.ax.set_yscale('log')

            plt.subplots_adjust(bottom=0.1)
            plt.subplots_adjust(right=0.83)
            plt.subplots_adjust(top=0.9)
            plt.subplots_adjust(left=0.1)

            # self.sim = [float('nan') if x[25:] == '-1.000000' else x[22:] for x in ur]
            # self.obs = [float('nan') if x == '    -1.000000' else x for x in fl]

            self.flc = list()
            self.sim = list()
            self.simpercent = list()
            self.obspercent = list()

            for i in range(len(vector)):
                if float(vector[i]) != -1:
                    self.flc.append(float(vector[i]))
                    self.sim.append(float(simdata[i][22:]))

            # if self.flc == []:
            #     QMessageBox.information(self.iface.mainWindow(), 'Error', 'Observed discharge data is empty')
            #     return

            simbase = list(range(1, len(self.sim)+1))
            obsbase = list(range(1, len(self.flc)+1))

            d = float(len(self.sim) + 1)
            q = float(len(self.flc) + 1)

            self.simpercent = [float(float(i)*100/d) for i in simbase]
            self.obspercent = [float(float(j)*100/q) for j in obsbase]

            self.sim.sort(reverse=1)
            self.flc.sort(reverse=1)

            self.ax.plot(self.simpercent, self.sim, c='r', label='SIM', linewidth=0.45)
            self.ax.plot(self.obspercent, self.flc, c='b', label='OBS', linewidth=0.45)
            self.simpoints, = self.ax.plot(self.simxpts, self.simypts, marker="o")

            plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)
            tit = plt.gcf()
            tit.canvas.set_window_title('MGB')
            plt.connect('button_press_event', self.clickcfdso)

            plt.show()
        else:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'No data available')

    def vfds(self, point, button):

        #Visualize calculated flow duration only

        self.canvas.unsetMapTool(self.toolvfds)
        idcatch = None

        try:
            if self.iface.activeLayer().type() != 0:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select a vetorial layer')
                return
            elif self.iface.activeLayer().geometryType() != 2:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select a polygon vetorial layer')
                return

            for feature in self.iface.activeLayer().getFeatures():
                if QgsGeometry.fromPointXY(point).intersects(feature.geometry()):
                    try:
                        idcatch = str(feature.attribute("ID"))
                    except:
                        try:
                            idcatch = str(feature.attribute("DN"))
                        except:
                            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Field name isn\'t compatible')
                            return

            if idcatch is None:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Catchment shapefile wasn\'t intersected')
                return
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select layer')
            return

        try:
            infoarq = open('C:/MGB/Input/infoMGB.sim', 'r')
            infodata = infoarq.read()
            infoarq.close()
            infotemp = infodata.split('!CELLS THAT CORRESPONDS TO THOSE POINTS')
            infotemporary = infotemp[1].split('!Number of cells where calculated flow must be substituted for the one read from file and filename')
            info = infotemporary[0].split('\n')
            info.remove(' ')
            lista = list()
            for i in range(len(info)):
                if info[i] == '':
                    lista.append(i)

            for j in reversed(lista):
                del info[j]

            temp = info[len(info) - 1].split(' ')
            temp.remove('')
            info[len(info) - 1] = temp[0]

            infoo = list()

            for i in info:
                infoo.append(str(int(i)))
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'infoMGB.sim\' not found in directory \'C:/MGB/Input\'')
            return

        try:
            miniarq = open('C:/MGB/Input/MINI.gtp', 'r')
            minidata = miniarq.read()
            miniarq.close()
            mini = minidata.split('\n')
            string = str()

            for i in range(1, len(mini)):
                if mini[i][:8] == idcatch.rjust(8):
                    string = mini[i][10:16]
                    break

            stringtemp = string.split(' ')

            for j in range(len(stringtemp)):
                if stringtemp[0] == '':
                    stringtemp.remove('')

            idmini = stringtemp[0]
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'MINI.gtp\' not found in directory \'C:/MGB/Input\'')
            return

        if idmini in infoo:
            if os.path.isfile('c:/mgb/flag/flag.txt'):
                arqsim = 'SIM_INERC_' + str(idmini) + '.TXT'
            else:
                arqsim = 'SIM_MC_' + str(idmini) + '.TXT'

            try:
                simarq = open('C:/MGB/Output/' + arqsim, 'r')
                simdata = simarq.readlines()
                simarq.close()
            except:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \' ' + arqsim + ' \' not found in directory \'C:/MGB/Output\'')
                return

            self.fig = plt.figure(figsize=(11.5, 5))
            self.ax = self.fig.add_subplot(111)
            plt.title('Flow Duration - Unit Catchment ID: ' + str(idmini))
            plt.xlabel('Percentage (%)')
            plt.ylabel('Flow (cubic meters/second)')
            plt.grid(True, axis='both')
            self.ax.set_yscale('log')

            plt.subplots_adjust(bottom=0.1)
            plt.subplots_adjust(right=0.83)
            plt.subplots_adjust(top=0.9)
            plt.subplots_adjust(left=0.1)

            # self.sim = [float('nan') if string[25:] == '-1.000000' else string[22:] for string in simdata]

            self.pct = list()
            self.sim = list()

            for i in range(len(simdata)):
                self.sim.append(float(simdata[i][22:]))

            simbase = list(range(1, len(simdata)+1))

            d = float(len(simdata))

            self.pct = [float(float(i)*100/d) for i in simbase]

            self.sim.sort(reverse=1)

            self.ax.plot(self.pct, self.sim, c='r', label='SIM', linewidth=0.45)
            self.simpoints, = self.ax.plot(self.simxpts, self.simypts, marker="o")

            plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)
            tit = plt.gcf()
            tit.canvas.set_window_title('MGB')
            plt.connect('button_press_event', self.clickvfds)

            plt.show()
        else:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'No data available')

    def vwdts(self, point, button):

        #Visualize water depth times series (only after Inertial simulation)

        if os.path.isfile('c:/mgb/flag/flag.txt'):
            pass
        else:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Inertial simulation not detected')
            return

        self.canvas.unsetMapTool(self.toolvwdts)
        idcatch = None

        try:
            if self.iface.activeLayer().type() != 0:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select a vetorial layer')
                return
            elif self.iface.activeLayer().geometryType() != 2:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select a polygon vetorial layer')
                return

            for feature in self.iface.activeLayer().getFeatures():
                if QgsGeometry.fromPointXY(point).intersects(feature.geometry()):
                    try:
                        idcatch = str(feature.attribute("ID"))
                    except:
                        try:
                            idcatch = str(feature.attribute("DN"))
                        except:
                            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Field name isn\'t compatible')
                            return

            if idcatch is None:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'Catchment shapefile wasn\'t intersected')
                return
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Please select layer')
            return

        try:
            infoarq = open('C:/MGB/Input/infoMGB.sim', 'r')
            infodata = infoarq.read()
            infoarq.close()
            infotemp = infodata.split('!CELLS THAT CORRESPONDS TO THOSE POINTS')
            infotemporary = infotemp[1].split('!Number of cells where calculated flow must be substituted for the one read from file and filename')
            info = infotemporary[0].split('\n')
            info.remove(' ')
            lista = list()
            for i in range(len(info)):
                if info[i] == '':
                    lista.append(i)

            for j in reversed(lista):
                del info[j]

            temp = info[len(info) - 1].split(' ')
            temp.remove('')
            info[len(info) - 1] = temp[0]

            infoo = list()

            for i in info:
                infoo.append(str(int(i)))
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'infoMGB.sim\' not found in directory \'C:/MGB/Input\'')
            return

        try:
            miniarq = open('C:/mgb/Input/MINI.gtp', 'r')
            minidata = miniarq.read()
            miniarq.close()
            mini = minidata.split('\n')

            string = str()

            for i in range(1, len(mini)):
                if mini[i][:8] == idcatch.rjust(8):
                    string = mini[i][10:16]
                    break

            stringtemp = string.split(' ')

            for k in range(len(stringtemp)):
                if stringtemp[0] == '':
                    stringtemp.remove('')

            idmini = stringtemp[0]
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \'MINI.gtp\' not found in directory \'C:/MGB/Input\'')
            return

        if idmini in infoo:
            arqsim = 'SIM_INERC_Hfl_' + str(idmini) + '.TXT'
            try:
                simarq = open('C:/MGB/Output/' + arqsim, 'r')
                simdata = simarq.readlines()
                simarq.close()
            except:
                QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \' ' + arqsim + ' \' not found in directory \'C:/MGB/Output\'')
                return

            dayfirst = datetime.datetime(int(str(simdata[0][14:18])), int(str(simdata[0][10:12])), int(str(simdata[0][4:6])))
            self.days = [dayfirst + datetime.timedelta(days=i) for i in range(len(simdata))]
            dayarrayfirst = str(self.days[0])
            dayarraylast = str(self.days[len(self.days) - 1])
            datefirst = datetime.datetime(int(dayarrayfirst[:4]), int(dayarrayfirst[5:7]), int(dayarrayfirst[8:10]))
            datelast = datetime.datetime(int(dayarraylast[:4]), int(dayarraylast[5:7]), int(dayarraylast[8:10]))
            datedelta = datelast - datefirst
            datedeltatemp = datedelta.days + 1
            self.dayarraydelta = list(range(datedeltatemp))

            format = dates.DateFormatter('%d/%m/%y')
            self.fig = plt.figure(figsize=(11.5, 5))
            self.ax = self.fig.add_subplot(111)
            self.ax.xaxis.set_major_formatter(format)
            # self.fig.autofmt_xdate(rotation=10)
            plt.title('Calculated Water Depth - Unit Catchment ID: ' + str(idmini))
            plt.xlabel('Date')
            plt.ylabel('Water Depth (meters)')
            plt.grid(True, axis='both')

            plt.subplots_adjust(bottom=0.12)
            plt.subplots_adjust(right=0.83)
            plt.subplots_adjust(top=0.9)
            plt.subplots_adjust(left=0.1)

            self.sim = [float('nan') if string[25:] == '-1.000000' else float(string[22:]) for string in simdata]

            self.ax.plot(self.days, self.sim, c='r', label='SIM', linewidth=0.45)
            self.simpoints, = self.ax.plot(self.simxpts, self.simypts, marker="o")

            plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)
            tit = plt.gcf()
            tit.canvas.set_window_title('MGB')
            plt.connect('button_press_event', self.clickvwdts)

            plt.show()

    def fats(self):
        if os.path.isfile('c:/mgb/flag/flag.txt'):
            pass
        else:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'Inertial simulation not detected')
            return

        arqsim = 'TOTAL_FLOODED_AREAS.FLOOD'
        # arqsim = 'PL_FLOODEDAREAS.MGB'

        try:
            simarq = open('C:/MGB/Output/' + arqsim, 'r')
            simdata = simarq.readlines()
            simarq.close()
        except:
            QMessageBox.information(self.iface.mainWindow(), 'Error', 'File \' ' + arqsim + ' \' not found in directory \'C:/MGB/Output\'')
            return

        reply = QMessageBox.question(self.iface.mainWindow(), 'Plot graph', 'Plot flooded area time series for all the basin?', QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            pass
        else:
            return

        dayfirst = datetime.datetime(int(str(simdata[0][14:18])), int(str(simdata[0][10:12])), int(str(simdata[0][4:6])))
        self.days = [dayfirst + datetime.timedelta(days=i) for i in range(len(simdata))]
        dayarrayfirst = str(self.days[0])
        dayarraylast = str(self.days[len(self.days) - 1])
        datefirst = datetime.datetime(int(dayarrayfirst[:4]), int(dayarrayfirst[5:7]), int(dayarrayfirst[8:10]))
        datelast = datetime.datetime(int(dayarraylast[:4]), int(dayarraylast[5:7]), int(dayarraylast[8:10]))
        datedelta = datelast - datefirst
        datedeltatemp = datedelta.days + 1
        self.dayarraydelta = list(range(datedeltatemp))

        format = dates.DateFormatter('%d/%m/%y')
        self.fig = plt.figure(figsize=(11.5, 5))
        self.ax = self.fig.add_subplot(111)
        self.ax.xaxis.set_major_formatter(format)
        # self.fig.autofmt_xdate(rotation=10)
        plt.title('Calculated Flooded Area (for the all basin)')
        plt.xlabel('Date')
        plt.ylabel('Flooded Area (square kilometers)')
        plt.grid(True, axis='both')

        plt.subplots_adjust(bottom=0.12)
        plt.subplots_adjust(right=0.85)
        plt.subplots_adjust(top=0.9)
        plt.subplots_adjust(left=0.1)

        self.sim = [float('nan') if string[25:] == '-1.000000' else float(string[22:]) for string in simdata]

        self.ax.plot(self.days, self.sim, c='r', label='SIM', linewidth=0.45)
        self.simpoints, = self.ax.plot(self.simxpts, self.simypts, marker="o")

        plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)
        tit = plt.gcf()
        tit.canvas.set_window_title('MGB')
        plt.connect('button_press_event', self.clickfats)

        plt.show()

    def process(self):

        # subprocess.call(['runas', '/user:Administrator', 'D:/Guilherme Martinbiancho/Fortran/Fortran/Fortran/x64/Release/Fortran.exe'])

        if str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Compare simulated and observed hydrographs', Qt.MatchRecursive,
                                                       0)):
            self.canvas.setMapTool(self.toolchso)

        # elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(self.dockwidget.treeWidget_2.findItems('Generate geometry (MINI.gtp) shapefile', Qt.MatchRecursive, 0)):
        #     os.startfile(self.plugdir + '/bin/.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Update Unit-catchments Polygon', Qt.MatchRecursive, 0)):
            self.dlg.show()

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('HRCs description', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_blo.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('ANA data acquisition (Discharge data for Brazil)',
                                                       Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Down_ANA.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Using ANA data (Brazil)', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_plu.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Using MERGE data (South America)', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/merge_interplu.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Using TRMM data (Global)', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/DadosTRMM.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Discharge', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_flu.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Using INMET climatology database (Brazil)', Qt.MatchRecursive,
                                                       0)):
            os.startfile(self.plugdir + '/bin/Form_cliauto.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Using CRU climatology database (Global)', Qt.MatchRecursive,
                                                       0)):
            os.startfile(self.plugdir + '/bin/CRU_Data.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Using Daily data', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_cli.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Vegetation Parameters', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_parfix.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Soil Parameters', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_parcal.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Create/Edit Simulation Project', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_proj.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Run Simulation', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_simu.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Compare flow duration curves', Qt.MatchRecursive, 0)):
            self.canvas.setMapTool(self.toolcfdso)

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Visualize calculated hydrographs only', Qt.MatchRecursive, 0)):
            self.canvas.setMapTool(self.toolvhs)

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Visualize calculated flow duration curves only',
                                                       Qt.MatchRecursive, 0)):
            self.canvas.setMapTool(self.toolvfds)

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems(
                        'Visualize water depth time series (only after Inertial simulation)', Qt.MatchRecursive, 0)):
            self.canvas.setMapTool(self.toolvwdts)

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems(
                        'Visualize flooded area time series (only after Inertial simulation)', Qt.MatchRecursive, 0)):
            self.fats()

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Flood postprocessing (only after Inertial simulation)',
                                                       Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_Flood3.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Automatic calibration parameteres', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_calib.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Geometry file editor', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_Editor.exe')

        # elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(self.dockwidget.treeWidget_2.findItems('Flow gauge hydrograph', Qt.MatchRecursive, 0)):
        #     os.startfile(self.plugdir + '/bin/.exe')

        # elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(self.dockwidget.treeWidget_2.findItems('Base flow filter for flow gauges', Qt.MatchRecursive, 0)):
        #     os.startfile(self.plugdir + '/bin/.exe')

        # elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(self.dockwidget.treeWidget_2.findItems('Flow duration curves from flow gauges data', Qt.MatchRecursive, 0)):
        #     os.startfile(self.plugdir + '/bin/.exe')

        # elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(self.dockwidget.treeWidget_2.findItems('Rainfall gauge chart', Qt.MatchRecursive, 0)):
        #     os.startfile(self.plugdir + '/bin/.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Create precipitation data raster', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/CriarRasterSaida.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Internal database', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_BaseInterna.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('Longitudinal profile', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Perfil_Longitudinal.exe')

        elif str('[' + str(self.dockwidget.treeWidget_2.currentItem()) + ']') == str(
                self.dockwidget.treeWidget_2.findItems('>> About', Qt.MatchRecursive, 0)):
            os.startfile(self.plugdir + '/bin/Form_ini.exe')

    def run(self):

        if not self.pluginIsActive:
            self.pluginIsActive = True
            self.dockwidget.closingPlugin.connect(self.close)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            # self.iface.addDockWidget(Qt.DockWidgetArea_Mask, self.dockwidget)
            self.dockwidget.show()
