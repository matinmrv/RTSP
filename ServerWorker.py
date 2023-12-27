from random import randint
import sys, traceback, threading, socket
import os
from VideoStream import VideoStream
from RtpPacket import RtpPacket

class ServerWorker:
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'
	
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2
	
	clientInfo = {}
	
	def __init__(self, clientInfo):
		self.clientInfo = clientInfo
		
	def run(self):
		threading.Thread(target=self.recvRtspRequest).start()
	
	def recvRtspRequest(self):
		connSocket = self.clientInfo['rtspSocket'][0]
		while True:            
			data = connSocket.recv(256)
			if data:
				print("Data received:\n")
				self.processRtspRequest(data.decode("utf-8"))
	
	def processRtspRequest(self, data):
		request = data.split('\n')
		print(request)

		requestType = request[0].split(' ')[0]
		print("requestType: ", requestType)
		
		if requestType == "SETUP":
			filename = request[1].split(' ')[0]
			print("filename: ", filename)
		
			seq = request[2].split(' ')
			print("seq: ", seq[0])
		else:
			seq = request[1].split(' ')
			print("seq: ", seq)

		if requestType == self.SETUP:
			if self.state == self.INIT:
				print("processing SETUP\n")
				
				try:
					self.clientInfo['videoStream'] = VideoStream(filename)
					self.state = self.READY
					print("state: READY") 

				except IOError:
					self.replyRtsp(self.FILE_NOT_FOUND_404, seq[0]) 
					print("File not found")
				
				self.clientInfo['session'] = randint(100000, 999999)
				print("session created") 
				
				self.replyRtsp(self.OK_200, seq[0])
				print("reply ok")

				self.clientInfo['rtpPort'] = request[-1].split(' ')[3]
				print("SETUP REQUEST WORKING!")
		
		
		elif requestType == self.PLAY:
			if self.state == self.READY:
				print("processing PLAY\n")
				self.state = self.PLAYING
				
				self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				print("server rtpSocket", self.clientInfo["rtpSocket"])
				print("rtp socket created")

				self.replyRtsp(self.OK_200, seq[0])
				
				self.clientInfo['event'] = threading.Event()
				self.clientInfo['worker']= threading.Thread(target=self.sendRtp) 
				self.clientInfo['worker'].start()
				
				print("PLAY REQUEST WORKING!")
		
		elif requestType == self.PAUSE:
			if self.state == self.PLAYING:
				print("processing PAUSE\n")
				self.state = self.READY
				
				self.clientInfo['event'].set()
			
				self.replyRtsp(self.OK_200, seq[0])

				print("PAUSE REQUEST WORKING!")
		
		elif requestType == self.TEARDOWN:
			print("processing TEARDOWN\n")

			self.clientInfo['event'].set()
			
			self.replyRtsp(self.OK_200, seq[0])
			
			self.clientInfo['rtpSocket'].close()
			
	def sendRtp(self):
		while True:
			self.clientInfo['event'].wait(0.05) 
			
			if self.clientInfo['event'].isSet(): 
				break 
				
			data = self.clientInfo['videoStream'].nextFrame()
			
			if data: 
				frameNumber = self.clientInfo['videoStream'].frameNbr()
				print(frameNumber)

				try:
					address = self.clientInfo['rtspSocket'][1][0]
					port = int(self.clientInfo['rtpPort'])
					print(address, port)

					self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber),(address,port))
				except:
					print("Connection Error")


	def makeRtp(self, payload, frameNbr):
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0 
		
		rtpPacket = RtpPacket()
		
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		
		return rtpPacket.getPacket()
		
	def replyRtsp(self, code, seq):
		if code == self.OK_200:
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())
		
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")
