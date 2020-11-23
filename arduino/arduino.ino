/*
Arduino code for controlling servos with Blender's animation system. 
 (or anything else that can send serial commands really)

A Python script in blender generates serial commands and this reads them and
 sets the servos (using the stock Arduino servo lib).

* servo_pins defines the IO pin each servo connects to.
* the GLOBAL(_MIN/_MAX) define the absolute bounds your servos will be 
     to travel, regardless of what commands are given. (Cheapie servos
     sometimes don't like to go the full 0-180). TODO: these are currently
     ignored by the recommended absolute move commands
* SERVO_COUNT is self explanitory. Setting it to 12 (the max) regardless
     shouldn't hurt, as long as it matches the size of servo_pins.
* speed adjustments made using the 'f' command are applied on the next 'a'
     command, not instantly.

serial commands are:
MOVE: <servo1_angle> a <servo2_angle> a ... <servoX_angle> a
SET SPEED: <servo1_deg_s> f <servo2_deg_s> f ... <servoX_deg_s> f

OLD COMMAND FORMAT, may be removed:
    SPEED1 DIR1 SPEED2 DIR2...
    DIR1 = 0 for FORWARD
         = 1 for REVERSE
    set SPEED to -1 to stop servo
*/

#if defined(ESP_H)
#include <ESP32_Servo.h>
#else
#include <Servo.h>
#endif

#define SERVO_COUNT 1
#define BUFFER_SZ 50
#define GLOBAL_MIN 5
#define GLOBAL_MAX 175
#define GLOBAL_SPEED 30
#define DEBUG true
#define DEBUG2 true


Servo servo[SERVO_COUNT];
byte servo_pins[SERVO_COUNT] = {32};
byte servo_start[SERVO_COUNT];
byte servo_end[SERVO_COUNT];

unsigned int servo_speed[SERVO_COUNT];

unsigned long cycle_dur[SERVO_COUNT];
unsigned long cycle_start[SERVO_COUNT];
bool moving[SERVO_COUNT];

int b_count;
char buff[BUFFER_SZ];
char command[BUFFER_SZ];


void setup() {
    // put your setup code here, to run once:
    attach_all_servos();
    Serial.setTimeout(10);
    Serial.begin(115200);
    servo[0].write(90);
}

void loop() {
    // put your main code here, to run repeatedly:
    serial_parse();
    update_servos();

    if (b_count > 0) {
#if DEBUG        
        Serial.print("received ");
        Serial.println(command);
#endif 
        set_servos_from_serial();
    }
}


void serial_parse() { 
    b_count = 1; 
    b_count = Serial.readBytesUntil('\n', buff, BUFFER_SZ);

    if (b_count > 0) strcpy(command, buff);

    memset(buff, 0, sizeof(buff));
    Serial.flush();
}

void set_servos_from_serial() {
    char* pch = strtok(command, " ");
    byte counter = 0;
    String sv_speed;
    String sv_dir;
    
    while (pch != NULL) {
        //TODO: converting to String ideal?
        sv_speed = String(pch);
        pch = strtok(NULL, " ");
        
        if (pch == NULL) {
            Serial.println("invalid command format");
            break;
        }
        
        sv_dir = String(pch);
       
        if (sv_dir == "f") // set feed rate command
            servo_speed[counter] = sv_speed.toInt();
        else               // move commands
            set_servo(counter, sv_speed.toInt(), (sv_dir == "1"), (sv_dir == "a"));
        
        counter++;
        pch = strtok(NULL, " ");

        if (counter > SERVO_COUNT) {
            counter = 0;
            break;
        }
    }   
}

// find how long it takes to travel X degrees
long deg_sec_to_time(int deg_sec, int cur_pos, bool dir) {
    if (dir) return ((180 - (-(float)cur_pos + 180)) / (float)deg_sec) * 1000;
    else return ((180 - (float)cur_pos) / (float)deg_sec) * 1000; 
}

// takes a desired servo move and sets all the 
// vars as necessary - call this to move a servo
void set_servo(byte index, int deg_s, bool dir, bool absolute) {
    servo_start[index] = servo[index].read();
    
    if (absolute) 
        servo_end[index] = deg_s;
    else
        servo_end[index] = dir ? GLOBAL_MIN : GLOBAL_MAX;
    
    switch (deg_s) {
    case -1:
        moving[index] = false;
#if DEBUG2
        Serial.println("stopped moving servo");
#endif
    case 0:
        return;
        break;
    }
    
#if DEBUG
    Serial.print("deg_s: ");
    Serial.println(deg_s);
#endif
    // record start time and set velocity    
    cycle_start[index] = millis();
    
    if (absolute) {
        int new_pos = abs(deg_s - servo[index].read());
        
        if (new_pos != 0 && servo_speed[index] != 0) {
            cycle_dur[index] = millis() + 
                               ((new_pos * 1000) / servo_speed[index]);
            moving[index] = true;
#if DEBUG
            Serial.print("servo move takes ");
            Serial.print((new_pos * 1000) / servo_speed[index]);
            Serial.println(" ms");
#endif
        }
        else {
           moving[index] = false;
        }
    }
    else {
        cycle_dur[index] = cycle_start[index] + 
            deg_sec_to_time(deg_s, servo[index].read(), dir);
        
        moving[index] = true;
#if DEBUG
        Serial.print("servo velocity is ");
        Serial.println(deg_sec_to_time(deg_s, servo[index].read(), dir));
#endif
    }
}

// interfaces to servo library
void update_servos() {
    for (int i = 0; i < SERVO_COUNT; i++) {
        if (cycle_dur[i] != 0) {
            unsigned long time_into_cycle = millis() % cycle_dur[i];
            
            if (moving[i]) {
#if DEBUG
                Serial.println("cycle-timer, start, end:");
                Serial.println(time_into_cycle);
                Serial.println(cycle_start[i]);
                Serial.println(cycle_dur[i]);
                Serial.println(servo_start[i]);
                Serial.println(servo_end[i]);
#endif            
                servo[i].write(map(time_into_cycle, cycle_start[i], 
                               cycle_dur[i] - 1, servo_start[i], servo_end[i]));
#if DEBUG2            
                Serial.println(time_into_cycle);
#endif
            }

            if (time_into_cycle >= cycle_dur[i] - 10) {
                moving[i] = false;
                servo_start[i] = servo[i].read();
            }
        }
    }
}

void attach_all_servos() {
    for (int i = 0; i < SERVO_COUNT; i++) {
        servo[i].attach(servo_pins[i]);
        servo_start[i] = 89;
        servo_end[i] = 90;
        cycle_dur[i] = 100;
        cycle_start[i] = 0;
        moving[i] = true;
    }
}
