# servoctrl
Note: If for some reason you're reading this and not me, there's probably
better code out there for doing this. Don't bother with this project!

Arduino code for controlling servos with Blender's animation system.
A Python script in blender generates serial commands 
and this reads them and sets the servos (using the stock Arduino servo lib).

This code is easily adjustable for use in a variety of projects:
* the GLOBAL(_MIN/_MAX) define the absolute bounds your servos will be 
     to travel, regardless of what commands are given. (Cheapie servos
     sometimes don't like to go the full 0-180)
* Global Speed is only used for "absolute" movements (which are untested!)
* Servo count is self explanitory. Setting it to 12 (the max) regardless
     shouldn't hurt. Just make sure it matches the size of servo_pins.
* servo_pins defines the io pin each servo connects to - make sure this 
     lines up with what you set up in Blender to get good results.

# serial command format:
SPEED1 DIR1 SPEED2 DIR2...

for DIR1:
* = -1 for halt
* = 0 for FORWARD
* = 1 for REVERSE
* = a for ABSOLUTE (Speed is pre-defined, Servo will travel to SPEED degress and stop)
