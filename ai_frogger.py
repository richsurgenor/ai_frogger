import numpy as np
import PIL
#import screen
import time
from time import sleep
from datetime import datetime
import pyscreenshot as imageGrab
import keyboard
import cv2

#img_rgb = cv2.imread('sample2.png')

import json
# with open('data.json', 'w') as fp:
#     json.dump(data, fp)


# with open('data.json', 'r') as fp:
#     data = json.load(fp)


template_names = ["frog1", "frog2", "frog3", "frog4",
				  "car0left", "car1right" , "car2left" , "car3right" , "car4left" ]
x1,y1,x2,y2 = 400,472,1054,777 #508


decisions = {0 : "up",
			 1 : "down",
			 2 : "left",
			 3 : "right",
			 4 : "wait"}

D_0, D_1, D_2, D_3, D_4 = 6, 0, 4, 2, -10 #30, 10, 20, 20, 20 wait
REWARD = 5
FAIL = -3

class FroggerBot(object):
	def __init__(self):
		self.threshold = 0.7
		self.templates = [] # list of dictionaries
		self.objects = []	# list of dictionaries
		self.frog = None
		self.previous_state = None
		self.database = AIDatabase()
		self.generate_templates()


	def run(self):
		# self.img = np.array(imageGrab.grab(bbox=(400,108,1054,777)).convert('RGB'))
		
		#self.sample = cv2.imread('sample.png')
		
		i = -1
		while not self.frog:
			self.img = np.array(imageGrab.grab(bbox=(x1,y1,x2,y2)).convert('RGB'))
			self.process_objects()
			print ("I VALUE FOR FROG" + str(i))
			i += 1


		if self.previous_state:
			curModel = self.database.lookup_model(self.previous_state[0], self.previous_state[1], self.previous_state[2])
			if curModel:
				if i:
					#punishment
					print ("frog is being punished")
					curModel[self.last_move] += FAIL
				else:
					#reward
					print ("frog is being rewarded")
					curModel[self.last_move] += REWARD



		state_parameter1 = state_parameter2 = state_parameter3 = 0

		for item in self.objects:
			# print (item["loc"])
			if len(item["loc"]):
				vertical_displacement = self.frog["y"] - item["loc"][1][0]

				print ("vertical:"+str(vertical_displacement))
				if abs(vertical_displacement) < 150:
					bucket = int(self.calculate_bucket(item["loc"][0][0])) # only value in the array
					if abs(vertical_displacement) < 20:
						state_parameter2 = bucket
					elif vertical_displacement > 0:
						state_parameter1 = bucket
					else:
						state_parameter3 = bucket

					#print ("Bucket"+str(bucket) + "y" + str(item["loc"][1][0]))
		print(state_parameter1, state_parameter2, state_parameter3)

		self.make_decision(state_parameter1, state_parameter2, state_parameter3)

		self.previous_state = [state_parameter1,state_parameter2,state_parameter3]
		

		self.objects = []
		self.frog = None
		print("--- %s seconds end run ---" % (time.time() - start_time))

	#def make_decision(self, state_param1, state_param2, state_param3):


	def make_decision(self, state_parameter1, state_parameter2, state_parameter3):
		model = self.database.lookup_model(state_parameter1, state_parameter2, state_parameter3)

		#print ("MODEL TYPE " + str(type (model)))
		if not model:
			model = self.database.insert_model(state_parameter1, state_parameter2, state_parameter3)

		maximum = max(model)
		index = model.index(maximum)

		self.last_move = index

		mov = decisions[index]

		print ("MODEL : {} {} {}".format(state_parameter1, state_parameter2, state_parameter3))
		print ("CURRENT VALS : " + str(model))
		if mov == "wait":
			sleep(0.05) # pass
		else:
			self.move(mov)

	def move(self, direction):
		keyboard.press_and_release(direction)


	def calculate_bucket(self, x):
		return round(x/128)

	def generate_templates(self):
		for name in template_names:
			_template = {}
			_template["name"] = name
			_template["content"] = np.array(PIL.Image.open(name + ".png").convert('RGB'))
			#cv2.imread(name + ".png")
			# cv2.imwrite('blah.png', _template['content'])

			self.templates.append(_template)

	def process_objects(self):
		found_frog = False
		for template in self.templates:

			_object = {}
			_object["w"] = template["content"].shape[:-1][0]
			_object["h"] = template["content"].shape[:-1][1]
			_object["res"] = cv2.matchTemplate(self.img, template["content"], cv2.TM_CCOEFF_NORMED)
			_object["loc"] = np.where(_object["res"] >= self.threshold)

			if "right" in template["name"]:
				_object["direction"] = 0
			else:
				_object["direction"] = 1

			# self.filter_locations(_object["loc"])
			for x in _object['loc']:
				x = self.remove_duplicates(x)

			if "frog" in template["name"] and len(_object['loc'][0])>0:
				self.frog = { "x" : _object['loc'][1][0],
							  "y" : _object['loc'][0][0]}
				found_frog = True


			elif "frog4" in template["name"] and not self.frog:
		  		#print ("PUNISHMENT")
		  		break
				
			elif "frog" in template["name"]:
				continue


				# if "x" not in self.frog and not "y" in self.frog:
				# 	if found_frog:
				# 		continue
				# 	else:
				# 		pass
				# else:
				# 	found_frog = True

				# print "frog position" + str(self.frog)
			


			print("We are on car "+str(template['name']))
			list1 = self.filter_locations(_object["loc"][1], self.frog["x"], _object['direction'])
			if list1:
				list2 = [_object['loc'][0][0]]
				_object["loc"] = tuple([list1, list2])
			else:
				_object["loc"] = tuple()
				continue

			for pt in zip(*_object["loc"]):
				# at this point if the object was found there will be a defined point
				cv2.rectangle(self.img, pt, (pt[0] + _object["h"], pt[1] + _object["w"]), (0, 0, 255), 2)
				#print ("MAKE RECTANGLE")
		#print (_object["loc"])

		
			if "frog" not in template["name"]:
				self.objects.append(_object)	
		cv2.imwrite('result.png', self.img)

	def remove_duplicates(self, x_array):
		x_array = list(set(x_array))
		return x_array

	def filter_locations(self, _array, frog, direction):
		unique_vals = []
		slack=10
		new_array = []

		for val in _array:
			true_val = int(val) - int(frog) # value relative to frog
			if direction == 0 and true_val <= 0: #moving right
				if len(new_array) == 0:
					new_array.append(val)
				else:
					new_value = True
					for x in new_array:
						if (abs(x - val) < slack):
							new_value = False
							break
					if new_value:
						new_array = [val]

			elif direction == 1 and true_val >= 0: #moving left
				if len(new_array) == 0:
					new_array.append(val)
				else:
					new_value = True
					for x in new_array:
						if (abs(x - val) < slack):
							new_value = False
							break
					if new_value:
						new_array = [min(new_array[0], (val))]
		# print("This is where we are "+str(new_array))
		return new_array



def capture(filename="sample.png"):
	screenshot=imageGrab.grab(bbox=(406,142,1033,773))
	screenshot.save(filename)
	print (datetime.now() - startTime)


class AIDatabase(object):

	def __init__(self):
		self.models = {}

	def save_database(self):
		with open('models.json', 'w+') as fp:
			json.dump(self.models, fp)

	def load_database(self):
		with open('models.json', 'r') as fp:
			self.models = json.load(fp)

	def insert_model(self, state_param1, state_param2, state_param3):
		to_insert = self.models["{} {} {}".format(state_param1, state_param2, state_param3)] = [D_0, D_1, D_2, D_3, D_4]
		return to_insert

	def lookup_model(self, state_param1, state_param2, state_param3):
		lookup = "{} {} {}".format(state_param1, state_param2, state_param3)
		if lookup in self.models.keys():
			return self.models["{} {} {}".format(state_param1, state_param2, state_param3)]

		return None



if __name__ == "__main__":
	keyboard.wait('0')
	start_time = time.time()
	frog = FroggerBot()

	n = 0
	while True:
		frog.run()

	# print(str(++n) + " ITERATION")
	print("--- %s seconds end ---" % (time.time() - start_time))

