#!/usr/bin/env python

'''
480,437,109
371,328,40
This python file runs a ROS-node of name drone_control which holds the position of e-Drone on the given dummy.
This node publishes and subsribes the following topics:

		PUBLICATIONS			SUBSCRIPTIONS
		/drone_command			/whycon/poses
		/alt_error				/pid_tuning_altitude
		/pitch_error			/pid_tuning_pitch
		/roll_error				/pid_tuning_roll
					
								

Rather than using different variables, use list. eg : self.setpoint = [1,2,3], where index corresponds to x,y,z ...rather than defining self.x_setpoint = 1, self.y_setpoint = 2
CODE MODULARITY AND TECHNIQUES MENTIONED LIKE THIS WILL HELP YOU GAINING MORE MARKS WHILE CODE EVALUATION.	
'''

# Importing the required libraries

from edrone_client.msg import *
from geometry_msgs.msg import PoseArray
from std_msgs.msg import Int16
from std_msgs.msg import Int64
from std_msgs.msg import Float64
from pid_tune.msg import PidTune
from math import ceil,floor
import rospy
import time


class Edrone():
	"""docstring for Edrone"""
	def __init__(self):
		
		rospy.init_node('drone_control')	# initializing ros node with name drone_control

		# This corresponds to your current position of drone. This value must be updated each time in your whycon callback
		# [x,y,z]
		self.drone_position = [0.0,0.0,0.0]	

		# [x_setpoint, y_setpoint, z_setpoint]
		self.setpoint = [2,2,20] # whycon marker at the position of the dummy given in the scene. Make the whycon marker associated with position_to_hold dummy renderable and make changes accordingly


		#Declaring a cmd of message type edrone_msgs and initializing values
		self.cmd = edrone_msgs()
		self.cmd.rcRoll = 1500
		self.cmd.rcPitch = 1500
		self.cmd.rcYaw = 1500
		self.cmd.rcThrottle = 1500
		self.cmd.rcAUX1 = 1500
		self.cmd.rcAUX2 = 1500
		self.cmd.rcAUX3 = 1500
		self.cmd.rcAUX4 = 1500


		#initial setting of Kp, Kd and ki for [roll, pitch, throttle]. eg: self.Kp[2] corresponds to Kp value in throttle axis
		#after tuning and computing corresponding PID parameters, change the parameters
		'''self.Kp = [350,372,328]
		self.Ki = [99,100,359]
		self.Kd = [110,110,44]'''
		self.Kp = [21.6,22.8,30.12]
		self.Kd = [33.6,35.1,19.8]
		self.Ki = [0.872,0.872,3.672]
		'''self.Kp = [21.0,0,0]
		self.Ki = [33.0,0,0]
		self.Kd = [0.792,0,0]'''
		'''self.Kp=[0,0,0]
		self.Ki=[0,0,0]
		self.Kd=[0,0,0]'''

		#-----------------------Add other required variables for pid here ----------------------------------------------

		self.cur_error = [0,0,0]
		self.prev_error = [0,0,0]
		self.te = [0,0,0]
		self.outRoll = 0
		self.outThrottle = 0
		self.outPitch = 0
		self.outYaw = 0




		# Hint : Add variables for storing previous errors in each axis, like self.prev_values = [0,0,0] where corresponds to [pitch, roll, throttle]		#		 Add variables for limiting the values like self.max_values = [2000,2000,2000] corresponding to [roll, pitch, throttle]
		#													self.min_values = [1000,1000,1000] corresponding to [pitch, roll, throttle]
		#																	You can change the upper limit and lower limit accordingly. 
		#----------------------------------------------------------------------------------------------------------

		# # This is the sample time in which you need to run pid. Choose any time which you seem fit. Remember the stimulation step time is 50 ms
		self.sample_time = 0.050# in seconds






		# Publishing /drone_command, /alt_error, /pitch_error, /roll_error
		self.command_pub = rospy.Publisher('/drone_command', edrone_msgs, queue_size=1)
		#------------------------Add other ROS Publishers here-----------------------------------------------------
		self.pub1 = rospy.Publisher('/pitch_error/data', Float64, queue_size=10)
		self.pub2 = rospy.Publisher('/roll_error/data', Float64, queue_size=10)
		self.pub3 = rospy.Publisher('/throttle_error/data', Float64, queue_size=10)






		#-----------------------------------------------------------------------------------------------------------


		# Subscribing to /whycon/poses, /pid_tuning_altitude, /pid_tuning_pitch, pid_tuning_roll
		rospy.Subscriber('whycon/poses', PoseArray, self.whycon_callback)
		#rospy.Subscriber('/pid_tuning_altitude',PidTune,self.altitude_set_pid)
		#-------------------------Add other ROS Subscribers here----------------------------------------------------
		#rospy.Subscriber('/pid_tuning_roll',PidTune,self.roll_set_pid)
		#rospy.Subscriber('/pid_tuning_pitch',PidTune,self.pitch_set_pid)
		#rospy.Subscriber('/pid_tuning_yaw',PidTune,self.yaw_set_pid)


		#------------------------------------------------------------------------------------------------------------

		self.arm() # ARMING THE DRONE


	# Disarming condition of the drone
	def disarm(self):
		self.cmd.rcAUX4 = 1100
		self.command_pub.publish(self.cmd)
		rospy.sleep(1)


	# Arming condition of the drone : Best practise is to disarm and then arm the drone.
	def arm(self):

		self.disarm()

		self.cmd.rcRoll = 1500
		self.cmd.rcYaw = 1500
		self.cmd.rcPitch = 1500
		self.cmd.rcThrottle = 1000
		self.cmd.rcAUX4 = 1500
		self.command_pub.publish(self.cmd)	# Publishing /drone_command
		rospy.sleep(1)



	# Whycon callback function
	# The function gets executed each time when /whycon node publishes /whycon/poses 
	def whycon_callback(self,msg):
		self.drone_position[0] = msg.poses[0].position.x

		#--------------------Set the remaining co-ordinates of the drone from msg----------------------------------------------
		self.drone_position[1] = msg.poses[0].position.y
		self.drone_position[2] = msg.poses[0].position.z


		
		#---------------------------------------------------------------------------------------------------------------



	# Callback function for /pid_tuning_altitude
	# This function gets executed each time when /tune_pid publishes /pid_tuning_altitude
	
	'''def altitude_set_pid(self,alt):
		self.Kp[2] = alt.Kp * 0.06 # This is just for an example. You can change the ratio/fraction value accordingly
		self.Ki[2] = alt.Ki * 0.008
		self.Kd[2] = alt.Kd * 0.3
		print(alt.Kp)
		#self.do_nothing =1

	#----------------------------Define callback function like altitide_set_pid to tune pitch, roll--------------
	def roll_set_pid(self,alt):
		self.Kp[0] = alt.Kp * 0.06 # This is just for an example. You can change the ratio/fraction value accordingly
		self.Ki[0] = alt.Ki * 0.008
		self.Kd[0] = alt.Kd * 0.3
		#self.do_nothing =1
		
	def pitch_set_pid(self,alt):
		self.Kp[1] = alt.Kp * 0.06 # This is just for an example. You can change the ratio/fraction value accordingly
		self.Ki[1] = alt.Ki * 0.008
		self.Kd[1] = alt.Kd * 0.3
		#self.do_nothing =1
	def yaw_set_pid(self,alt):
		self.do_nothing = 1'''
		
	#################
	'''def altitude_set_pid(self,alt):
		self.Kp[2] = 328 * 0.06 # This is just for an example. You can change the ratio/fraction value accordingly
		self.Ki[2] = 359 * 0.008
		self.Kd[2] = 44 * 0.3
		print(alt.Kp)
		#self.do_nothing =1

	#----------------------------Define callback function like altitide_set_pid to tune pitch, roll--------------
	def roll_set_pid(self,alt):
		self.Kp[0] = 349 * 0.06 # This is just for an example. You can change the ratio/fraction value accordingly
		self.Ki[0] = 100 * 0.008
		self.Kd[0] = 109 * 0.3
		#self.do_nothing =1
		
	def pitch_set_pid(self,alt):
		self.Kp[1] = 371 * 0.06 # This is just for an example. You can change the ratio/fraction value accordingly
		self.Ki[1] = 100 * 0.008
		self.Kd[1] = 109 * 0.3
		#self.do_nothing =1
	def yaw_set_pid(self,alt):
		self.do_nothing = 1'''
	############################
	#----------------------------------------------------------------------------------------------------------------------


	def pid(self):
	#-----------------------------Write the PID algorithm here--------------------------------------------------------------

	# Steps:
	# 	1. Compute error in each axis. eg: error[0] = self.drone_position[0] - self.setpoint[0] ,where error[0] corresponds to error in x...
	#	2. Compute the error (for proportional), change in error (for derivative) and sum of errors (for integral) in each axis. Refer "Understanding PID.pdf" to understand PID equation.
	#	3. Calculate the pid output required for each axis. For eg: calcuate self.out_roll, self.out_pitch, etc.
	#	4. Reduce or add this computed output value on the avg value ie 1500. For eg: self.cmd.rcRoll = 1500 + self.out_roll. LOOK OUT FOR SIGN (+ or -). EXPERIMENT AND FIND THE CORRECT SIGN
	#	5. Don't run the pid continously. Run the pid only at the a sample time. self.sampletime defined above is for this purpose. THIS IS VERY IMPORTANT.
	#	6. Limit the output value and the final command value between the maximum(2000) and minimum(1000)range before publishing. For eg : if self.cmd.rcPitch > self.max_values[1]:
	#																														self.cmd.rcPitch = self.max_values[1]
	#	7. Update previous errors.eg: self.prev_error[1] = error[1] where index 1 corresponds to that of pitch (eg)
	#	8. Add error_sum


		'''Throttle = self.cmd.rcThrottle
		Pitch = self.cmd.rcPitch
		Roll = self.cmd.rcRoll'''
		cur_error = [self.setpoint[0] - self.drone_position[0],self.setpoint[1] - self.drone_position[1],self.setpoint[2] - self.drone_position[2]]
		
		#outThrottle = (cur_error[2]*self.Kp[2]) + (cur_error[2] - self.prev_error[2])*self.Kd[2]/self.sample_time
		
		'''self.Kp = [21.0,22.14,19.74]
		self.Kd = [33.0,33.0,13.2]
		self.Ki = [0.792,0.8,2.88]
		'''
		print("kp",self.Kp)
		print("ki",self.Ki)
		print("kd",self.Kd)
		'''throttle_error = [cur_error[2]*19.22,(cur_error[2] - self.prev_error[2])*2.88/self.sample_time,(cur_error[2] + self.te[2])*13.2*self.sample_time]
		pitch_error=[cur_error[1]*22,(cur_error[1] - self.prev_error[1])*0.8/self.sample_time,(cur_error[1] + self.te[1])*33*self.sample_time]
		roll_error=[cur_error[0]*21,(cur_error[0] - self.prev_error[0])*0.792/self.sample_time,(cur_error[0] + self.te[0])*33*self.sample_time]'''
		
		throttle_error = [cur_error[2]*self.Kp[2],(cur_error[2] - self.prev_error[2])*self.Kd[2]/self.sample_time,(cur_error[2] + self.te[2])*self.Ki[2]*self.sample_time]
		pitch_error=[cur_error[1]*self.Kp[1],(cur_error[1] - self.prev_error[1])*self.Kd[1]/self.sample_time,(cur_error[1] + self.te[1])*self.Ki[1]*self.sample_time]
		roll_error=[cur_error[0]*self.Kp[0],(cur_error[0] - self.prev_error[0])*self.Kd[0]/self.sample_time,(cur_error[0] + self.te[0])*self.Ki[0]*self.sample_time]
		#p = (cur_error[2]*self.Kp[2])
		#d = (cur_error[2] - self.prev_error[2])*self.Kd[2]/self.sample_time
		#i = (cur_error[2] + self.te)*self.Ki[2]*self.sample_time
		
		"""if i > 0:
			i = ceil(i)
		else:
			i = floor(i)"""
		min_te = [100,100,100]
		###########################	
		self.te[2] += cur_error[2]
		if self.te[2] > min_te[2]:
			self.te[2] = min_te[2]
		if self.te[2] < -min_te[2]:
			self.te[2] = -min_te[2]
		###########################		
		self.te[1] += cur_error[1]
		if self.te[1] > min_te[1]:
			self.te[1] = min_te[1]
		if self.te[1] < -min_te[1]:
			self.te[1] = -min_te[1]
		###########################
		self.te[0] += cur_error[0]
		if self.te[0] > min_te[0]:
			self.te[0] = min_te[0]
		if self.te[0] < -min_te[0]:
			self.te[0] = -min_te[0]
		###########################
		#self.outThrottle = throttle_error[0]+throttle_error[1]+throttle_error[2]
		#self.outPitch = pitch_error[0]+pitch_error[1]+pitch_error[2]
		#self.outRoll = roll_error[0]+roll_error[1]+roll_error[2]
		#print(throttle_error[0])
		Throttle = 1500 - (throttle_error[0]+throttle_error[1]+throttle_error[2])
		Pitch = 1500 - (pitch_error[0]+pitch_error[1]+pitch_error[2])
		Roll = 1500 + (roll_error[0]+roll_error[1]+roll_error[2])
		
		print('%.2f'%(1500-Throttle),'%.2f'%self.drone_position[2])
		############
		print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
		print('the current KPs are',self.Kp)
		print('the current KDs are',self.Kd)
		print('the current Kis are',self.Ki)
		#print('smiran snageets')
		print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
		##########
		#ll = 1050
		#ul = 1950
		upper_limit=[1950,1950,1950]
		lower_limit=[1050,1050,1050]
		self.prev_error = cur_error
		
		if Throttle < lower_limit[2]:
			Throttle = lower_limit[2]
		if Throttle > upper_limit[2]:	
			Throttle = upper_limit[2]
		self.cmd.rcThrottle = Throttle
		
		if Pitch < lower_limit[1]:
			Pitch = lower_limit[1]
		if Pitch > upper_limit[1]:	
			Pitch = upper_limit[1]
		self.cmd.rcPitch = Pitch
		
		if Roll < lower_limit[0]:
			Roll = lower_limit[0]
		if Roll > upper_limit[0]:	
			Roll = upper_limit[0]
		self.cmd.rcRoll = Roll
		#print(Throttle)
	#------------------------------------------------------------------------------------------------------------------------
		self.pub1.publish(cur_error[0])
		self.pub2.publish(cur_error[1])
		self.pub3.publish(cur_error[2])
		
		
		self.command_pub.publish(self.cmd)
		


if __name__ == '__main__':

	e_drone = Edrone()
	r = rospy.Rate(1/e_drone.sample_time) #specify rate in Hz based upon your desired PID sampling time, i.e. if desired sample time is 33ms specify rate as 30Hz
	while not rospy.is_shutdown():
		e_drone.pid()
		r.sleep()
