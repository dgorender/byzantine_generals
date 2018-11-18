import sys 
import os
import socket
import threading
import json
import random
from collections import Counter
from anytree import AnyNode, RenderTree, Resolver, LevelOrderIter

#Read input
n, m, is_commander_traitor = [int(x) for x in sys.argv[1:]]
if (n < 3*m + 1) or (is_commander_traitor == 1 and m == 0):
	print("It is impossible to solve the byzantine generals problem for that configuration")

#Majority function
def majority(values):
	counter = Counter(values)
	maj = counter.most_common()
	if len(maj) > 1 and maj[0][1] == maj[1][1]:
		return 'retreat'
	else:
		return maj[0][0]

class Process:

	def __init__(self, ip, port, process_id, process_list):
		self.ip = ip
		self.port = port
		self.id = process_id
		self.process_list = process_list
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((ip, port))
		if process_id == "0":
			self.value = "attack"
		else:
			self.value = ''
		self.loyal = True
		self.root = None
		self.listener = threading.Thread(target=self.receive)
		self.listener.start()

	def setLoyalty(self, loyalty):
		self.loyal = loyalty

	def print_decision(self):
		print("Process", self.id, "has decided", self.value)

	def construct_message(self, path, value):
			message = {}
			message["path"] = path
			message["value"] = value
			return message

	def send(self, ip, port, message):
		if self.loyal == False:
			message["value"] = random.choice(["attack", "retreat"])
		self.sock.sendto(json.dumps(message).encode('utf-8'), (ip, port))

	def multicast(self, group, message):
		for member in group:
			self.send(member["ip"], member["port"], message)

	def receive(self):
		while self.value == '':
		    message, addr = self.sock.recvfrom(1024)
		    message = json.loads(message.decode('utf-8'))
		    self.handle_message(message)

	def handle_message(self, message):
		#m = 0
		if m == 0:
			self.value = message["value"]
			self.decide()
		#m > 0
		else:
			path = message["path"]
			#Commander message, empty tree
			if len(message["path"]) == 1:
				self.root = AnyNode(id=path[0], value=message["value"], decide_value=message["value"], name=path[0])
			#Message from a lieutenant
			else:
				#Get last known node on path and add new node as its child
				r = Resolver('id')
				last_node = r.get(self.root, '/'.join(path[1:-1]))
				AnyNode(id=path[-1], value=message["value"], decide_value=message["value"], parent=last_node, name=path[-1])
			if self.id not in path and len(path) <= m:
				#If possible, apend its own id to the path and broadcast the message
				path.append(self.id)
				message = self.construct_message(path, message["value"])
				self.multicast(self.process_list[1:], message)
			leafs = [node for node in LevelOrderIter(self.root) if node.is_leaf]

			if (len(leafs) == (n - 1) * (n - m)) or (m == 1 and len(leafs) == (n - 1)):
				#If already received all the messages, start phase 2
				reverse_nodes = [node for node in LevelOrderIter(self.root)][::-1]
				for node in reverse_nodes:
					if not node.is_leaf:
						node.decide_value = majority([n.decide_value for n in node.children])
				self.value = self.root.decide_value
				print("Process", self.id, "has decided", self.value)
				#print("Process", self.id, "has decided", self.value)
				with open('./results/' + self.id + ".txt", "w") as f:
					print(self.id, RenderTree(self.root), file=f)				

	def oral_messages(self, m):
		#Commander
		if self.id == "0":
			message = self.construct_message([self.id], self.value)
			self.multicast(self.process_list[1:], message)

processes_info = [{"ip":"localhost", "port":9000 + i, "id":str(i)} for i in range(n)]
processes = [Process(process["ip"], process["port"], process["id"], processes_info) for process in processes_info]
if is_commander_traitor:
	traitors = [0] + random.sample(range(1, n), m-1)
else:
	traitors = random.sample(range(1,n), m)
for traitor in traitors:
	processes[traitor].setLoyalty(False)

print(traitors)

processes[0].oral_messages(m)