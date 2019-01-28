import bpy
import serial
import time
from math import degrees

class Servos:
    def build(mode): 
        if (mode == "man"):
            Servos.arm_bones = bpy.context.scene.objects['Armature'].pose.bones
            #                                             ^^^^ Set this to your source rig 
            Servos.servo_count = 6 
            #                    ^^ Set to how many servos you plan to run
            Servos.servo_list = []
            # Define your servos here (copy or delete these lines as you need)        Reverse
            Servos.servo_list.append(Servo(Servos.arm_bones['neck'].rotation_euler[2], False, 90))
            #                                   name of bone^^^^   Axis of rotation^          ^^ Home position
            Servos.servo_list.append(Servo(Servos.arm_bones['neck'].rotation_euler[0], True, 90))
            #...for every servo
            Servos.servo_list.append(Servo(Servos.arm_bones['eye_top'].rotation_euler[0], False, 90))
            Servos.servo_list.append(Servo(Servos.arm_bones['eye'].rotation_euler[2], False, 90))
            Servos.servo_list.append(Servo(Servos.arm_bones['eye'].rotation_euler[0], False, 90))
            Servos.servo_list.append(Servo(Servos.arm_bones['eye_bottom'].rotation_euler[0], False, 90))
						
        elif (mode == "auto"): raise Exception("not implemented yet!")
        else: raise Exception("MODE must = \"auto\", \"man\", or a valid config path")

class Servo:
    def __init__(self, src, rev, hm):
        self.source = src
        self.reversed = rev
        self.home = hm
        self.position = self.home
    

class RobotPanel(bpy.types.Panel):
    bl_label = "Robot"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        arm = context.scene.objects['Armature']
        bone = arm.pose.bones['eye']
        mat = bone.matrix.to_euler()
        
        self.layout.operator("robot.animate", text='Play Animation')
        #self.layout.
        
        col = self.layout.column(align = True)
        
        col.label(text = bpy.context.scene.robot_message)
        col.prop(context.scene, "robot_port")
        col.prop(context.scene, "robot_port_rate")
        col.operator("robot.connect", text='(Dis)Connect')
        
        row = self.layout.row()
        
        row.label(text='X: {:.3}'.format(degrees(mat.x)))
        row.label(text='Y: {:.3}'.format(degrees(mat.y)))
        row.label(text='Z: {:.3}'.format(degrees(mat.z)))

    def register():
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
    debug = False
    
    def print_connected(): 
        bpy.context.scene.robot_message = "Connected"
        bpy.context.scene.robot_connected = 1

    def print_disconnected(fail):
        if (fail): bpy.context.scene.robot_message = "Connect Failure"
        else: bpy.context.scene.robot_message = "Disconnected"
        bpy.context.scene.robot_connected = 0
    

class PlaysAnimation:
    # stops servo movement
    @classmethod
    def cancel(self): 
        cancel_str = ''
        for sv in range(0, Servos.servo_count):
            cancel_str += '-1 0 '
        if (StoresStuff.debug): print((cancel_str + '\n'))
        else: StoresStuff.ser.write((cancel_str + '\n').encode())
    
    # gets per-servo data for given frame, formats and commits to arduino   
    @classmethod
    def update_frame(self, frame, fps):      
        send_str = ''
        new_servo_pos = []
        
        for sv in range(0, Servos.servo_count):
            curr_servo = Servos.servo_list[sv]
            print ('test ' + str(degrees(curr_servo.source)))
            new_servo_pos.append(curr_servo.home + degrees(curr_servo.source))
            send_str += self.gen_servo_args(
                curr_servo.position, 
                new_servo_pos[sv], 
                curr_servo.reversed, 
                fps) + ' '
            curr_servo.position = new_servo_pos[sv]
        
        if (StoresStuff.debug): print (send_str + '\n')
        else: StoresStuff.ser.write((send_str + '\n').encode())
    
    # plays entire animation on arduino 
    # note this holds up the thread (time.sleep()) so the UI goes unresponsive
    @classmethod
    def play(self, fps):
        for frame in range(StoresStuff.start, StoresStuff.end):
            bpy.context.scene.frame_set(frame)
          
            if (not bpy.context.scene.robot_connected and not StoresStuff.debug):
                bpy.context.scene.robot_message = "No Connection!"
                return
              
            print ('frame ' + str(frame) + '\n')
            Servos.build("man") #TODO: find a better place for this
              
            if (frame == StoresStuff.end - 1):
                self.cancel()
                return
              
            self.update_frame(frame, StoresStuff.fps)
            time.sleep(1 / StoresStuff.fps)
            
    # converts a servo position for current and last frame into velocity/direction string
    @classmethod
    def gen_servo_args(self, start_pos, end_pos, reverse, fps): #todo: add revese
        print("start_pos: " + str(start_pos))
        print("end_pos: " + str(end_pos))
        deg_sec = (end_pos - start_pos) * fps
        print("deg_sec" + str(deg_sec))
        if (deg_sec == 0): return '-1 0'
        if ((deg_sec < 0 and not reverse)): 
            return str(int(deg_sec * -1)) + ' 1'
        elif ((deg_sec > 0 and reverse)):
            return str(int(deg_sec)) + ' 1'
        elif ((deg_sec < 0 and reverse)):
            return str(int(deg_sec * -1)) + ' 0'
        else: return str(int(deg_sec)) + ' 0'				


class ConnectButton(bpy.types.Operator):
    bl_idname = "robot.connect"
    bl_label = "Connect"
    
    def execute(self, context):
        if (bpy.context.scene.robot_connected):
            try: 
                StoresStuff.print_disconnected(False)
                StoresStuff.ser.close()

                return{'FINISHED'}
            except: 
                bpy.context.scene.robot_message = "Disconnect Failure"

                return{'FINISHED'}
        try: 
            StoresStuff.ser = serial.Serial(bpy.context.scene.robot_port, 
                bpy.context.scene.robot_port_rate)
            StoresStuff.print_connected()                   
            
            return{'FINISHED'}
        except: 
            StoresStuff.print_disconnected(True)
            
            return{'FINISHED'}  
     

class PlayAnimButton(bpy.types.Operator):
    bl_idname = "robot.animate"
    bl_label = "Play"  

    def execute(self, context): 
        StoresStuff.fps = bpy.context.scene.render.fps
        StoresStuff.start = bpy.context.scene.frame_start
        StoresStuff.end = bpy.context.scene.frame_end
        PlaysAnimation.play(StoresStuff.fps)
        return{'FINISHED'}
        

bpy.utils.register_class(RobotPanel)
bpy.utils.register_class(ConnectButton)
bpy.utils.register_class(PlayAnimButton)