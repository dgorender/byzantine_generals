import sys 
import os
import socket
import threading
import json
import random
from math import factorial
from collections import Counter
from anytree import AnyNode, RenderTree, Resolver, LevelOrderIter
from time import sleep

#Read input
n, m, is_commander_traitor = [int(x) for x in sys.argv[1:]]
if (n < 3*m + 1) or (is_commander_traitor == 1 and m == 0):
	print("It is impossible to solve the byzantine generals problem for that configuration")

n_leafs = factorial(n - 1) / factorial(n - m - 1)

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
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind((ip, port))
		self.sock.listen(9999999)
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

	def has_path(self, path):
		r = Resolver('id')
		try:
			r.get(self.root, path)
			return True
		except:
			return False

	def construct_message(self, path, value):
			message = {}
			message["path"] = path
			message["value"] = value
			return message

	def send(self, ip, port, message):
		s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		if self.loyal == False:
			message["value"] = random.choice(["attack", "retreat"])
		s.connect((ip, port))
		s.sendall(json.dumps(message).encode('utf-8'))
		#print(port - 10000, message)
		s.close()
		with open("./debug/sended.txt", "a") as f:
			print(self.id, str(port - 10000), message["path"], file=f)

	def multicast(self, group, message):
		for member in group:
			self.send(member["ip"], member["port"], message)

	def receive(self):
		messages = []
		while self.value == '':
			conn, addr = self.sock.accept()
			message = conn.recv(1024)
			#print(self.id, message)
			if not message:
				break
			conn.close()
			message = json.loads(message.decode('utf-8'))
			#print(message)
			with open("./debug/received.txt", "a") as f:
					print(self.id, message["path"], file=f)
			messages = [message] + messages
			#print(self.id, messages)
			#Handle "out of order" messages due to distribution
			for m in messages:
				if len(m["path"]) == 1 or self.has_path('/'.join(m["path"][1:-1])):
					#print(self.id, m)
					self.handle_message(m)
					messages.remove(m)
					with open('./debug/' + self.id + ".txt", "w") as f:
						print(self.id, RenderTree(self.root), file=f)
			#print(self.id, messages)

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
				with open("./debug/messages_handled_lieutenant.txt", "a") as f:
					print(self.id, message["path"], path[-1], file=f)
				r = Resolver('id')
				last_node = r.get(self.root, '/'.join(path[1:-1]))
				AnyNode(id=path[-1], value=message["value"], decide_value=message["value"], parent=last_node, name=path[-1])
				with open("./debug/all_tree_operations.txt", "a") as f:
					print(self.id, message["path"], last_node.id, path[-1], file=f)
			if self.id not in path and len(path) <= m:
				#If possible, apend its own id to the path and broadcast the message
				path.append(self.id)
				message = self.construct_message(path, message["value"])
				self.multicast(self.process_list[1:], message)
			leafs = [node for node in LevelOrderIter(self.root) if node.is_leaf]

			if len(leafs) == n_leafs:
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

processes_info = [{"ip":"localhost", "port":10000 + i, "id":str(i)} for i in range(n)]
processes = [Process(process["ip"], process["port"], process["id"], processes_info) for process in processes_info]
if is_commander_traitor:
	traitors = [0] + random.sample(range(1, n), m-1)
else:
	traitors = random.sample(range(1,n), m)
for traitor in traitors:
	processes[traitor].setLoyalty(False)

processes[0].oral_messages(m)