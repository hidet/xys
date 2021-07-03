import signal
import os
import time
import sys
import numpy as np
import pandas as pd
import scipy.special
from scipy.interpolate import interp1d


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import matplotlib
matplotlib.use("Qt5Agg")

import matplotlib.cm as cm
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import xraylib as xrl

import default
import material
import line_wrap
from line_wrap import voigt

sigma_from_fwhm=2.*np.sqrt(2.*np.log(2))



class ApplicationWindow(QMainWindow):
    def __init__(self, parent=None):
        super(ApplicationWindow, self).__init__(parent)
        
        QMainWindow.__init__(self)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setWindowTitle("xray yield simulation")
             
        self.resize(1200, 750)
        
        self.er_low=0.1# keV
        self.er_high=20.# keV
        self.er_step=0.001# keV
        self.enes_keV=np.arange(self.er_low,self.er_high+self.er_low+self.er_step,self.er_step)
        self.qeout=np.zeros_like(self.enes_keV)# for output
        self.flout=np.zeros_like(self.enes_keV)# for output
        # IUPAC macro
        self.LINES=['KL3','KL2','KM3','KM2',
                    'L3M5','L3M4','L2M4','L3N5',
                    'L1M3','L1M2','L2N4','L3M1']
        # Siegbahn
        self.SGBLINES=['KA1','KA2','KB1','KB3',
                       'LA1','LA2','LB1','LB2',
                       'LB3','LB4','LG1','LL']

        # radionuclide list
        self.RDNLIST=list(xrl.GetRadioNuclideDataList())
        #['55Fe','57Co','109Cd','125I','137Cs',
        #'133Ba','153Gd','238Pu','241Am','244Cm']
        # half life
        self.RDNHL=[1006.70,272.11,463.26,59.49,11018.3,
                    3854.7,239.472,32031.74,157857.678,6610.52]# days

        # universal parameters
        self.rad_duration=3600.# sec
        self.beam_duration=7200.# sec
        self.detector_resolution=8.0# eV
        self.detector_solidangle=1.0
        
        self.csvd="./csv/"
        IUPACdf=pd.read_csv(self.csvd+"IUPAC_macro.csv")
        self.IUPACmac=IUPACdf['IUPAC_macro'].values
        self.allLINES=[xrl.__getattribute__(mac) for mac in self.IUPACmac] 
        
        # ---- layout ----
        # main widget
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()

          
        # target, detector, filter materials
        topleft=QWidget()
        topleftbox=QVBoxLayout()


        self.fopenButton = QPushButton("Load csv file")
        self.fopenButton.clicked.connect(self.openFileNameDialog)
        
        self.default_none          = "None (reset all)"
        self.default_tes_jparc_mlf = "TES(Bi) J-PARC MLF"
        self.default_tes_spring8   = "TES(Bi) Spring-8"
        self.default_tes_sn        = "TES(Sn)"
        self.default_cdte          = "CdTe"
        self.default_ge            = "Ge"
        self.default_si            = "Si"
        self.chkbox0 = QCheckBox(self.default_none)
        self.chkbox1 = QCheckBox(self.default_tes_jparc_mlf)
        self.chkbox2 = QCheckBox(self.default_tes_spring8)
        self.chkbox3 = QCheckBox(self.default_tes_sn)
        self.chkbox4 = QCheckBox(self.default_cdte)
        self.chkbox5 = QCheckBox(self.default_ge)
        self.chkbox6 = QCheckBox(self.default_si)
        self.chkbg = QButtonGroup()
        self.chkbg.addButton(self.chkbox0,1)
        self.chkbg.addButton(self.chkbox1,2)
        self.chkbg.addButton(self.chkbox2,3)
        self.chkbg.addButton(self.chkbox3,4)
        self.chkbg.addButton(self.chkbox4,5)
        self.chkbg.addButton(self.chkbox5,6)
        self.chkbg.addButton(self.chkbox6,7)
        self.chkbg.buttonClicked[QAbstractButton].connect(self.btngroup)
        self.chkbox0.setChecked(True)
        ltboxw=QWidget()
        ltbox=QVBoxLayout(ltboxw)
        ltbox.setContentsMargins(0, 0, 0, 0)
        ltbox.addWidget(QLabel("Default setting"))
        ltbox.addWidget(self.fopenButton)
        ltbox.addWidget(self.chkbox0)
        ltbox.addWidget(self.chkbox1)
        ltbox.addWidget(self.chkbox2)
        ltboxw_02=QWidget()
        ltbox_02=QHBoxLayout(ltboxw_02)
        ltbox_02.setContentsMargins(0, 0, 0, 0)
        ltbox_02.addWidget(self.chkbox3)
        ltbox_02.addWidget(self.chkbox4)
        ltbox_02.addWidget(self.chkbox5)
        ltbox_02.addWidget(self.chkbox6)
                
        ltboxw2=QWidget()
        ltbox2=QVBoxLayout(ltboxw2)
        qtab=QTabWidget()
        self.bem={}
        self.tgt={}
        self.det={}
        self.bet={}
        self.rad={}
        self.dets=[]
        self.bets=[]
        self.rads=[]
        self.bemtab=material.MaterialTabWidget(parent=self,name='bem')
        self.tgttab=material.MaterialTabWidget(parent=self,name='tgt')
        self.dettab=material.MaterialTabWidget(parent=self,name='det')
        self.bettab=material.MaterialTabWidget(parent=self,name='bet')
        self.radtab=material.MaterialTabWidget(parent=self,name='rad')
        qtab.addTab(self.dettab,'Detector')
        qtab.addTab(self.tgttab,'Target')
        qtab.addTab(self.bettab,'Filter')
        qtab.addTab(self.radtab,'RadioNucl')
        qtab.addTab(self.bemtab,'Beam')
        ltbox2.addWidget(qtab)
        
        topleftbox.addWidget(ltboxw)
        topleftbox.addWidget(ltboxw_02)
        topleftbox.addWidget(ltboxw2)
        topleft.setLayout(topleftbox)


        plotButton = QPushButton("Plot")
        plotButton.clicked.connect(self._plot_trans_fluor)
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self._save_trans_fluor)
        #plotButton = QPushButton("Plot transmission")
        #plotButton.clicked.connect(self._update_trans_cv)
        #fluorButton = QPushButton("Plot flurorescence")
        #fluorButton.clicked.connect(self._update_fluor_cv)
        
        # energy range
        rangebox=QHBoxLayout()
        self.ene_range_low_le = QLineEdit()
        self.ene_range_low_le.setValidator(QDoubleValidator(0.,800.,999))
        self.ene_range_low_le.returnPressed.connect(self.apply_enerangelow)
        self.ene_range_low_le.setText("0.1")
        self.ene_range_high_le = QLineEdit()
        self.ene_range_high_le.setValidator(QDoubleValidator(0.,800.,999))
        self.ene_range_high_le.returnPressed.connect(self.apply_enerangehigh)
        self.ene_range_high_le.setText("20.")
        self.ene_range_step_le = QLineEdit()
        self.ene_range_step_le.setValidator(QDoubleValidator(0.,800.,999))
        self.ene_range_step_le.returnPressed.connect(self.apply_enerangestep)
        self.ene_range_step_le.setText("0.001")
        rangebox.addWidget(QLabel("Low:"))
        rangebox.addWidget(self.ene_range_low_le)
        rangebox.addWidget(QLabel("High:"))
        rangebox.addWidget(self.ene_range_high_le)
        rangebox.addWidget(QLabel("Step:"))
        rangebox.addWidget(self.ene_range_step_le)

        # detector resolution
        self.detector_resolution_le = QLineEdit()
        self.detector_resolution_le.setValidator(QDoubleValidator(0.,1e5,999))
        self.detector_resolution_le.returnPressed.connect(self.apply_detector_resolution)
        self.detector_resolution_le.setText(str(self.detector_resolution))
        # detector solidangle
        self.detector_solidangle_le = QLineEdit()
        self.detector_solidangle_le.setValidator(QDoubleValidator(0.,1.,999))
        self.detector_solidangle_le.returnPressed.connect(self.apply_detector_solidangle)
        self.detector_solidangle_le.setText(str(self.detector_solidangle))
        
        
        # check current setup
        topmiddle=QWidget()
        tmbox=QVBoxLayout()
        self.cc_table = QTableWidget()
        self.init_cc_table()
        self.not_draw_lines=[]
        self.line_table = QTableWidget()
        self.init_line_table()

        tmbox.addWidget(QLabel("Plot"))
        tmbox.addWidget(QLabel("Energy range (keV)"))
        tmbox.addLayout(rangebox)
        tmbox.addWidget(plotButton)
        tmbox.addWidget(saveButton)
        self.chkbox_resol = QCheckBox("Detector resolution FWHM (eV)")
        self.chkbox_resol.stateChanged.connect(self.chkbox_resol_action)
        self.chkbox_resol.setChecked(True)
        #tmbox.addWidget(QLabel("Detector resolution FWHM (eV)"))
        tmbox.addWidget(self.chkbox_resol)
        tmbox.addWidget(self.detector_resolution_le)
        tmbox.addWidget(QLabel("Solidangle ratio (0.-1.)"))
        tmbox.addWidget(self.detector_solidangle_le)
        
        #tmbox.addWidget(fluorButton)
        tmbox.addWidget(QLabel("Current setting"))
        tmbox.addWidget(self.cc_table)
        tmbox.addWidget(QLabel("X-ray lines"))
        tmbox.addWidget(self.line_table)
        topmiddle.setLayout(tmbox)
       
        topright=QWidget()
        trbox=QVBoxLayout()
        mini_width=300
        self.fig_tr = Figure(figsize=(8, 6), dpi=80)
        trans_cv = FigureCanvas(self.fig_tr)
        trans_tlbar = NavigationToolbar(trans_cv, self)
        trans_tlbar.setMinimumWidth(mini_width)
        trans_tlbar.setStyleSheet("QToolBar { border: 0px }")
        self.ax = trans_cv.figure.subplots()
        self.fig_fl = Figure(figsize=(8, 6), dpi=80)
        fluor_cv = FigureCanvas(self.fig_fl)
        fluor_tlbar = NavigationToolbar(fluor_cv, self)
        fluor_tlbar.setMinimumWidth(mini_width)
        fluor_tlbar.setStyleSheet("QToolBar { border: 0px }")
        self.ax_fl = fluor_cv.figure.subplots()
        trbox.addWidget(trans_tlbar)
        trbox.addWidget(trans_cv)
        trbox.addWidget(fluor_cv)
        trbox.addWidget(fluor_tlbar)
        topright.setLayout(trbox)
        topright.layout().setSpacing(0)

        ## cosole outputs
        ## used for debug
        #resultTE = QTextEdit()
        #resultTE.setReadOnly( True )
        #resultTE.setUndoRedoEnabled( False )
        #sys.stdout = line_wrap.Logger(resultTE, sys.stdout, QColor(0, 100, 100))
        #sys.stderr = line_wrap.Logger(resultTE, sys.stderr, QColor(200, 0, 0))
        
        splitter1 = QSplitter(Qt.Horizontal)
        splitter1.addWidget(topleft)
        splitter1.addWidget(topmiddle)
        splitter3 = QSplitter(Qt.Horizontal)
        splitter3.addWidget(splitter1)
        splitter3.addWidget(topright)
        #splitter2 = QSplitter(Qt.Vertical)
        #splitter2.addWidget(splitter3)
        #splitter2.addWidget(resultTE)
        #main_layout.addWidget(splitter2)
        main_layout.addWidget(splitter3)
        main_widget.setLayout(main_layout)
        main_widget.setFocus()
        
        self.show()


    def init_cc_table(self):
        self.cc_table.setRowCount(0)
        self.cc_table.setColumnCount(4)
        self.cc_table.setHorizontalHeaderLabels(['','Thickness (cm)', 'Density (g/cm3)', 'Name'])
        cc_header = self.cc_table.horizontalHeader()       
        cc_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cc_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        cc_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        cc_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)


    def init_line_table(self):
        self.line_table.setRowCount(0)
        self.line_table.setColumnCount(7)
        self.line_table.setSortingEnabled(True)
        self.line_table.setHorizontalHeaderLabels(['','El','Line','Energy (keV)','Width (eV)','Intensity','Name'])
        self.line_table.setColumnWidth(0, 40)
        self.line_table.setColumnWidth(1, 30)
        line_header = self.line_table.horizontalHeader()
        line_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        line_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        line_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        line_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        

    def set_table_read_only(self,table):
        for i in range(table.columnCount()+1):
            for j in range(table.rowCount()+1):
                cell_item=table.item(i,j)
                if cell_item: cell_item.setFlags(cell_item.flags() ^ Qt.ItemIsEditable)
                
        
    def _set_from_file(self,fname=None):
        self.dettab.reset_material()
        self.bettab.reset_material()
        self.tgttab.reset_material()
        self.radtab.reset_material()
        self.bemtab.reset_material()
        self.init_cc_table()
        self.init_line_table()
        if fname is None:
            print("no file")
            return
        
        dic=default.read_default_csv(fname)
        self.detector_resolution_le.setText(dic['detector_resolution'][0])
        self.detector_solidangle_le.setText(dic['detector_solidangle'][0])
        
        self.bemtab.bem_beamene_le.setText(dic['beam_energy'][0])
        self.bemtab.bem_beamalpha_le.setText(dic['beam_alpha'][0])
        self.bemtab.bem_beambeta_le.setText(dic['beam_beta'][0])
        self.bemtab.bem_beamflux_le.setText(dic['beam_flux'][0])
        self.bemtab.bem_time_le.setText(dic['beam_time'][0])
        self.bemtab.add_beam()
        print(self.bem['beamene'],self.bem['beamalpha'],self.bem['beambeta'],self.bem['beamflux'],self.beam_duration)

        for i in range(len(dic['target'])):
            self.tgttab.mat_thick_le.setText(dic['target_thickness'][i])
            self.tgttab.cp_le.setText(dic['target'][i])
            if dic['target_density'][i]=='-1':
                self.tgttab.el_cb.setCurrentIndex(xrl.SymbolToAtomicNumber(dic['target'][i]))
            else:
                self.tgttab.mat_dens_le.setText(dic['target_density'][i])
                self.tgttab.apply_mat_cp()
            self.tgttab.add_material()

        for i in range(len(dic['detector'])):
            self.dettab.mat_thick_le.setText(dic['detector_thickness'][i])
            if dic['detector_density'][i]=='-1':
                self.dettab.el_cb.setCurrentIndex(xrl.SymbolToAtomicNumber(dic['detector'][i]))
            else:
                self.dettab.cp_le.setText(dic['detector'][i])
                self.dettab.mat_dens_le.setText(dic['detector_density'][i])
                self.dettab.apply_mat_cp()
            self.dettab.add_material()

        for i in range(len(dic['filter_materials'])):
            self.bettab.mat_thick_le.setText(dic['filter_mat_thickness'][i])
            if dic['filter_mat_density'][i]=='-1':
                self.bettab.el_cb.setCurrentIndex(xrl.SymbolToAtomicNumber(dic['filter_materials'][i]))
            else:
                self.bettab.cp_le.setText(dic['filter_materals'][i])
                self.bettab.mat_dens_le.setText(dic['filter_mat_density'][i])
                self.bettab.apply_mat_cp()
            self.bettab.add_material()

        for i in range(len(dic['NIST_CP_ID'])):
            self.bettab.mat_thick_le.setText(dic['NIST_CP_thickness'][i])
            self.bettab.nist_cb.setCurrentIndex(int(dic['NIST_CP_ID'][i])+1)
            self.bettab.add_material()

        for i in range(len(dic['radionuclide'])):
            self.radtab.rad_act_le.setText(dic['activity_calib'][i])
            self.radtab.rad_date_le.setText(dic['date_calib'][i])
            self.radtab.rad_time_le.setText(dic['radio_time'][i])
            self.radtab.ra_cb.setCurrentIndex(self.RDNLIST.index(dic['radionuclide'][i])+1)
            self.radtab.add_radionuclide()

            
    def btngroup(self,btn):
        if btn.text()==self.default_none:            self._set_from_file(fname=None)
        elif btn.text()==self.default_tes_jparc_mlf: self._set_from_file(fname=self.csvd+"default_TES_Bi_MLF.csv")
        elif btn.text()==self.default_tes_spring8:   self._set_from_file(fname=self.csvd+"default_TES_Bi_Spring8.csv")
        elif btn.text()==self.default_tes_sn:        self._set_from_file(fname=self.csvd+"default_TES_Sn.csv")
        elif btn.text()=="CdTe":      self._set_from_file(fname=self.csvd+"default_CdTe.csv")
        elif btn.text()=="Si":        self._set_from_file(fname=self.csvd+"default_Si.csv")
        elif btn.text()=="Ge":        self._set_from_file(fname=self.csvd+"default_Ge.csv")
        

    def apply_enerangelow(self):
        if self.ene_range_low_le.text()!="":
            erl=float(self.ene_range_low_le.text())
            if erl<0.1:
                self.er_low=0.1
                self.ene_range_low_le.setText("0.1")
            if erl>800.:
                self.er_low=800.
                self.ene_range_low_le.setText("800.")
            else:
                self.er_low=erl
        else:
            self.er_low=0.1
            self.ene_range_low_le.setText("0.1")
            
        
    def apply_enerangehigh(self):
        if self.ene_range_high_le.text()!="":
            erh=float(self.ene_range_high_le.text())
            if erh<0.1:
                self.er_high=0.1
                self.ene_range_high_le.setText("0.1")
            if erh>800.:
                self.er_high=800.
                self.ene_range_high_le.setText("800.")
            else:
                self.er_high=erh
        else:
            self.er_high=20.
            self.ene_range_high_le.setText("20.")


    def apply_enerangestep(self):
        if self.ene_range_step_le.text()!="":
            estep=float(self.ene_range_step_le.text())
            if estep<=0.:
                self.er_step=0.001
                self.ene_range_step_le.setText("0.001")
            else:
                self.er_step=estep
        else:
            self.er_step=0.001# 1 eV
            self.ene_range_step_le.setText("0.001")


    def chkbox_resol_action(self,state):
        if (Qt.Checked == state):
            self.apply_detector_resolution()
        else:
            self.detector_resolution=0.
            self.detector_resolution_le.setText("0.")
            print("Detector resolution is not considered")
            
    def apply_detector_resolution(self):
        s=self.detector_resolution_le.text()
        if s!="":
            self.detector_resolution=float(s)
        else:
            self.detector_resolution=0.
            self.detector_resolution_le.setText("0.")
            print("Detector resolution is not considered")


    def apply_detector_solidangle(self):
        s=self.detector_solidangle_le.text()
        if s!="":
            self.detector_solidangle=float(s)
        else:
            self.detector_solidangle=1.
            self.detector_solidangle_le.setText("1.")


    def _transmission(self):
        trans_all=np.ones_like(self.enes_keV,dtype=np.float64)
        trans_each=[]
        if len(self.bets)==0:
            sys.stderr.write('Warning: no filter materials data\n')
            return trans_all,trans_each
        if "name" not in [*self.bets[0].keys()]:
            sys.stderr.write('Warning: no filter materials data\n')
            return trans_all,trans_each
        for bet in self.bets:
            name=bet['name']
            thickness=bet['thickness']
            density=bet['density']
            if (name=="LUXELHT"):# <- use LUXEL HT window
                each = self._trans_luxel_ht_window()
            else:
                each=np.exp(-np.array([xrl.CS_Total_CP(name,E) for E in self.enes_keV])*density*thickness)
            trans_each.append(each)
            trans_all=trans_all*each
        return trans_all,trans_each


    def _trans_luxel_ht_window(self):
        df = pd.read_csv(self.csvd+"LUXEL_filter_HT_large.csv")
        ene = np.array(df['ev'].values,dtype=float)
        tra = np.array(df['trans'].values,dtype=float)
        f = interp1d(ene, tra)
        each = f(self.enes_keV*1e3)/100.
        return each
    

    def _photoel(self):
        phabs_all=np.ones_like(self.enes_keV,dtype=np.float64)
        phabs_each=[]
        if len(self.dets)==0:
            sys.stderr.write('Warning: _photoel, no detector set\n')
            return phabs_all,phabs_each
        if "name" not in [*self.det.keys()]:
            sys.stderr.write('Warning: _photoel, no detector name\n')
            return phabs_all,phabs_each
        for det in self.dets:
            name=det['name']
            thickness=det['thickness']
            density=det['density']
            each=np.exp(-np.array([xrl.CS_Photo_CP(name,E) for E in self.enes_keV])*density*thickness)
            phabs_each.append(1.-each)
            phabs_all=phabs_all*each
        phabs_all=1.-phabs_all
        return phabs_all,phabs_each


    def _absall(self):
        phabs_all=np.ones_like(self.enes_keV,dtype=np.float64)
        phabs_each=[]
        if len(self.dets)==0:
            sys.stderr.write('Warning: _photoel, no detector set\n')
            return phabs_all,phabs_each
        if "name" not in [*self.det.keys()]:
            sys.stderr.write('Warning: _photoel, no detector name\n')
            return phabs_all,phabs_each
        for det in self.dets:
            name=det['name']
            thickness=det['thickness']
            density=det['density']
            each=np.exp(-np.array([xrl.CS_Total_CP(name,E) for E in self.enes_keV])*density*thickness)
            phabs_each.append(1.-each)
            phabs_all=phabs_all*each
        phabs_all=1.-phabs_all
        return phabs_all,phabs_each
        

    def _selfabs_corr(self,z,line):
        if "name" not in [*self.tgt.keys()]:
            sys.stderr.write('Warning: _selfabs_corr, tgt has no name\n')
            return 0.
        name=self.tgt['name']
        thickness=self.tgt['thickness']
        density=self.tgt['density']
        beamene=self.bem['beamene']
        alpha=self.bem['beamalpha']
        beta=self.bem['beambeta']
        try:
            mu_0=xrl.CS_Total_CP(name, beamene)
        except:
            return 0.
        try:
            mu_1 = xrl.CS_Total_CP(name, line_wrap.get_lineenergy(z,line))
        except:
            return 0.
        chi = mu_0/np.sin(np.pi/180.*alpha) + mu_1/np.sin(np.pi/180.*beta)
        A_corr = (1.0-np.exp(-chi*density*thickness))/(chi*density*thickness)
        return A_corr

    
    def _xrf_intensity(self,z,line):
        if "name" not in [*self.tgt.keys()]:
            sys.stderr.write('Error: _xrf_intensity, tgt has no name\n')
            return 0.
        beamene=self.bem['beamene']
        thickness=self.tgt['thickness']
        density=self.tgt['density']
        nel=self.tgt['nElements']
        els=[*self.tgt['Elements']]# Z
        massfr=[*self.tgt['massFractions']]
        el_ind=np.where(np.array(els)==z)[0][0]
        A_corr = self._selfabs_corr(z,line)
        try:
            Q = xrl.CS_FluorLine_Kissel(z,line,beamene)
        except:
            Q=0.
        return Q * massfr[el_ind] * density * thickness * A_corr


    def _update_line_table_by_radionuclide(self):
        if len(self.rads)==0:
            sys.stderr.write('Warning: update_line_table_by_radionulide, rads has no member\n')
            #self.line_table.setRowCount(0)# reset rows
            return
        for i,rad in enumerate(self.rads):
            name=rad['name']
            Z=rad['Z']
            elSource=xrl.AtomicNumberToSymbol(Z)
            Z_xray=rad['Z_xray']
            elXray=xrl.AtomicNumberToSymbol(Z_xray)
            nXrays=rad['nXrays']
            nGammas=rad['nGammas']
            XrayLines=list(rad['XrayLines'])
            XrayLineTypes=[self.IUPACmac[self.allLINES.index(xl)].split('_')[0] for xl in XrayLines]
            XrayEnergies=np.array([line_wrap.get_lineenergy(Z_xray,line) for line in XrayLines])
            XrayWidths=np.array([line_wrap.get_linewidth(Z_xray,linetype) for linetype in XrayLineTypes])*1e3# eV
            XrayIntensities=np.array(list(rad['XrayIntensities']))
            GammaEnergies=np.array(list(rad['GammaEnergies']))
            GammaIntensities=np.array(list(rad['GammaIntensities']))
            # Xray
            for lt,ene,gamma,norm in zip(XrayLineTypes,XrayEnergies,XrayWidths,XrayIntensities):
                if ene>0. and gamma>0. and norm>0.:
                    row=self.line_table.rowCount()
                    self.line_table.insertRow(row)
                    chk = QCheckBox(parent=self.line_table)
                    chk.setChecked(True)
                    chk.clicked.connect(self._line_table_chkChanged)
                    self.line_table.setCellWidget(row, 0, chk)
                    self.line_table.setItem(row,1, QTableWidgetItem(elXray))
                    self.line_table.setItem(row,2, QTableWidgetItem(lt))
                    self.line_table.setItem(row,3, QTableWidgetItem("%.5f"%(ene)))
                    self.line_table.setItem(row,4, QTableWidgetItem("%.5f"%(gamma)))
                    self.line_table.setItem(row,5, QTableWidgetItem("%.5e"%(norm)))
                    self.line_table.setItem(row,6, QTableWidgetItem("%s %d"%(self.radtab.RADIONUCL_STR,i+1)))
            # Gamma-ray
            for ene,norm in zip(GammaEnergies,GammaIntensities):
                if ene>0. and norm>0.:
                    row=self.line_table.rowCount()
                    self.line_table.insertRow(row)
                    chk = QCheckBox(parent=self.line_table)
                    chk.setChecked(True)
                    chk.clicked.connect(self._line_table_chkChanged)
                    self.line_table.setCellWidget(row, 0, chk)
                    self.line_table.setItem(row,1, QTableWidgetItem(name))
                    self.line_table.setItem(row,2, QTableWidgetItem("Gamma"))
                    self.line_table.setItem(row,3, QTableWidgetItem("%.5f"%(ene)))
                    self.line_table.setItem(row,4, QTableWidgetItem("%.5f"%(0.001)))
                    self.line_table.setItem(row,5, QTableWidgetItem("%.5e"%(norm)))
                    self.line_table.setItem(row,6, QTableWidgetItem("%s %d"%(self.radtab.RADIONUCL_STR,i+1)))

    def update_line_table(self):
        if "name" not in [*self.tgt.keys()]:
            sys.stderr.write('Warning: update_line_table, tgt has no name\n')
            self.line_table.setRowCount(0)# reset rows
            if len(self.rads)!=0: self._update_line_table_by_radionuclide()
            return
        #print("update_line_table")
        name=self.tgt['name']
        zs=[*self.tgt['Elements']]
        lines=[xrl.__getattribute__('%s_LINE'%(x)) for x in self.LINES]
        linetypes=np.array([l for l in self.LINES for z in zs])
        sgblinetypes=np.array([l for l in self.SGBLINES for z in zs])
        els=np.array([xrl.AtomicNumberToSymbol(z) for i in range(len(lines)) for z in zs])
        el_inds=np.array([i for k in range(len(lines)) for i,z in enumerate(zs)])
        enes=np.array([line_wrap.get_lineenergy(z,line) for line in lines for z in zs])
        gammas=np.array([line_wrap.get_linewidth(z,lt) for lt in self.LINES for z in zs])*1e3
        intens=np.array([self._xrf_intensity(z,line) for line in lines for z in zs])
        # remove non-valid lines
        indx=np.where((enes!=0.) & (intens!=0.))[0]
        els=els[indx]
        el_inds=el_inds[indx]
        enes=enes[indx]
        gammas=gammas[indx]
        intens=intens[indx]
        linetypes=linetypes[indx]
        sgblinetypes=sgblinetypes[indx]
        # fill tabel
        self.line_table.setRowCount(0)# reset rows
        self.line_table.setRowCount(len(els))
        for i,(el,lt,sgblt,ene,gamma,norm) in enumerate(zip(els,linetypes,sgblinetypes,enes,gammas,intens)):
            if ene>0. and gamma>0. and norm>0.:
                chk = QCheckBox(parent=self.line_table)
                chk.setChecked(True)
                chk.clicked.connect(self._line_table_chkChanged)
                self.line_table.setCellWidget(i, 0, chk)
                self.line_table.setItem(i,1, QTableWidgetItem(el))
                self.line_table.setItem(i,2, QTableWidgetItem(sgblt))
                self.line_table.setItem(i,3, QTableWidgetItem("%.5f"%(ene)))
                self.line_table.setItem(i,4, QTableWidgetItem("%.5f"%(gamma)))
                self.line_table.setItem(i,5, QTableWidgetItem("%.5e"%(norm)))
                self.line_table.setItem(i,6, QTableWidgetItem(name))
        if len(self.rads)!=0: self._update_line_table_by_radionuclide()

        
    def _line_table_chkChanged(self):
        chk=self.sender()
        self.not_draw_lines=[]
        for i in range(self.line_table.rowCount()):
            ch=self.line_table.cellWidget(i,0)
            if not ch.isChecked():
                el=self.line_table.item(i,1).text()
                lt=self.line_table.item(i,2).text()
                self.not_draw_lines.append(el+lt)
        self._update_fluor_cv()


    def _plot_trans_fluor(self):
        self._update_trans_cv()
        self._update_fluor_cv()


    def _save_trans_fluor(self):
        # save ascii data
        # enes_keV, flout, qeout
        # -- specify folder? or automatic ? --
        savedir='./output'
        os.makedirs(savedir, exist_ok=True)
        # - save -
        default.save_numpy_arrays(self.enes_keV,self.qeout,'%s/qe.txt'%(savedir))
        default.save_numpy_arrays(self.enes_keV,self.flout,'%s/fluor.txt'%(savedir))
        # -- figure save --
        f_tr=default.file_check('%s/qe.pdf'%(savedir))
        self.fig_tr.savefig(f_tr,format='pdf')
        print('%s is created.'%(f_tr))
        f_fl=default.file_check('%s/fluor.pdf'%(savedir))
        self.fig_fl.savefig(f_fl,format='pdf')
        print('%s is created.'%(f_fl))
        try :
            import ROOT
            frname=default.file_check('%s/out.root'%(savedir))
            f_root=ROOT.TFile(frname,"recreate")
            f_root.cd()
            l=self.enes_keV[0]-self.er_step/2.
            h=self.enes_keV[-1]+self.er_step/2.
            nbin=int((h-l)/self.er_step)
            hfluor = ROOT.TH1F("hfluor","hfluor",nbin,l,h)
            for e,f in zip(self.enes_keV,self.flout):
                i = hfluor.FindBin(e)
                hfluor.SetBinContent(i,f)
            gqe=ROOT.TGraph(len(self.enes_keV),self.enes_keV,self.qeout)
            gqe.SetNameTitle("gqe","gqe")
            gfl=ROOT.TGraph(len(self.enes_keV),self.enes_keV,self.flout)
            gfl.SetNameTitle("gfl","gfl")
            hfluor.Write()
            gqe.Write()
            gfl.Write()
            f_root.Close()
            print("%s is created."%(frname))
        except ImportError:
            return

        
    def _update_fluor_cv_by_radionuclide(self):
        if len(self.rads)==0:
            sys.stderr.write('Warning: update_fluor_cv_by_radionulide, rads has no member\n')
            #self.line_table.setRowCount(0)# reset rows
            return
        #self.ax_fl.clear()
        trans_all,trans_each=self._transmission()
        phabs_all,phabs_each=self._photoel()
        radtimesec=self.rad_duration# sec
        solidangle=self.detector_solidangle
        resolution=self.detector_resolution
    
        for i,rad in enumerate(self.rads):
            activitytoday=rad['activitytoday']
            name=rad['name']
            Z_xray=rad['Z_xray']
            elXray=xrl.AtomicNumberToSymbol(Z_xray)
            nXrays=rad['nXrays']
            nGammas=rad['nGammas']
            XrayLines=list(rad['XrayLines'])
            XrayLineTypes=[self.IUPACmac[self.allLINES.index(xl)].split('_')[0] for xl in XrayLines]
            XrayEnergies=np.array([line_wrap.get_lineenergy(Z_xray,line) for line in XrayLines])
            XrayWidths=np.array([line_wrap.get_linewidth(Z_xray,linetype) for linetype in XrayLineTypes])*1e3# eV
            XrayIntensities=np.array(list(rad['XrayIntensities']))
            GammaEnergies=np.array(list(rad['GammaEnergies']))
            GammaIntensities=np.array(list(rad['GammaIntensities']))
            
            # Xray
            specX=np.zeros_like(self.enes_keV,dtype=np.float64)
            for lt,ene,gamma,norm in zip(XrayLineTypes,XrayEnergies,XrayWidths,XrayIntensities):
                if ene>0. and gamma>0. and norm>0.:
                    if elXray+lt in self.not_draw_lines: continue
                    specX += activitytoday * radtimesec * solidangle * norm * trans_all * phabs_all * voigt(self.enes_keV*1e3,ene*1e3,gamma/2.,resolution/sigma_from_fwhm)
                    
            # Gamma-ray
            specG=np.zeros_like(self.enes_keV,dtype=np.float64)
            for ene,norm in zip(GammaEnergies,GammaIntensities):
                if ene>0. and norm>0.:
                    if name+"Gamma" in self.not_draw_lines: continue
                    specG += activitytoday * solidangle * norm * trans_all * phabs_all * voigt(self.enes_keV*1e3,ene*1e3,1.0/2.,resolution/sigma_from_fwhm)

            self.flout+=specX
            self.flout+=specG
            self.ax_fl.plot(self.enes_keV,specX,linestyle='-',marker='',label=elXray)
            self.ax_fl.plot(self.enes_keV,specG,linestyle='-',marker='',label=name)
            self.ax_fl.legend(loc='upper right',fontsize=8)
            self.ax_fl.set_xlabel("Energy (keV)")
            self.ax_fl.set_xlim(self.er_low,self.er_high)
            if self.er_low<=0.1: self.ax_fl.set_xlim(0.,self.er_high)
            self.ax_fl.set_ylabel("Normalized intensity")
            self.ax_fl.figure.canvas.draw()
        
        
    
    def _update_fluor_cv(self):
        #print("update_fluor_cv")
        self.apply_enerangelow()
        if self.er_low<=0.1: self.er_low=0.1
        self.apply_enerangehigh()
        self.apply_enerangestep()
        self.apply_detector_resolution()
        self.apply_detector_solidangle()
        self.enes_keV=np.arange(self.er_low,self.er_high+self.er_low+self.er_step,self.er_step)
        self.flout=np.zeros_like(self.enes_keV)
        self.ax_fl.clear()
        if "name" not in [*self.tgt.keys()]:
            sys.stderr.write('Warning: update_fluor_cv, no target set\n')
            self.ax_fl.plot()
            self.ax_fl.figure.canvas.draw()
            if len(self.rads)!=0:  self._update_fluor_cv_by_radionuclide()
            return
        trans_all,trans_each=self._transmission()
        self.bemtab.add_beam()
        flux=self.bem['beamflux']
        beamtimesec=self.beam_duration# sec
        title=self.tgt['name']
        beamene = self.bem['beamene']
        zs=[*self.tgt['Elements']]
        phabs_all,phabs_each=self._photoel()
        solidangle=self.detector_solidangle
        resolution=self.detector_resolution
        lines=np.array([xrl.__getattribute__('%s_LINE'%(x)) for x in self.LINES])
        linetypes=np.array([l for l in self.LINES for z in zs])
        sgblinetypes=np.array([l for l in self.SGBLINES for z in zs])
        elms=[xrl.AtomicNumberToSymbol(z) for i in range(len(lines)) for z in zs]
        els=np.array([xrl.AtomicNumberToSymbol(z) for i in range(len(lines)) for z in zs])
        el_inds=np.array([i for k in range(len(lines)) for i,z in enumerate(zs)])
        enes=np.array([line_wrap.get_lineenergy(z,line) for line in lines for z in zs])
        gammas=np.array([line_wrap.get_linewidth(z,lt) for lt in self.LINES for z in zs])*1e3# eV
        intens=np.array([self._xrf_intensity(z,line) for line in lines for z in zs])
        # remove non-valid lines
        indx=np.where((enes!=0.) & (intens!=0.))[0]
        els=els[indx]
        el_inds=el_inds[indx]
        enes=enes[indx]
        gammas=gammas[indx]
        intens=intens[indx]
        linetypes=linetypes[indx]
        sgblinetypes=sgblinetypes[indx]
        specs=[np.zeros_like(self.enes_keV,dtype=np.float64) for i in range(len(zs))]
        for i,(el,elind,lt,sgblt,ene,gamma,norm) in enumerate(zip(els,el_inds,linetypes,sgblinetypes,enes,gammas,intens)):
            if ene>0. and gamma>0.:
                if el+sgblt in self.not_draw_lines: continue
                specs[elind] += flux * beamtimesec * solidangle * norm * trans_all * phabs_all * voigt(self.enes_keV*1e3,ene*1e3,gamma/2.,resolution/sigma_from_fwhm)
        cindex={x:i for i,x in enumerate([xrl.AtomicNumberToSymbol(z) for z in zs])}
        for el,spec in zip(elms,specs):
            self.flout+=spec
            self.ax_fl.plot(self.enes_keV,spec,linestyle='-',marker='',color=cm.jet(cindex[el]/len(cindex)),label=el)

        if len(self.rads)!=0:  self._update_fluor_cv_by_radionuclide()
            
        self.ax_fl.legend(loc='upper right',fontsize=8)
        self.ax_fl.set_xlabel("Energy (keV)")
        self.ax_fl.set_xlim(self.er_low,self.er_high)
        if self.er_low<=0.1: self.ax_fl.set_xlim(0.,self.er_high)
        self.ax_fl.set_ylabel("Normalized intensity")
        self.ax_fl.set_title("%s, beam %.3f keV, resol %.1f eV"%(title,beamene,resolution))
        self.ax_fl.figure.canvas.draw()

        
    def _update_trans_cv(self):
        self.apply_enerangelow()
        if self.er_low<=0.1: self.er_low=0.1
        self.apply_enerangehigh()
        self.apply_enerangestep()
        self.apply_detector_resolution()
        self.apply_detector_solidangle()
        self.enes_keV=np.arange(self.er_low,self.er_high+self.er_low+self.er_step,self.er_step)
        self.qeout=np.zeros_like(self.enes_keV)
        self.ax.clear()
        trans_all,trans_each=self._transmission()
        phabs_all,phabs_each=self._photoel()
        abs_all,abs_each=self._absall()
        if len(trans_each)!=0:
            for tr,bet in zip(trans_each,self.bets):
                self.ax.plot(self.enes_keV,tr,'--',label="trns %s %.2e"%(bet['name'],bet['thickness']))
            self.ax.plot(self.enes_keV,trans_all,'-',label="trns all")
        if len(phabs_each)!=0:
            for ph,det in zip(phabs_each,self.dets):
                self.ax.plot(self.enes_keV,ph,'--',label="phabs %s %.2e"%(det['name'],det['thickness']))
            self.ax.plot(self.enes_keV,phabs_all,'-',label="phabs all")
        #if len(abs_each)!=0:
        #    for ph,det in zip(abs_each,self.dets):
        #        self.ax.plot(self.enes_keV,ph,'--',label="totalabs %s %.2e"%(det['name'],det['thickness']))
        #    self.ax.plot(self.enes_keV,abs_all,'-',label="totalabs all")
        self.qeout=trans_all*phabs_all
        self.ax.plot(self.enes_keV, self.qeout,'-',color='black',label="trans x phabs")
        self.ax.legend(loc='upper right',fontsize=8)
        self.ax.set_xlabel("Energy (keV)")
        self.ax.set_xlim(self.er_low,self.er_high)
        if self.er_low<=0.1: self.ax.set_xlim(0.,self.er_high)
        self.ax.set_ylim(0,1.)
        self.ax.set_ylabel("Transmission and absorption")
        self.ax.figure.canvas.draw()
        

    # https://pythonspot.com/pyqt5-file-dialog/
    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;csv Files (*.csv)", options=options)
        if fileName:
            self.chkbox0.setChecked(True)
            self._set_from_file(fname=fileName)
        else:
            print("no file")
        

    def exit_handler(self, signal, frame):
        #sys.stderr.write('\n')
        #if QMessageBox.question(None, '', "Are you sure you want to quit?",
        #                        QMessageBox.Yes | QMessageBox.No,
        #                        QMessageBox.No) == QMessageBox.Yes:
        QApplication.quit()
        sys.exit(0)
        

if __name__ == "__main__":
    # GUI
    app = QApplication(sys.argv)
    aw = ApplicationWindow()
    aw.show()
    signal.signal(signal.SIGINT, aw.exit_handler)
    sys.exit(app.exec_())



    
