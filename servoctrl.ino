#include <VarSpeedServo.h>

#define SERVO_COUNT 6
#define BUFFER_SZ 50
#define GLOBAL_MIN 5
#define GLOBAL_MAX 175
#define GLOBAL_SPEED 30
#define DEBUG true

VarSpeedServo servo[SERVO_COUNT];
byte servo_pins[SERVO_COUNT] = {2, 3, 4, 6, 7, 8};
byte servo_home[SERVO_COUNT];
int b_count;

char buff[BUFFER_SZ];
char command[BUFFER_SZ];

void setup() {
    // put your setup code here, to run once:
    attach_all_servos();
    Serial.begin(9600);
    servo[0].write(90);
}

void loop() {
    // put your main code here, to run repeatedly:
    serial_parse();

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
        sv_speed = String(pch);
        pch = strtok(NULL, " ");
        sv_dir = String(pch);

        if (sv_speed == "-1") servo[counter].stop(); // -1 = stop
        else if (sv_speed == "0") { } // 0 = do nothing
        else if (sv_dir == "a") // dir set to "a" = absolute position
            servo[counter].write(sv_speed.toInt(), GLOBAL_SPEED);
        else set_servo(counter, sv_speed.toInt(), sv_dir.toInt());
        
        counter++;
        pch = strtok(NULL, " ");

        if (counter > SERVO_COUNT) {
            counter = 0;
            break;
        }
    }   
}

void set_servo(byte sv, int deg_s, bool dir) { 
    if (dir) servo[sv].write(GLOBAL_MIN, deg_s * .417, false);
    else servo[sv].write(GLOBAL_MAX, deg_s * .417, false);
}

void attach_all_servos() {
    for (int i = 0; i < SERVO_COUNT; i++) {
        servo[i].attach(servo_pins[i]);
    }
}



