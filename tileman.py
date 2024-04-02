from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import QColor
from threading import Thread
import socket
import threading
import subprocess
import time
import sched
from ftplib import *
import re
import traceback
import os

from convert import Converter

DELAY = 1

app = QApplication([])
main = QWidget(windowTitle="Tileman")
main.show()
layout = QVBoxLayout()
main.setLayout(layout)
threadpool = QThreadPool()
threadpool.setMaxThreadCount(270)


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class Upload_worker(QRunnable):
		
	def __init__(self,connect_to_tile,gif_urls):
		super().__init__()
		self.setAutoDelete(True)
		self.tile = connect_to_tile
		self.urls = gif_urls
		self.signals = WorkerSignals()
		self.bytes_sent = 0
		self.file_size = 0
		for url in self.urls:
			self.file_size += os.path.getsize(url.toLocalFile())
		
	def run(self):
		self.tile[3].acquire()
		print('uploading to '+self.tile[2])
		for url in self.urls:
			print('starting upload: '+url.fileName())
			try:
				self.tile[4].storbinary('STOR '+url.fileName(),open(url.toLocalFile(), 'rb') , callback=self.upload_status )
			except Exception as e:
				print('upload of'+url.fileName()+'to '+self.tile[2]+'  failed!')
				print(e)
		print('finished all uploads to '+self.tile[2])
		self.tile[3].release()
		self.signals.result.emit(0)
		for url in self.urls:
			if url.fileName().startswith('0x'):
				os.remove(url.toLocalFile())
		self.signals.finished.emit()
		
	def upload_status(self, new_bytes_sent):
		self.bytes_sent += len(new_bytes_sent)
		self.signals.result.emit(int((self.bytes_sent/self.file_size)*100))
		
class Update_worker(QRunnable):

	def __init__(self,connect_to_tile,direct):
		super().__init__()
		self.setAutoDelete(True)
		self.tile = connect_to_tile
		self.directory = direct
		self.signals = WorkerSignals()
		
	def run(self):
		self.tile[3].acquire()
		print('updating ' + self.tile[2])
		try:
			del self.directory[:]
			for i in range(2):
					try:
						self.tile[4].dir(self.directory.append)
						break
					except error_perm as e:
						print('update of '+str(self.tile[2])+' failed! moving on...')
						print(e)
						break
					except error_temp as e:
						print('update of '+str(self.tile[2])+' failed. Retrying in 3s...')
						time.sleep(3)
			print('update of '+self.tile[2]+' finished')
			self.signals.finished.emit()
		except Exception as e:
			print('update of '+self.tile[2]+'failed!')
			print(e)
		self.tile[3].release()
		
class Scan_worker(QRunnable):

	def __init__(self, adress):
		super().__init__()
		self.setAutoDelete(True)
		self.adress = adress
		self.signals = WorkerSignals()
		
	def run(self):
		try:
			ftp = FTP(self.adress, timeout=30)
			print('hit at '+self.adress)
			ftp.set_pasv(False)
			ftp.login()
			info = ftp.getwelcome().split('\n')[0].split('---')[1]
			display_size = info.split(',')[1].strip()
			name = info.split(',')[0]
			if ('esp' in name) or ('ESP' in name):
				print('connected to tile '+name+' at '+str(self.adress)+':21')
				self.signals.result.emit((self.adress,21,name,threading.Semaphore(1),ftp,display_size))
		except:
			return
		
		
class Delete_worker(QRunnable):
	
	def __init__(self,target_tile, target_filenames):
		super().__init__()
		self.setAutoDelete(True)
		self.tile = target_tile
		self.filenames = target_filenames
		self.signals = WorkerSignals()
		
	def run(self):
		self.tile[3].acquire()
		
		try:
			for filename in self.filenames:
				print('deleting '+filename+' from '+self.tile[2])
				self.tile[4].delete(filename)
			print('delete successfull')
			self.signals.finished.emit()
		except Exception as e:
			print('delete failed.')
			print(e)
		self.tile[3].release()

class Convert_worker(QRunnable):
	
	def __init__(self,url,screen_size,tile_orientation,bgcolor=None):
		super().__init__()
		self.setAutoDelete(True)
		self.url = url
		self.signals = WorkerSignals()
		self.width = int(screen_size.split('x')[0])
		self.height = int(screen_size.split('x')[1])
		self.orientation = tile_orientation
		if bgcolor is None:
			self.color = None
		elif bgcolor.startswith('#'):
			self.color = '0x'+bgcolor[1:]
		elif bgcolor.startswith('0x'):
			self.color = bgcolor
		
		
	def run(self):
		converter = Converter(self.width, self.height, self.orientation)
		print('starting conversion of '+self.url.toLocalFile())
		self.signals.result.emit(converter.convert(self.url.toLocalFile(),self.color))


class TileHolder(QFrame):
#Container displaying info about and handling interactions with one tile

	def __init__(self, fatherTile):
		super().__init__()
		self.no_conv = False
		self.setAcceptDrops(True)
		self.tile = fatherTile
		self.directory = list()
		self.setFrameStyle(QFrame.Shape.Box)
		outerLayout = QHBoxLayout()
		self.setLayout(outerLayout)
		#------------- settings widget -----------------
		settingsWidget = QFrame()
		settingsWidget.setFrameStyle(QFrame.Shape.Box)
		settingsLayout = QVBoxLayout()
		settingsWidget.setLayout(settingsLayout)
		
		self.orientation_combo = QComboBox()
		self.orientation_combo.addItems(['portrait','landscape','portrait reversed', 'landscape reversed'])
		
		self.just_upload_cb = QCheckBox('just upload')
		self.just_upload_cb.clicked.connect(self.setting_changed)
		
		self.just_resize_cb = QCheckBox('resize and remove transparency')
		self.just_resize_cb.clicked.connect(self.setting_changed)
		
		self.convert_custom_cb = QCheckBox('convert with custom bgcolor')
		self.convert_custom_cb.clicked.connect(self.setting_changed)
		self.convert_custom_but = QPushButton('pick color')
		self.convert_custom_but.clicked.connect(self.pick_color)
		
		self.convert_cb = QCheckBox('convert with auto bgcolor')
		self.convert_cb.setChecked(True)
		self.convert_cb.clicked.connect(self.setting_changed)
		
		settingsLayout.addWidget(self.orientation_combo)
		settingsLayout.addWidget(self.just_upload_cb)
		settingsLayout.addWidget(self.just_resize_cb)
		settingsLayout.addWidget(self.convert_custom_cb)
		settingsLayout.addWidget(self.convert_custom_but)
		settingsLayout.addWidget(self.convert_cb)
		outerLayout.addWidget(settingsWidget)
		outerLayout.addStretch()
		#------------- label ---------------------------
		outerLayout.addWidget(QLabel(self.tile[2]+'\n'+self.tile[0]+':'+str(self.tile[1])))
		outerLayout.addStretch()
		#------------- progress bar --------------------
		self.progBar = QProgressBar()
		outerLayout.addWidget(self.progBar)
		outerLayout.addStretch()
		#------------- deleteAll button ----------------
		deleteAllButton = QPushButton('delete all')
		deleteAllButton.clicked.connect(self.delete_all)
		outerLayout.addWidget(deleteAllButton)
		outerLayout.addStretch()
		#------------- directory table widget ----------
		table = QVBoxLayout()
		self.tableLayout = table
		tableWidget = QWidget()
		tableWidget.setLayout(table)
		self.tableWidget = tableWidget
		outerLayout.addWidget(tableWidget)
		
		self.update()
	
	def setting_changed(self, newState):
		self.just_upload_cb.setChecked(False)
		self.just_resize_cb.setChecked(False)
		self.convert_custom_cb.setChecked(False)
		self.convert_cb.setChecked(False)
		cb = self.sender()
		cb.setChecked(True)
		
	def pick_color(self):
		if self.convert_custom_but.text() == 'pick color':
			self.convert_custom_but.setText(QColorDialog.getColor().name())
		else:
			self.convert_custom_but.setText(QColorDialog.getColor(initial=QColor(self.convert_custom_but.text())).name())
		self.convert_custom_but.setStyleSheet('QPushButton {color: '+self.convert_custom_but.text()+';}')
	
	def dragEnterEvent(self, e):
		if e.mimeData().hasUrls():
			e.accept()
		else:
			e.ignore()
		
	def dropEvent(self, e):
		if self.just_upload_cb.isChecked():
			worker = Upload_worker(self.tile,e.mimeData().urls())
			worker.signals.finished.connect(self.update)
			worker.signals.result.connect(self.__update_progBar)
			threadpool.start(worker)
			return
		elif self.just_resize_cb.isChecked():
			for url in e.mimeData().urls():
				conv_worker = Convert_worker(url,self.tile[5],self.orientation_combo.currentIndex(),'#000000')
				conv_worker.signals.result.connect(self.__convert_done)
				threadpool.start(conv_worker)
		elif self.convert_custom_cb.isChecked():
			for url in e.mimeData().urls():
				if self.convert_custom_but.text() == 'pick color':
					print('No color picked, aborting')
					return
				conv_worker = Convert_worker(url,self.tile[5],self.orientation_combo.currentIndex(),self.convert_custom_but.text())
				conv_worker.signals.result.connect(self.__convert_done)
				threadpool.start(conv_worker)
		elif self.convert_cb.isChecked():
			for url in e.mimeData().urls():
				conv_worker = Convert_worker(url,self.tile[5],self.orientation_combo.currentIndex())
				conv_worker.signals.result.connect(self.__convert_done)
				threadpool.start(conv_worker)

				
	def __convert_done(self,filepath):
		self.last_uploaded = filepath
		worker = Upload_worker(self.tile,[QUrl.fromLocalFile(filepath)])
		worker.signals.finished.connect(self.update)
		worker.signals.result.connect(self.__update_progBar)
		threadpool.start(worker)
		
		
	def __update_progBar(self, value):
		self.progBar.setValue(value)
		
	
	def delete_all(self):
		cleanDir = list()
		self.update()
		if not self.directory:
			return
		for line in self.directory:
			cleanDir.append(line.split()[-1])
		worker = Delete_worker(self.tile,cleanDir)
		worker.signals.finished.connect(self.update)
		threadpool.start(worker)
		
		
	def update(self):
		worker = Update_worker(self.tile, self.directory)
		worker.signals.finished.connect(self.__update_finished)
		threadpool.start(worker)
		
	def __update_finished(self):
		for i in reversed(range(self.tableLayout.count())): 
			self.tableLayout.itemAt(i).widget().setParent(None)
		for line in self.directory:
			self.tableLayout.addWidget(Entry(self.tile,line.split()[-1]))
		
			
		
class Entry(QWidget):
	
	def __init__(self,fatherTile,label_text):
		super().__init__()
		self.tile = fatherTile
		if label_text.startswith('0x'):
			self.label = QLabel(''.join(label_text.split('_')[1:])[1:])
		else:
			self.label = QLabel(label_text)
		
		self.filename = list()
		self.filename.append(label_text)
		self.delButton = QPushButton('x')
		self.delButton.clicked.connect(self.delete_from_server)
		entryLayout = QHBoxLayout()
		entryLayout.addWidget(self.label)
		entryLayout.addWidget(self.delButton)
		self.setLayout(entryLayout)
		
	def delete_from_server(self):
		worker = Delete_worker(self.tile,self.filename)
		worker.signals.finished.connect(self.__del_finished)
		threadpool.start(worker)
	
	def __del_finished(self):
		self.setParent(None)


def scan_for_tiles():
	if threadpool.activeThreadCount() > 0:
		print('Operations are still active please wait until they\'ve finished.')
		return
	if tiles:
		for tile in tiles:
			try:
				tile[4].quit()
			except:
				pass
	del tiles[:]
	print('scanning for tiles in the network')
	host_adress = socket.gethostbyname(socket.gethostname()).split('.')
	subnet_adress = host_adress[0]+'.'+host_adress[1]+'.'+host_adress[2]+'.'
	for i in range(1,254):
		adress = subnet_adress+str(i)
		worker = Scan_worker(adress)
		worker.signals.result.connect(add_tile)
		threadpool.start(worker)	
			

def add_tile(found_tile):
	tiles.append(found_tile)
	redraw_all()

def update_all():
	print('updating all tiles')
	for frame in frames:
		frame.update()
		
def redraw_all():
	print('redrawing')
	for widget in app.allWidgets():
		widget.setParent(None)
	del frames[:] 
	for tile in tiles: 
		if tile[1]==21:
			frame = TileHolder(tile)
			frames.append(frame)
			layout.addWidget(frame)
	buttonBar = QWidget()
	buttonLayout = QHBoxLayout()
	buttonBar.setLayout(buttonLayout)
	layout.addWidget(buttonBar)
	updateButton = QPushButton('refresh tile contents')
	updateButton.clicked.connect(lambda: update_all())
	buttonLayout.addWidget(updateButton)
	rescanButton = QPushButton('scan for tiles again')
	rescanButton.clicked.connect(lambda: scan_for_tiles())
	buttonLayout.addWidget(rescanButton)
	print('redrawing finished')

#def create_tile_base
tiles = list()
frames = list()
scan_for_tiles()
# Start the event loop.
app.exec()
#make sure, that the ftp connections are closed when the app ends
print('cleaning up')
for tile in tiles:
	try:
		target=tile[4].quit()
	except Exception as e:
		print(e)


    
    
