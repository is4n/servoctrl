import bpy
import serial
import time
import os
from math import degrees

bl_info = {
    "name": "ServoControl",
    "author": "<author>",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "category": "Animation",
}

class Servos:
    servo_list = []
    def build(mode): 
        if (mode == "man"):
            Servos.arm_bones = bpy.context.scene.objects['Armature'].pose.bones
            Servos.rig = 'Armature'
            
            Servos.servo_count = 6 
            #                    ^^ Set to how many servos you plan to run
            # Define your servos here (copy or delete these lines as you need)        Reverse
            Servos.servo_list.append(Servo('neck', 2, False, 90))
            #                                   name of bone^^^^   Axis of rotation^          ^^ Home position
            Servos.servo_list.append(Servo('neck', 0, True, 90))
            #...for every servo
            Servos.servo_list.append(Servo('eye_top', 0, False, 90))
            Servos.servo_list.append(Servo('eye', 2, False, 90))
            Servos.servo_list.append(Servo('eye', 0, False, 90))
            Servos.servo_list.append(Servo('eye_bottom', 0, False, 90))
						
        else: 
            # attempt to read external file first
            if (os.path.exists(mode)): 
                mode_file = open(mode, "r")
                bpy.context.scene.robot_servo_data = mode_file.read()
                mode_file.close()
            
            # set global info, chop off first armature line
            servo_config_lines = bpy.context.scene.robot_servo_data.split("\n")
            Servos.rig = servo_config_lines[0]
            Servos.arm_bones = bpy.context.scene.objects[servo_config_lines[0]].pose.bones
            servo_config_lines = servo_config_lines[1:-1]
            Servos.servo_count = len(servo_config_lines)
            
            if (StoresStuff.debug): 
                print("DEBUG: Servo build: config file")
                print(servo_config_lines)
            
            # add servos to the class
            for line in servo_config_lines: 
                servo_props = line.split(" ")
                Servos.servo_list.append(Servo( \
                    servo_props[0], \
                    int(servo_props[1]), \
                    (servo_props[2] == "True"), \
                    int(servo_props[3])))
    
    def update():
        for servo in Servos.servo_list:
            servo.source = \
                Servos.arm_bones[servo.source_bone].rotation_euler[servo.source_axis]
    
    def export(filepath):
        export_file = bpy.context.scene.robot_global_source + "\n"
        
        for servo in Servos.servo_list:
            export_file += \
                str(servo.source_bone) + " " + \
                str(servo.source_axis) + " " + \
                str(servo.reversed) + " " + \
                str(servo.home) + "\n"           
                
            if (StoresStuff.debug): print("DEBUG: export data\n" + export_file) 
            if (filepath == ""): bpy.context.scene.robot_servo_data = export_file
            elif (os.path.exists(filepath)): 
                filewriter = open(filepath, "w")
                filewriter.write(export_file)
                filewriter.close()
            else: print("EXPORT SERVOS: invalid string input")
        

class ServoInterface:
    def set_rig():
        Servos.arm_bones = \
            bpy.context.scene.objects[bpy.context.scene.robot_global_source].pose.bones
    # makes sure Servos.servo_count and the acutal servo list match up  
    def fit_servos():
        while (Servos.servo_count != len(Servos.servo_list)):
            if (Servos.servo_count > len(Servos.servo_list)):
                Servos.servo_list.append(Servo('', 0, False, 90))
                if (StoresStuff.debug): print("DEBUG: fit: added servos\n")
            if (Servos.servo_count < len(Servos.servo_list)):
                del Servos.servo_list[-1]
                if (StoresStuff.debug): print("DEBUG: fit: removed servos\n")
    def get_servo_data(channel):
        try:
            servo = Servos.servo_list[channel]
            return [
                servo.source_bone, 
                str(servo.home), 
                str(servo.reversed), 
                str(servo.source_axis)]
        except IndexError:
            return ['']
    
    def set_servo_source(channel, src): 
        Servos.servo_list[channel].source_bone = src
    
    def set_servo_home(channel, home_pos):
        Servos.servo_list[channel].home = home_pos
    
    def set_servo_reverse(channel, reverse):
        Servos.servo_list[channel].reversed = reverse
        
    def set_servo_axis(channel, ax):
        Servos.servo_list[channel].source_axis = ax
    
    
class Servo:
    def __init__(self, src, src_xyz, rev, hm):
        #self.source = src
        self.source_bone = src
        self.source_axis = src_xyz
        self.reversed = rev
        self.home = hm
        self.position = self.home
    

#Draws GUI, defines Blender Props
class RobotPanel(bpy.types.Panel):
    bl_label = "Servo Control"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        self.layout.operator("robot.animate", text='Play Animation')
        
        col = self.layout.column(align = True)        
        col.prop(context.scene, "robot_debug")
        col.prop(context.scene, "robot_sync")
        col.label(text = bpy.context.scene.robot_message)
        col.prop(context.scene, "robot_port")
        col.prop(context.scene, "robot_port_rate")
        col.operator("robot.connect", text='(Dis)Connect')
        
        row = self.layout.row()        
        
        col2 = self.layout.column(align = True)        
        col2.label(text = "Source Armature")
        col2.prop(context.scene, "robot_global_source")
        col2.label(text = "Channel Config")
        col2.prop(context.scene, "robot_channel_count")
        col2.prop(context.scene, "robot_channel")
        
        row2 = self.layout.row()
        row2.operator("robot.read_servo", text = "Read")
        row2.operator("robot.write_servo", text = "Write")
        
        col3 = self.layout.column(align = True)
        col3.prop(context.scene, "robot_channel_source")
        col3.prop(context.scene, "robot_channel_home")
        col3.prop(context.scene, "robot_channel_axis")
        col3.prop(context.scene, "robot_channel_reverse")

    def register():
        bpy.types.Scene.robot_servo_data = bpy.props.StringProperty()
        bpy.types.Scene.robot_debug = bpy.props.BoolProperty \
            (
                name = "Debug",
                description = "dump to terminal instead of sending serial data",
                default = False
            )
        bpy.types.Scene.robot_sync = bpy.props.BoolProperty \
            (
                name = "Sync",
                description = "Follow rig in realtime",
                default = False
            )
        bpy.types.Scene.robot_channel = bpy.props.IntProperty \
            ( 
                name = "Edit",
                description = "set the servo channel you want to edit here",
                default = 1
            )
        bpy.types.Scene.robot_channel_count = bpy.props.IntProperty \
            ( 
                name = "Channels",
                description = "total amount of servo channels",
                default = 1
            )     
        bpy.types.Scene.robot_channel_axis = bpy.props.IntProperty \
            ( 
                name = "Axis",
                description = "axis of rotation (0-X, 1-Y, 2-Z)",
                default = 0
            )       
        bpy.types.Scene.robot_channel_reverse = bpy.props.BoolProperty \
            (
                name = "Reversed",
                description = "check if servo moves backwards of what's expected",
                default = False
            )
        bpy.types.Scene.robot_channel_home = bpy.props.IntProperty \
            (
                name = "HomePos",
                description = "Degrees added to frame bone position",
                default = 90
            )
        bpy.types.Scene.robot_channel_source = bpy.props.StringProperty \
            (
                name = "SourceBone",
                default = "bone"
            )
        bpy.types.Scene.robot_global_source = bpy.props.StringProperty \
            (
                name = "Source",
                default = "Armature"
            )
        bpy.types.Scene.robot_connected = bpy.props.BoolProperty \
            (
                name = "ConnectionStatus",
                default = 0
            )
        bpy.types.Scene.robot_message = bpy.props.StringProperty \
            (
                name = "Message",
                default = ""
            )
        bpy.types.Scene.robot_port_rate = bpy.props.IntProperty \
            (
                name = "PortRate",
                description = "Set the Serial port Speed (baudrate) here",
                default = 38400
            )
        bpy.types.Scene.robot_port = bpy.props.StringProperty \
            (
               name = "Port",
               description = "Set the Serial Port to access the robot here",
               default = "/dev/ttyUSB0"
            )
            

class StoresStuff:
    debug = True
    timer_const = 14 # frame rate to robot
    timer_active = False
        
    def print_connected(): 
        bpy.context.scene.robot_message = "Connected"
        bpy.context.scene.robot_connected = 1

    def print_disconnected(fail):
        if (fail): bpy.context.scene.robot_message = "Connect Failure"
        else: bpy.context.scene.robot_message = "Disconnected"
        bpy.context.scene.robot_connected = 0
    

class PlaysAnimation(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    # pulled from Blender example scripts
    bl_idname = "wm.robot_data_sender"
    bl_label = "Robot Data Sender"

    _timer = None
    _timerStart = 0
    _timerConst = 1 / StoresStuff.timer_const

    def modal(self, context, event):
        ##if event.type in {'RIGHTMOUSE', 'ESC'}:
        ##    self.cancel(context)
        ##    return {'CANCELLED'}
        #print("loop pt1")
        # robot sync is on
        elapsed = time.monotonic() - self._timerStart
        
        if (event.type == 'TIMER'):
            # shut down event if connection is severed
            if (bpy.context.scene.robot_connected == 0) and (not StoresStuff.debug):
                print("timer killing itself")
                self.cancel(context)
                StoresStuff.timer_active = False
                return {'CANCELLED'}
            
            # if sync is checked...
            if ((bpy.context.scene.robot_sync) and (elapsed > self._timerConst)):
                print(StoresStuff.debug)
                print("timer elapsed") 
                self._timerStart = time.monotonic()
                
                # check the connection
                if (not bpy.context.scene.robot_connected and (not StoresStuff.debug)):
                    print("no connection!")
                
                else: # connection OK
                    self.update_frame(bpy.context.scene.frame_current,StoresStuff.timer_const)

            #print(f"timer has gone {elapsed} so far")
        
        #TODO: unregister event on sync uncheck
        #if ((event.type == 'TIMER') and (not bpy.context.scene.robot_sync)):
        #    self.cancel(context)
        #    return {'CANCELLED'}
          
        return {'PASS_THROUGH'}

    def execute(self, context):
        self._timerStart = time.monotonic()
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        
    #TODO: stops servo movement
    #@classmethod
    #def cancel(self): 
    #    cancel_str = ''
    #    for sv in range(0, Servos.servo_count):
    #        cancel_str += '-1 0 '
    #    if (StoresStuff.debug): print((cancel_str + '\n'))
    #    else: StoresStuff.ser.write((cancel_str + '\n').encode())
    
    # gets per-servo data for given frame, formats and commits to arduino   
    @classmethod
    def update_frame(self, frame, fps):      
        op_str = ''
        new_servo_pos = []
        Servos.update()
        
        for sv in range(0, Servos.servo_count):
            curr_servo = Servos.servo_list[sv]
            
            if (curr_servo.reversed):
                new_servo_pos.append(curr_servo.home - degrees(curr_servo.source))
            else:
                new_servo_pos.append(curr_servo.home + degrees(curr_servo.source))
            
            position, velocity = self.gen_servo_args(
                curr_servo.position, 
                new_servo_pos[sv], 
                curr_servo.reversed, 
                fps)
                
            curr_servo.position = new_servo_pos[sv]
            
            op_str += position + ' ' + velocity + ' '
        
        if (StoresStuff.debug and not bpy.context.scene.robot_connected): 
            print("robot output")
            print(op_str[:-1])
        else: 
            #StoresStuff.ser.write((velocity_str + '\n').encode("UTF-8"))
            StoresStuff.ser.write((op_str[:-1] + '\n').encode("UTF-8"))
            
            if (StoresStuff.debug):
                print(StoresStuff.ser.read(300))
            else:
                # forcing serial to time out fixes intermittant communications
                # for some reason
                StoresStuff.ser.read(300) 
            #time.sleep(0.5)
    
    # plays entire animation on arduino 
    # note this holds up the thread (time.sleep()) so the UI goes unresponsive
    @classmethod
    def play(self, fps):
        for frame in range(StoresStuff.start, StoresStuff.end):
            bpy.context.scene.frame_set(frame)
            
            if (not bpy.context.scene.robot_connected and (not StoresStuff.debug)):
                bpy.context.scene.robot_message = "No Connection!"
                return
              
            print ('frame ' + str(frame) + '\n')
            
              
            if (frame == StoresStuff.end - 1):
                #self.cancel()
                return
              
            self.update_frame(frame, StoresStuff.fps)
            time.sleep(1 / StoresStuff.fps)
            
    # converts a servo position for current and last frame into velocity/direction string
    @classmethod
    def gen_servo_args(self, start_pos, end_pos, reverse, fps, drift_corr_spd=50, drift_corr_thresh=10, vel_scale=0.8): #todo: add revese
        deg_sec = (end_pos - start_pos) * fps
        
        if (deg_sec > drift_corr_spd):
            deg_sec *= vel_scale
        if (abs(deg_sec) < drift_corr_thresh):
            deg_sec = drift_corr_spd
        
        retstrs = [str(int(end_pos)), str(abs(int(deg_sec)))]
        
        #print("start_pos: " + str(start_pos))
        #print("end_pos: " + str(end_pos))
        #print("deg_sec" + str(deg_sec))
        
        return retstrs
        
        # code for old style commands
        if (deg_sec == 0): return '-1 0'
        if ((deg_sec < 0 and not reverse)): 
            return str(int(deg_sec * -1)) + ' 1'
        elif ((deg_sec > 0 and reverse)):
            return str(int(deg_sec)) + ' 1'
        elif ((deg_sec < 0 and reverse)):
            return str(int(deg_sec * -1)) + ' 0'
        else: return str(int(deg_sec)) + ' 0'

# Following classes are input handlers
class ConnectButton(bpy.types.Operator):
    bl_idname = "robot.connect"
    bl_label = "Connect"
    
    def execute(self, context):
        # update debug mode
        StoresStuff.debug = bpy.context.scene.robot_debug
        Servos.build("")
        
        if (bpy.context.scene.robot_connected):
            # disconnect
            try: 
                StoresStuff.print_disconnected(False)
                StoresStuff.ser.close()

                return{'FINISHED'}
            except: 
                bpy.context.scene.robot_message = "Disconnect Failure"

                return{'FINISHED'}
        
        try:
            # connect serial port
            StoresStuff.ser = serial.Serial(bpy.context.scene.robot_port, 
                bpy.context.scene.robot_port_rate, timeout=0.01)
            StoresStuff.print_connected()                   
        except: 
            StoresStuff.print_disconnected(True)
            # start timer anyways if debugging
            if (not StoresStuff.debug): 
                return{'FINISHED'}  
          
        # start the timer
        if (not StoresStuff.timer_active):
            print("timer NOT active, starting")
            bpy.ops.wm.robot_data_sender()
            StoresStuff.timer_active = True
        
        return {'FINISHED'}
     

class PlayAnimButton(bpy.types.Operator):
    bl_idname = "robot.animate"
    bl_label = "Play"  
    
    def execute(self, context): 
        Servos.build("") # in order to remember servo config after re-opening blender 
        #StoresStuff.debug = bpy.context.scene.robot_debug  # Moved to connection routine
        StoresStuff.fps = bpy.context.scene.render.fps
        StoresStuff.start = bpy.context.scene.frame_start
        StoresStuff.end = bpy.context.scene.frame_end
        PlaysAnimation.play(StoresStuff.fps)
        return{'FINISHED'}
        

class ReadServoButton(bpy.types.Operator):
    bl_idname = "robot.read_servo"
    bl_label = "Read Servo"
    
    def execute(self, context):
        # Builds servo data if it hasn't already been done
        try:
            bpy.context.scene.robot_channel_count = Servos.servo_count
        except AttributeError:
            Servos.build("")
            bpy.context.scene.robot_channel_count = Servos.servo_count
        
        sv_data = ServoInterface.get_servo_data(bpy.context.scene.robot_channel - 1)
        if (StoresStuff.debug): print ("DEBUG: Servo data read: " + str(sv_data) + "\n")
        bpy.context.scene.robot_channel_source = sv_data[0]
        bpy.context.scene.robot_channel_home = int(sv_data[1])
        bpy.context.scene.robot_channel_reverse = (sv_data[2] == "True")
        bpy.context.scene.robot_channel_axis = int(sv_data[3])
        
        return{'FINISHED'}
   
      
class WriteServoButton(bpy.types.Operator):
    bl_idname = "robot.write_servo"
    bl_label = "Write Servo"
    
    def execute(self, context):
        Servos.servo_count = bpy.context.scene.robot_channel_count 
        ServoInterface.fit_servos()
        ServoInterface.set_rig()
        
        ServoInterface.set_servo_source \
            (bpy.context.scene.robot_channel - 1, bpy.context.scene.robot_channel_source)
        ServoInterface.set_servo_home \
            (bpy.context.scene.robot_channel - 1, bpy.context.scene.robot_channel_home)
        ServoInterface.set_servo_reverse \
            (bpy.context.scene.robot_channel - 1, bpy.context.scene.robot_channel_reverse)
        ServoInterface.set_servo_axis \
            (bpy.context.scene.robot_channel - 1, bpy.context.scene.robot_channel_axis)
            
        Servos.export("");
             
        return{'FINISHED'}

classes = (
    ReadServoButton,
    WriteServoButton,
    RobotPanel,
    ConnectButton,
    PlayAnimButton,
    PlaysAnimation
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
if __name__ == "__main__":
    register()

# clean up any old test runs
#try:
#    bpy.context.window_manager
#bpy.ops.wm.robot_data_sender()
