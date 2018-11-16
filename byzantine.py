from sys import argv
import socket
import threading
import json
from anytree import AnyNode

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
		self.root = None
		self.listener = threading.Thread(target=self.receive)
		self.listener.start()

	def decide(self):
		print("Process", self.id, "has decided", self.value)

	def construct_message(self, path, value):
  		message = {}
  		message["path"] = path
  		message["value"] = value
  		return json.dumps(message)

	def send(self, ip, port, message):
		self.sock.sendto(message.encode('utf-8'), (ip, port))

	def multicast(self, group, message):
		for member in group:
			self.send(member["ip"], member["port"], message)

	def receive(self):
		while True:
		    message, addr = self.sock.recvfrom(1024)
		    message = json.loads(message.decode('utf-8'))
		    self.handle_message(message)

	def handle_message(self, message):
		if m == 0:
			self.value = message["value"]
			self.decide()
		else:
			path = message["path"]
			#Handle data
			#Commander message, empty tree
			if len(message["path"]) == 1:
				self.root = AnyNode(id=path[0], value=message["value"], decide_value=None)
			else:
				r = Resolver('id')
				last_node = r.get('/'.join(path[:-1]))
				AnyNode(id=path[-1], value=message["value"], decide_value=None, parent=last_node)
			if self.id not in path:
				path.append(self.id)

			

	def oral_messages(self, m):
		#Commander
		if self.id == 0:
			self.value = 'attack'
			message = self.construct_message([self.id], self.value)
			self.multicast(self.process_list[1:], message)

processes_info = [{"ip":"localhost", "port":9000 + i, "id":i} for i in range(n)]
processes = [Process(process["ip"], process["port"], process["id"], processes_info) for process in processes_info]

processes[0].oral_messages(m)