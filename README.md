# servoctrl

Arduino code for controlling servos with Blender's animation system (or anything that can spit out serial commands really).
A Python script in blender generates serial commands 
and this reads them and sets the servos (using the stock Arduino servo lib).

The Arduino code is more-or-less usable and is easily adjustable for use in a variety of projects:
* the GLOBAL(_MIN/_MAX) define the absolute bounds your servos will be 
     to travel, regardless of what commands are given. (Cheapie servos
     sometimes don't like to go the full 0-180)
* Global Speed is only used for "absolute" movements (which are untested!)
* Servo count is self explanitory. Setting it to 12 (the max) regardless
     shouldn't hurt. Just make sure it matches the size of servo_pins.
* servo_pins defines the io pin each servo connects to - make sure this 
     lines up with what you set up in Blender to get good results.
     
The blender side isn't so polished yet. As of now it's hard-coded around a setup of mine, although you should be able to get it working with your own custom rig - Paste the contents of sv_ctrl_blender.py into your blendfile. Set 'Armature' in line 9 to the name of the rig you want to pull from. Configure the servo definition lines (starting at line 15) to link your rig to the servos:
* Just look at the code, there's comments to help explain it a little
* The "home position" is a set number of degrees added to the rotation value of the chosen bone so you can line up your servos with the rig - in my case, the default position of the armature is 0 degrees, and the position my servo matches is that is 90 degrees (center) so I set it to 90
* Axis of rotation - 0 is X, 1 is Y, 3 is Z
If you scroll down around line 87 you can enable debug mode. This will disable the serial output, instead printing it (and more useful stuff) to blender's console.

# serial command format:
SPEED1 DIR1 SPEED2 DIR2...                

for DIR:
* = -1 for halt
* = 0 for FORWARD
* = 1 for REVERSE
* = a for ABSOLUTE (Speed is pre-defined, Servo will travel to SPEED degress and stop)
