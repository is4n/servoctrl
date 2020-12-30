# servoctrl

*note: code under active deving, parts of this doc might be baaad*

Arduino code for controlling servos with Blender's animation system.
A Python script in blender generates serial commands and an Arduino program reads them and sets the servos (using the stock Arduino servo lib).

# Setup

in the Arduino sketch:
* servo_pins defines the IO pin each servo connects to.
* the GLOBAL(_MIN/_MAX) define the absolute bounds your servos will be 
     to travel, regardless of what commands are given. (Cheap servos
     sometimes don't like to go the full 0-180). TODO: these are currently
     ignored by the recommended absolute move commands
* SERVO_COUNT is self explanitory. make sure it matches the size of servo_pins.

In Blender:
* Install the addon using the "Install from file" function in prefs. You should get a "Servo Control" panel (press T >> open "Misc" tab) 
* Create an Armature object with Bones that correlate to your device's servomotors
* Make sure those bones are set to use Euler rotation (not quats)
* Enter the name of your Armature rig into the panel's Source Armature text box
* set Channels to the number of motors you have in your dervice (must match Arduino config), click Write
* use the Edit slider to select servo 1, set its Source (bone name) and Axis (0:X, 1:Y, 2:Z), then click Write
* slide Edit to 2, press Read, repeat for each servo
* Enter your Port and PortRate, hit Connect, then check Sync. Enjoy posing and animating your device in real time!
* Be sure to Disconnect before editing the model (esp. before using Undo)
* Don't use the Play Animation button, instead check Sync and play the animation in Blender normally

# Current serial commands format:

If you want to drive the Arduino side without Blender:
* MOVE: <servo1_angle> <servo1_deg_s> ...

# Old serial command format:

SPEED1 DIR1 SPEED2 DIR2...

for DIR:
* = -1 for halt
* = 0 for FORWARD
* = 1 for REVERSE
* = a for ABSOLUTE (Speed is pre-defined, Servo will travel to SPEED degress and stop)
* speed adjustments made using the 'f' command are applied on the next 'a'
     command, not instantly. (this is no longer used, position is to be sent every command by serial)

Note that this format has been replaced with the new format above.

# Bugs

* The update speed of the servos is too slow. (Can't get it above ~7 Hz)
* Using Undo does not play well with the stateful operation of Servo Control. It seems that if you disconnect before using Undo, you can still reconnect to the robot.
* The UI is awful and will break if misused.
