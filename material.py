from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import sys
import copy
import numpy as np
from datetime import datetime

import xraylib as xrl


class MaterialTabWidget(QWidget):
    def __init__(self, parent=None, name=""):
        super(MaterialTabWidget, self).__init__()

        self.parent=parent
        self.name=name# tag
        self.mat={}# materials for target, detector, etc
        self.rad={}# radionuclide sources
        self.bem={}# beam
        # the following table was used for debug...
        self.mat_table = QTableWidget()
        self.mat_table.setRowCount(2)
        self.mat_table.setColumnCount(2)
        mat_header = self.mat_table.horizontalHeader()       
        mat_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        mat_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        # default values
        saddbutton=""
        sremovebutton="Remove"
        sresetbutton="Reset"
        if self.name=='det' or self.name=='rad' or self.name=='bet':
            saddbutton="Add"
        elif self.name=='tgt' or self.name=="bem":
            saddbutton="Set"

        self.TARGET_STR="Target"
        self.DETECTOR_STR="Detector"
        self.FILTER_STR="Filter"
        self.RADIONUCL_STR="RadioNucl"

        # main layout
        main_layout = QVBoxLayout()
        
        # add (set), remove, reset
        self.addButton = QPushButton(saddbutton)
        if self.name=='rad':
            self.addButton.clicked.connect(self.add_radionuclide)
        elif self.name=='bem':
            self.addButton.clicked.connect(self.add_beam)
        else:
            self.addButton.clicked.connect(self.add_material)
        self.resetButton = QPushButton(sresetbutton)
        self.resetButton.clicked.connect(self.reset_material)
        self.removeButton = QPushButton(sremovebutton)
        self.removeButton.clicked.connect(self.remove_material)
        ly1=QHBoxLayout()
        ly1.addWidget(self.addButton)
        if self.name=='bet' or self.name=='det' or self.name=='rad':
            ly1.addWidget(self.removeButton)
        ly1.addWidget(self.resetButton)

        # thickness & density
        self.mat_thick_le = QLineEdit()
        self.mat_thick_le.setValidator(QDoubleValidator(0,1e11,999))
        self.mat_thick_le.returnPressed.connect(self.apply_mat_thickness)
        self.mat_dens_le = QLineEdit()
        self.mat_dens_le.setValidator(QDoubleValidator(0,1e11,999))
        self.mat_dens_le.returnPressed.connect(self.apply_mat_density)
        ly2=QHBoxLayout()
        ly2.addWidget(QLabel("Thickness (cm)"))
        ly2.addWidget(QLabel("Density (g/cm3)"))
        ly3=QHBoxLayout()
        ly3.addWidget(self.mat_thick_le)
        ly3.addWidget(self.mat_dens_le)
        # Element
        el_list=["%d: %s"%(i,xrl.AtomicNumberToSymbol(z)) for i,z in enumerate(np.arange(1,108,1))]
        self.el_cb = QComboBox()
        self.el_cb.addItem("None")
        self.el_cb.addItems(el_list)
        self.el_cb.currentIndexChanged.connect(self.el_select)
        # CP
        self.cp_le = QLineEdit()
        self.cp_le.returnPressed.connect(self.apply_mat_cp)
        # NIST CP
        nistcp_list = ["%d: %s"%(i,cp) for i,cp in enumerate(xrl.GetCompoundDataNISTList())]
        self.nist_cb = QComboBox()
        self.nist_cb.addItem("None")
        self.nist_cb.addItems(nistcp_list)
        self.nist_cb.currentIndexChanged.connect(self.nistcp_select)

        self.bem_beamene_le = QLineEdit()
        self.bem_beamene_le.setValidator(QDoubleValidator(0,1e11,999))
        self.bem_beamene_le.returnPressed.connect(self.apply_beamene)
        self.bem_beamene_le.setText("15.")
        self.bem_beamalpha_le = QLineEdit()
        self.bem_beamalpha_le.setValidator(QDoubleValidator(0,90.,999))
        self.bem_beamalpha_le.returnPressed.connect(self.apply_beamalpha)
        self.bem_beamalpha_le.setText("45.")
        self.bem_beambeta_le = QLineEdit()
        self.bem_beambeta_le.setValidator(QDoubleValidator(0,90.,999))
        self.bem_beambeta_le.returnPressed.connect(self.apply_beambeta)
        self.bem_beambeta_le.setText("45.")
        self.bem_beamflux_le = QLineEdit()
        self.bem_beamflux_le.setValidator(QDoubleValidator(0,1e20,999))
        self.bem_beamflux_le.returnPressed.connect(self.apply_beamflux)
        self.bem_beamflux_le.setText("1e6")# 1 M/sec
        self.bem_time_le = QLineEdit()# duration
        self.bem_time_le.setValidator(QDoubleValidator(0,1e30,999))
        self.bem_time_le.setText("7200.")# 2 hours
        self.bem_time_le.returnPressed.connect(self.apply_beam_time)

        self.ra_cb = QComboBox()
        self.ra_cb.addItem("None")
        self.ra_cb.addItems(self.parent.RDNLIST)
        self.ra_cb.currentIndexChanged.connect(self.ra_select)      
        self.rad_act_le = QLineEdit()
        self.rad_date_le = QLineEdit()
        self.rad_date_m_le = QLineEdit()
        self.rad_act_m_le = QLineEdit()
        self.rad_act_m_le.setReadOnly(True)
        self.rad_today_le = QLineEdit()
        self.rad_today_le.setReadOnly(True)
        self.rad_hl_le = QLineEdit()
        self.rad_hl_le.setReadOnly(True)
        self.rad_time_le = QLineEdit()# duration
        self.rad_act_le.setValidator(QDoubleValidator(0,1e30,999))
        self.rad_date_le.setValidator(QIntValidator(19000101,99991231))
        self.rad_date_m_le.setValidator(QIntValidator(19000101,99991231))
        self.rad_time_le.setValidator(QDoubleValidator(0,1e30,999))
        self.rad_act_le.setText("1e6")
        self.rad_date_le.setText("20110311")
        self.rad_date_m_le.setText("20200311")
        self.rad_time_le.setText("3600.")
        self.rad_act_le.returnPressed.connect(self.apply_rad_act)
        self.rad_date_le.returnPressed.connect(self.apply_rad_date)
        self.rad_date_m_le.returnPressed.connect(self.apply_rad_date_measure)
        self.rad_time_le.returnPressed.connect(self.apply_rad_time)
        
        if self.name=="bem":
            beamw=QWidget()
            #beamw.setObjectName('beamw')
            #beamw_style='QWidget#beamw{border: 1px solid lightgray; border-radius: 2px;}'
            #beamw.setStyleSheet(beamw_style)
            beambox=QVBoxLayout(beamw)
            beambox.setSpacing(0)
            beamew=QWidget()
            ly4=QHBoxLayout(beamew)
            ly4.addWidget(QLabel("Incident energy (keV):   "))
            ly4.addWidget(self.bem_beamene_le)
            beamfw=QWidget()
            ly7=QHBoxLayout(beamfw)
            ly7.addWidget(QLabel("Beam flux (photons): "))
            ly7.addWidget(self.bem_beamflux_le)
            beamaw=QWidget()
            ly5=QHBoxLayout(beamaw)
            ly5.addWidget(QLabel("Incident angle (degree):"))
            ly5.addWidget(self.bem_beamalpha_le)
            beambw=QWidget()
            ly6=QHBoxLayout(beambw)
            ly6.addWidget(QLabel("Outgoing angle (degree):"))
            ly6.addWidget(self.bem_beambeta_le)
            beambox.addWidget(beamew)
            beambox.addWidget(beamfw)
            beambox.addWidget(beamaw)
            beambox.addWidget(beambw)
            #detiw=QWidget()
            #detiw.setObjectName('detiw')
            #detiw_style='QWidget#detiw{border: 1px solid lightgray; border-radius: 2px;}'
            #detiw.setStyleSheet(detiw_style)
            #detil=QVBoxLayout(detiw)
            btimew=QWidget()
            btimel=QHBoxLayout(btimew)
            btimel.addWidget(QLabel("Beam time (sec):"))
            btimel.addWidget(self.bem_time_le)
            #detil.addWidget(btimew)
            beambox.addWidget(btimew)
            main_layout.addLayout(ly1)
            main_layout.addWidget(beamw)
            #main_layout.addWidget(detiw)
                 
        # RadioNuclide
        elif self.name=="rad":
            # calibrated radioactivity
            radactw=QWidget()
            radactl=QHBoxLayout(radactw)
            radactl.addWidget(QLabel("Activity calib (Bq):"))
            radactl.addWidget(self.rad_act_le)
            # date of calibration
            raddatew=QWidget()
            raddatel=QHBoxLayout(raddatew)
            raddatel.addWidget(QLabel("Date calib (e.g., 20110311): "))
            raddatel.addWidget(self.rad_date_le)
            # half life
            radhlw=QWidget()
            radhll=QHBoxLayout(radhlw)
            radhll.addWidget(QLabel("Half life (days): "))
            radhll.addWidget(self.rad_hl_le)
            # date of measurement
            raddatemw=QWidget()
            raddateml=QHBoxLayout(raddatemw)
            raddateml.addWidget(QLabel("Date measure (e.g., 20200311): "))
            raddateml.addWidget(self.rad_date_m_le)
            #
            radtodayw=QWidget()
            radtodayl=QHBoxLayout(radtodayw)
            radtodayl.addWidget(QLabel("Activity today (Bq): "))
            radtodayl.addWidget(self.rad_today_le)
            # duration time
            radtimew=QWidget()
            radtimel=QHBoxLayout(radtimew)
            radtimel.addWidget(QLabel("Duration time (sec): "))
            radtimel.addWidget(self.rad_time_le)
            main_layout.addLayout(ly1)
            main_layout.addWidget(QLabel("Radionuclide source"))
            main_layout.addWidget(self.ra_cb)
            main_layout.addWidget(radactw)
            main_layout.addWidget(raddatew)
            main_layout.addWidget(radhlw)
            main_layout.addWidget(radtodayw)
            #radiw=QWidget()
            #radiw.setObjectName('radiw')
            #radiw_style='QWidget#radiw{border: 1px solid lightgray; border-radius: 2px;}'
            #radiw.setStyleSheet(radiw_style)
            #radil=QVBoxLayout(radiw)
            #radil.addWidget(radtimew)
            main_layout.addWidget(radtimew)
            #main_layout.addWidget(radiw)

        elif self.name=="bet":# between materials = filter
            main_layout.addLayout(ly1)
            main_layout.addLayout(ly2)
            main_layout.addLayout(ly3)
            main_layout.addWidget(QLabel("Element"))
            main_layout.addWidget(self.el_cb)
            main_layout.addWidget(QLabel("NIST compound"))
            main_layout.addWidget(self.nist_cb)
            main_layout.addWidget(QLabel("Compound parser (e.g., CdTe) press return"))
            main_layout.addWidget(self.cp_le)
            self.chkbox_luxelht = QCheckBox("add LUXEL HT window")
            self.chkbox_luxelht.stateChanged.connect(self.chkbox_luxelht_action)
            self.chkbox_luxelht.setChecked(False)
            main_layout.addWidget(self.chkbox_luxelht)
            
            
        else:
            main_layout.addLayout(ly1)
            main_layout.addLayout(ly2)
            main_layout.addLayout(ly3)
            main_layout.addWidget(QLabel("Element"))
            main_layout.addWidget(self.el_cb)
            main_layout.addWidget(QLabel("NIST compound"))
            main_layout.addWidget(self.nist_cb)
            main_layout.addWidget(QLabel("Compound parser (e.g., CdTe) press return"))
            main_layout.addWidget(self.cp_le)
            #main_layout.addWidget(self.mat_table) 
            
        self.setLayout(main_layout)


    def add_beam(self):
        self.apply_beamene()
        self.apply_beamalpha()
        self.apply_beambeta()
        self.apply_beamflux()
        self.apply_beam_time()
        self.parent.bem={}
        self.parent.bem=copy.deepcopy(self.bem)
        self.parent.update_line_table()
                                        

    def add_radionuclide(self):
        if "name" not in [*self.rad.keys()]:
            sys.stderr.write('Error: add_radionuclide, no radionuclide selected\n')
            return
        self.apply_rad_act()
        self.apply_rad_time()
        self.parent.rad=copy.deepcopy(self.rad)
        self.parent.rads.append(copy.deepcopy(self.rad))
        self.parent.update_line_table()

    def _add_target(self):
        self.parent.tgt=copy.deepcopy(self.mat)            
        self.parent.update_line_table()
        row=self.parent.cc_table.rowCount()
        items = self.parent.cc_table.findItems("%s 1"%(self.TARGET_STR), Qt.MatchExactly)
        if items:
            row=items[0].row()
        else:
            self.parent.cc_table.insertRow(row)
        self.parent.cc_table.setItem(row,0, QTableWidgetItem("%s 1"%(self.TARGET_STR)))
        self.parent.cc_table.setItem(row,1, QTableWidgetItem(str(self.mat['thickness'])))
        self.parent.cc_table.setItem(row,2, QTableWidgetItem(str(self.mat['density'])))
        self.parent.cc_table.setItem(row,3, QTableWidgetItem(self.mat['name']))        
    
    def _add_detector(self):
        self.parent.det=copy.deepcopy(self.mat)
        self.parent.dets.append(copy.deepcopy(self.mat))
        row=self.parent.cc_table.rowCount()
        self.parent.cc_table.insertRow(row)
        self.parent.cc_table.setItem(row,0, QTableWidgetItem("%s %d"%(self.DETECTOR_STR,len(self.parent.dets))))
        self.parent.cc_table.setItem(row,1, QTableWidgetItem(str(self.mat['thickness'])))
        self.parent.cc_table.setItem(row,2, QTableWidgetItem(str(self.mat['density'])))
        self.parent.cc_table.setItem(row,3, QTableWidgetItem(self.mat['name']))

    def _add_filter_materials(self):
        self.parent.bet=copy.deepcopy(self.mat)
        self.parent.bets.append(copy.deepcopy(self.mat))
        row=self.parent.cc_table.rowCount()
        self.parent.cc_table.insertRow(row)
        self.parent.cc_table.setItem(row,0, QTableWidgetItem("%s %d"%(self.FILTER_STR,len(self.parent.bets))))
        self.parent.cc_table.setItem(row,1, QTableWidgetItem(str(self.mat['thickness'])))
        self.parent.cc_table.setItem(row,2, QTableWidgetItem(str(self.mat['density'])))
        self.parent.cc_table.setItem(row,3, QTableWidgetItem(self.mat['name']))

        
    def add_material(self):
        if "name" not in [*self.mat.keys()]:
            sys.stderr.write('Error: add_material, no material selected\n')
            return
        self.apply_mat_thickness()
        if self.mat['thickness']<=0:
            sys.stderr.write('Error: add_material, thickness should be a positive value\n')
            return
        self.apply_mat_density()
        if self.mat['density']<=0:
            sys.stderr.write('Error: add_material, density should be a positive value\n')
            return
        if self.name=='tgt':   self._add_target()
        elif self.name=='det': self._add_detector()
        elif self.name=='bet': self._add_filter_materials()
                    

    def remove_material(self):
        items=None
        if self.name=='bet':
            r=len(self.parent.bets)
            items = self.parent.cc_table.findItems("%s %d"%(self.FILTER_STR,r), Qt.MatchExactly)
            if items:
                for item in items: self.parent.cc_table.removeRow(item.row())
            if r==1:
                self.parent.bet={}
            elif r>1:
                self.parent.bet=copy.deepcopy(self.parent.bets[-2])
            else:
                sys.stderr.write('Warning: no filter material\n')
                return
            #print("removed parent.bet=",self.parent.bets[-1])
            del self.parent.bets[-1]
        elif self.name=='det':
            r=len(self.parent.dets)
            items = self.parent.cc_table.findItems("%s %d"%(self.DETECTOR_STR,r), Qt.MatchExactly)
            if items:
                for item in items: self.parent.cc_table.removeRow(item.row())
            if r==1:
                self.parent.det={}
            elif r>1:
                self.parent.det=copy.deepcopy(self.parent.dets[-2])
            else:
                sys.stderr.write('Warning: no detector\n')
                return
            #print("removed parent.det=",self.parent.dets[-1])
            del self.parent.dets[-1]
        elif self.name=='rad':
            r=len(self.parent.rads)
            items = self.parent.line_table.findItems("%s %d"%(self.RADIONUCL_STR,r), Qt.MatchExactly)
            if items:
                for item in items: self.parent.line_table.removeRow(item.row())
            if r==1:
                self.parent.rad={}
            elif r>1:
                self.parent.rad=copy.deepcopy(self.parent.rads[-2])
            else:
                sys.stderr.write('Warning: no radionuclide\n')
                return
            del self.parent.rads[-1]
            


    def reset_material(self):
        items=None
        if self.name=='rad':
            self.parent.rad={}
            self.parent.rads=[]
            items = self.parent.line_table.findItems("%s"%(self.RADIONUCL_STR), Qt.MatchStartsWith)
            if items:
                for item in items: self.parent.line_table.removeRow(item.row())
            return
        if self.name=='tgt':
            self.parent.tgt={}
            items = self.parent.cc_table.findItems("%s"%(self.TARGET_STR), Qt.MatchStartsWith)
        elif self.name=='det':
            self.parent.det={}
            self.parent.dets=[]
            items = self.parent.cc_table.findItems("%s"%(self.DETECTOR_STR), Qt.MatchStartsWith)
        elif self.name=='bet':
            self.parent.bet={}
            self.parent.bets=[]
            items = self.parent.cc_table.findItems("%s"%(self.FILTER_STR), Qt.MatchStartsWith)
        elif self.name=='bem':
            self.parent.bem={}
        if items:
            for item in items: self.parent.cc_table.removeRow(item.row())
        

                 
    def apply_mat_thickness(self):
        s=self.mat_thick_le.text()
        if s!="":
            try:
                self.mat['thickness']=float(s)
            except:
                sys.stderr.write('Error: input is not valid\n')
                self.mat['thickness']=0.
        else:
            sys.stderr.write('Warning: please set a positive thickness\n')
            self.mat['thickness']=0.
            
    def apply_mat_density(self):
        s=self.mat_dens_le.text()
        if s!="":
            try:
                self.mat['density']=float(s)
            except:
                sys.stderr.write('Error: input is not valid\n')
                self.mat['density']=0.
        else:
            sys.stderr.write('Warning: please set a positive density\n')
            self.mat['density']=0.

                        
    def apply_beamene(self):
        s=self.bem_beamene_le.text()
        if s!="":
            try:
                self.bem['beamene']=float(s)
            except:
                sys.stderr.write('Error: input is not valid\n')
                self.bem_beamene_le.setText("20.")
                self.bem['beamene']=20.
        else:
            self.bem_beamene_le.setText("20.")
            self.bem['beamene']=20.
        

    def apply_beamalpha(self):
        s=self.bem_beamalpha_le.text()
        if s!="":
            try:
                self.bem['beamalpha']=float(s)
            except:
                sys.stderr.write('Error: input is not valid\n')
                self.bem_beamalpha_le.setText("45.")
                self.bem['beamalpha']=45.
        else:
            self.bem_beamalpha_le.setText("45.")
            self.bem['beamalpha']=45.

    def apply_beambeta(self):
        s=self.bem_beambeta_le.text()
        if s!="":
            try:
                self.bem['beambeta']=float(s)
            except:
                sys.stderr.write('Error: input is not valid\n')
                self.bem_beambeta_le.setText("45.")
                self.bem['beambeta']=45.
        else:
            self.bem_beambeta_le.setText("45.")
            self.bem['beambeta']=45.

    def apply_beamflux(self):
        s=self.bem_beamflux_le.text()
        if s!="":
            try:
                self.bem['beamflux']=float(s)
            except:
                sys.stderr.write('Error: input is not valid\n')
                self.bem_beamflux_le.setText("1e6")
                self.bem['beamflux']=0.
        else:
            self.bem_beamflux_le.setText("1e6")
            self.bem['beamflux']=1e6

    def apply_beam_time(self):
        if self.bem_time_le.text()!="":
            try:
                self.parent.beam_duration=float(self.bem_time_le.text())
            except:
                sys.stderr.write('Error: input is not valid\n')
                self.bem_time_le.setText("7200.")
                self.parent.beam_duration=7200.
        else:
            self.bem_time_le.setText("7200.")
            self.parent.beam_duration=7200.

    def apply_rad_time(self):
        if self.rad_time_le.text()!="":
            try:
                self.parent.rad_duration=float(self.rad_time_le.text())
            except:
                sys.stderr.write('Error: input is not valid\n')
                self.rad_time_le.setText("3600.")
                self.parent.rad_duration=3600.
        else:
            self.rad_time_le.setText("3600.")
            self.parent.rad_duration=3600.

            
    def apply_rad_act(self):
        if self.rad_act_le.text()!="":
            try:
                self.rad['activity']=float(self.rad_act_le.text())
            except:
                sys.stderr.write('Error: input is not valid\n')
                self.rad_act_le.setText("0.0")
                self.rad['activity']=0.
        else:
            self.rad_act_le.setText("0.0")
            self.rad['activity']=0.
        self.apply_rad_date()


    def apply_rad_date(self):
        dt=self._get_dt_days()
        A=0.
        A0=0.
        hl=0.
        if "activity" in [*self.rad.keys()]: A0=self.rad['activity']
        if "name" in [*self.rad.keys()]:
            try:
                hl=self.parent.RDNHL[self.parent.RDNLIST.index(self.rad['name'])]
                A=A0 * np.exp(-np.log(2)/hl * dt)
            except:
                A=0.
        self.rad_today_le.setText("%.3e"%A)
        self.rad_hl_le.setText("%.3f"%hl)
        self.rad['activitytoday']=A
        self.rad['halflife']=hl

        
    def apply_rad_date_measure(self):
        dt=self._get_measure_dt_days()
        A=0.
        A0=0.
        hl=0.
        if "activity" in [*self.rad.keys()]: A0=self.rad['activity']
        if "name" in [*self.rad.keys()]:
            try:
                hl=self.parent.RDNHL[self.parent.RDNLIST.index(self.rad['name'])]
                A=A0 * np.exp(-np.log(2)/hl * dt)
            except:
                A=0.
        self.rad_act_m_le.setText("%.3e"%A)
        self.rad_hl_le.setText("%.3f"%hl)
        self.rad['activitymeasure']=A
        self.rad['halflife']=hl
        

        
    def _get_dt_days(self):
        now = datetime.now()
        today = now.strftime("%Y%m%d")
        st=self.rad_date_le.text()
        if len(st)!=8:# 20110311
            sys.stderr.write('Error: input is not valid\n')
            self.rad['date']=today
            self.rad_date_le.setText(today)
            return
        year=int(st[0:4])
        month=int(st[4:6])
        day=int(st[6:8])
        flag=False
        td=None
        dt=0.
        if month>=1 and month<=12:
            if month in [1,3,5,7,8,10,12]:
                if day>=1 and day<=31: flag=True
            elif month in [4,6,9,11]:
                if day>=1 and day<=30: flag=True
            elif month==2:
                if day>=1 and day<=29: flag=True# leap day?
        if flag==False:
            self.rad['date']=today
            self.rad_date_le.setText(today)
            td = now - now
        else:
            self.rad['date']=st
            td = now - datetime(year,month,day)
        if td:
            dt = td.total_seconds()/86400.# days
            self.rad['deltadays']=dt
        return dt


    def _get_measure_dt_days(self):
        now = datetime.now()
        today = now.strftime("%Y%m%d")
        mt=st=self.rad_date_m_le.text()
        if len(mt)!=8:# 20110311
            sys.stderr.write('Error: input is not valid\n')
            self.rad['mdate']=today
            self.rad_date_m_le.setText(today)
            return
        st=self.rad_date_le.text()
        if len(st)!=8:# 20110311
            sys.stderr.write('Error: input is not valid\n')
            self.rad['date']=today
            self.rad_date_le.setText(today)
            return
        year=int(st[0:4])
        month=int(st[4:6])
        day=int(st[6:8])
        flag=False
        td=None
        dt=0.
        if month>=1 and month<=12:
            if month in [1,3,5,7,8,10,12]:
                if day>=1 and day<=31: flag=True
            elif month in [4,6,9,11]:
                if day>=1 and day<=30: flag=True
            elif month==2:
                if day>=1 and day<=29: flag=True# leap day?
        if flag==False:
            self.rad['date']=today
            self.rad_date_le.setText(today)
            td = now - now
        else:
            self.rad['date']=st
            td = now - datetime(year,month,day)
        if td:
            dt = td.total_seconds()/86400.# days
            self.rad['deltadays']=dt
        return dt
    
    
    def ra_select(self):
        r=self.ra_cb.currentIndex()
        if r>0:
            self.rad=xrl.GetRadioNuclideDataByIndex(r-1)
        else:
            self.rad={}
        self.apply_rad_act()

            
    def apply_mat_cp(self):
        if self.cp_le.text()=="":
            self.mat={}
            return
        try:
            self.nist_cb.setCurrentIndex(0)
            self.el_cb.setCurrentIndex(0)
            if self.name=="bet": self.chkbox_luxelht.setChecked(False)
            self.mat=xrl.CompoundParser(self.cp_le.text())
            self.mat['name']=self.cp_le.text()
            self.apply_mat_thickness()
            self.apply_mat_density()
        except:
            self.mat={}

    def el_select(self):
        Z=self.el_cb.currentIndex()
        if Z>0:
            self.nist_cb.setCurrentIndex(0)
            self.cp_le.setText("")
            if self.name=="bet": self.chkbox_luxelht.setChecked(False)
            self.mat=xrl.CompoundParser(xrl.AtomicNumberToSymbol(Z))
            self.mat['name']=xrl.AtomicNumberToSymbol(Z) 
            self.apply_mat_thickness()
            self.mat['density']=xrl.ElementDensity(Z)
            self.mat_dens_le.setText(str(self.mat['density']))
            self.apply_mat_density()
        else:
            self.mat={}
        
    def nistcp_select(self):
        if self.nist_cb.currentIndex()>0:
            self.el_cb.setCurrentIndex(0)
            self.cp_le.setText("")
            if self.name=="bet": self.chkbox_luxelht.setChecked(False)
            self.mat=xrl.GetCompoundDataNISTByIndex(self.nist_cb.currentIndex()-1)
            self.apply_mat_thickness()
            self.mat_dens_le.setText(str(self.mat['density']))
            self.apply_mat_density()
        else:
            self.mat={}

    def chkbox_luxelht_action(self):
        if self.chkbox_luxelht.isChecked():
            self.nist_cb.setCurrentIndex(0)
            self.el_cb.setCurrentIndex(0)
            self.cp_le.setText("")
            self.mat['name']="LUXELHT"# <- use this name as a flag
            # dummy info
            self.mat['nElements']=1
            self.mat['Elements']=(1)
            self.mat['massFractions']=(1.)
            self.mat['density']=1.
            self.mat['thickness']=0.01
            self.mat_dens_le.setText(str(self.mat['density']))
            self.mat_thick_le.setText(str(self.mat['thickness']))
            self.add_material()
            self.mat_dens_le.setText("")
            self.mat_thick_le.setText("")
        else:
            self.mat={}
        
            
    # this was used for debug
    def update_mat_table(self):
        self.apply_mat_thickness()
        self.apply_mat_density()
        if "name" not in [*self.mat.keys()]:
            self.mat_table.setRowCount(2)
            self.mat_table.setItem(0,0, QTableWidgetItem("thickness (cm)"))
            self.mat_table.setItem(0,1, QTableWidgetItem(str(self.mat['thickness'])))
            self.mat_table.setItem(1,0, QTableWidgetItem("density (g/cm3)"))
            self.mat_table.setItem(1,1, QTableWidgetItem(str(self.mat['density'])))
            return
        rows=[*self.mat.keys()]
        vals=[*self.mat.values()]
        self.mat_table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            self.mat_table.setItem(i,0, QTableWidgetItem(row))
            if row=='Elements':
                zl=[xrl.AtomicNumberToSymbol(z) for z in self.mat[row]]
                zl=','.join(zl)
                self.mat_table.setItem(i,1, QTableWidgetItem(str(self.mat[row])+"=("+zl+")"))
            elif row=='massFractions':
                frs=["%.3e"%fr for fr in self.mat[row]]
                frs=','.join(frs)
                self.mat_table.setItem(i,1, QTableWidgetItem("("+frs+")"))
            else:
                self.mat_table.setItem(i,1, QTableWidgetItem(str(self.mat[row])))
