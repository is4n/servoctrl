// Arduino code for controlling servos with Blender's animation system.
// A Python script in blender generates serial commands 
// and this reads them and sets the servos (using the stock Arduino servo lib).

// This code is easily adjustable for use in a variety of projects:
// * the GLOBAL(_MIN/_MAX) define the absolute bounds your servos will be 
//      to travel, regardless of what commands are given. (Cheapie servos
//      sometimes don't like to go the full 0-180)
// * Global Speed is only used for "absolute" movements (which are untested!)
// * Servo count is self explanitory. Setting it to 12 (the max) regardless
//      shouldn't hurt. Just make sure it matches the size of servo_pins.
// * servo_pins defines the io pin each servo connects to - make sure this 
//      lines up with what you set up in Blender to get good results.


// serial command format:
// SPEED1 DIR1 SPEED2 DIR2...
// DIR1 = -1 for halt
//      = 0 for FORWARD
//      = 1 for REVERSE
//      = a for ABSOLUTE:
//         Speed is pre-defined
//         Servo will travel to SPEED degress and stop

#include <Servo.h>

#define SERVO_COUNT 11
#define BUFFER_SZ 50
#define GLOBAL_MIN 5
#define GLOBAL_MAX 175
#define GLOBAL_SPEED 30
#define DEMO false
#define DEBUG false
#define DEBUG2 false

Servo servo[SERVO_COUNT];
byte servo_pins[SERVO_COUNT] = {2, 3, 4, 6, 7, 8, 9, 10, 5, 12, 13};
byte servo_start[SERVO_COUNT];
byte servo_end[SERVO_COUNT];

unsigned long cycle_dur[SERVO_COUNT];
unsigned long cycle_start[SERVO_COUNT];

bool moving[SERVO_COUNT];

bool serial_active = false;
#if DEMO
byte anim_fac = 0;
byte anim_time = 0;
#endif

int b_count;
char buff[BUFFER_SZ];
char command[BUFFER_SZ];

void setup() {
    // put your setup code here, to run once:
    attach_all_servos();
    Serial.setTimeout(10);
    Serial.begin(38400);
    servo[0].write(90);
}

void loop() {
    // put your main code here, to run repeatedly:
    serial_parse();
    update_servos();
#if DEMO
    update_demo();
#endif

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

#if DEMO
void update_demo() {    
    if (!serial_active) {   
        byte anim_servo = anim_time;
        while (anim_servo >= SERVO_COUNT) {
            anim_servo -= SERVO_COUNT;
#if DEBUG2            
            Serial.println("test");
            Serial.println(anim_servo);
#endif            
        }
        Serial.println(anim_fac);
        if (millis() > 10000 + (anim_time * 4000) && anim_fac == 0) {
            set_servo(0 + anim_servo, 30, 0, false);
            set_servo(1 + anim_servo, 30, 0, false);
            anim_fac++;
            Serial.println("1");
        }
        else if (millis() > 11000 + (anim_time * 4000) && anim_fac == 1) {
            set_servo(0 + anim_servo, 30, 1, false);
            set_servo(1 + anim_servo, 30, 1, false);
            anim_fac++;
            Serial.println("2");
        }
        else if (millis() > 12000 + (anim_time * 4000) && anim_fac == 2) {
            set_servo(0 + anim_servo, -1, 0, false);
            set_servo(1 + anim_servo, -1, 0, false);
            Serial.println("3");
#if DEBUG2
            Serial.println("demo servo: ");
            Serial.println(anim_servo); 
#endif      
            anim_fac = 0;
            if (anim_time < 5) {            
            
            anim_time++;
            }
        }
    }
}
#endif

void set_servos_from_serial() {
    char* pch = strtok(command, " ");
    byte counter = 0;
    String sv_speed;
    String sv_dir;

    serial_active = true;
    
    while (pch != NULL) {
        sv_speed = String(pch);
        pch = strtok(NULL, " ");
        sv_dir = String(pch);

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
    if (absolute) servo_end[index] = deg_s;
    else servo_end[index] = (GLOBAL_MIN * dir) + (GLOBAL_MAX * !dir); 
    
    if (deg_s == -1) {
        moving[index] = false;
#if DEBUG2
        Serial.println("stopped moving servo");
#endif
    }
    if (deg_s > -2 && deg_s < 1) return;
    
#if DEBUG
    Serial.print("deg_s: ");
    Serial.println(deg_s);
#endif
    cycle_start[index] = millis();
    cycle_dur[index] = cycle_start[index] + deg_sec_to_time(deg_s, servo[index].read(), dir);
    moving[index] = true;
#if DEBUG
    Serial.print("servo velocity is ");
    Serial.println(deg_sec_to_time(deg_s, servo[index].read(), dir));
#endif
}

// interfaces to servo library
void update_servos() {
    for (int i = 0; i < SERVO_COUNT; i++) {
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
            servo[i].write(map(time_into_cycle, 
                cycle_start[i], cycle_dur[i] - 1, servo_start[i], servo_end[i]));
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
