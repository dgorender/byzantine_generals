from sys import argv
import socket
import threading
import json

n, m, is_commander_traitor = [int(x) for x in argv[1:]]
if n < 3*m + 1:
	print("It is impossible to solve the byzantine generals problem for that configuration")

class Process:

	def __init__(self, ip, port, process_id, process_list):
		self.ip = ip
		self.port = port
		self.id = process_id
		self.process_list = process_list
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((ip, port))
		self.value = ''
		listener = threading.Thread(target=self.receive)
		listener.start()

	def send(self, ip, port, message):
		self.sock.sendto(message.encode('utf-8'), (ip, port))

	def multicast(self, group, message):
		for member in group:
			self.send(member["ip"], member["port"], message)

	def construct_message(self, process_id, value):
  		message = {}
  		message["id"] = process_id
  		message["value"] = value
  		return json.dumps(message)

	def receive(self):
		while True:
		    data, addr = self.sock.recvfrom(1024)
		    print(self.id, "Message: ", data)

	def oral_messages(self, m):
		if m == 0:
			#Commander
			if self.id == 0:
				self.value = 'attack'
				message = self.construct_message(self.id, self.value)
				self.multicast(self.process_list[1:], message)

	def run(self):
		if self.id == 0:
			self.oral_messages(m)

processes_info = [{"ip":"localhost", "port":9000 + i, "id":i} for i in range(n)]
processes = [Process(process["ip"], process["port"], process["id"], processes_info) for process in processes_info]

for p in processes:
	p.run()