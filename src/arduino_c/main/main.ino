#include <Servo.h>

const int box1StatusPin = 2;
const int box1ActionPin = 3;
Servo servo1;
const int box2StatusPin = 4;
const int box2ActionPin = 5;
Servo servo2;
// control vars
bool lock1Status = 0;
bool lock2Status = 0;
bool box1WasOpen = 0;
bool box2WasOpen = 0;

void getStatus() {
  Serial.println(
    String(digitalRead(box1StatusPin)) + ":" + 
    String(digitalRead(box2StatusPin)) + ":" + 
    String(lock1Status) + ":" + 
    String(lock2Status) + ";"
  );
}

void lockServo1() {
  servo1.write(0);
  lock1Status = 1;
}

void unlockServo1() {
  servo1.write(180);
  lock1Status = 0;
  box1WasOpen = 0;
}

void lockServo2() {
  servo2.write(0);
  lock2Status = 1;
}

void unlockServo2() {
  servo2.write(180);
  lock2Status = 0;
  box2WasOpen = 0;
}

void setup() {
  // setup serial port
  Serial.begin(115200);
  Serial.setTimeout(1);

  // setup pins
  pinMode(box1StatusPin, INPUT_PULLUP);
  servo1.attach(box1ActionPin);
  pinMode(box2StatusPin, INPUT_PULLUP);
  servo2.attach(box2ActionPin);

  // set initial status of servos
  if (digitalRead(box1StatusPin) == 0) {
    // box is closed, lock servo 1
    lockServo1();
  } else {
    // if box is open, make sure to unlock
    unlockServo1();
  }
  if (digitalRead(box2StatusPin) == 0) {
    // box is closed, lock servo 2
    lockServo2();
  } else {
    // if box is open, make sure to unlock
    unlockServo2();
  }
}

void loop() {
  if (digitalRead(box1StatusPin)) {
    // box is open
    if (lock1Status) {
      // box is locked, unlock to be able to close
      unlockServo1();
    }
    box1WasOpen = 1;
  } else if (box1WasOpen) {
    // it was open and now it's closed, so lock
    delay(1000); // wait to be sure it was closed
    lockServo1();
    box1WasOpen = 0;
  }
  if (digitalRead(box2StatusPin)) {
    // box is open
    if (lock2Status) {
      // box is locked, unlock to be able to close
      unlockServo2();
    }
    box2WasOpen = 1;
  } else if (box2WasOpen) {
    // it was open and now it's closed, so lock
    delay(1000); // wait to be sure it was closed
    lockServo2();
    box2WasOpen = 0;
  }
  if (Serial.available()) {
    String comm = Serial.readString();  
    if(comm == "O1") {
      // open box 1
      unlockServo1();
      getStatus();
    } else if (comm == "C1") {
      if (digitalRead(box1StatusPin) == 0) {
        // close box 1
        lockServo1();
      }
      getStatus();
    } else if (comm == "O2") {
      // open box 2
      unlockServo2();
      getStatus();
    } else if (comm == "C2") {
      if (digitalRead(box1StatusPin) == 0) {
        // close box 2
        lockServo2();
      }
      getStatus();
    } else {
      getStatus();
    }
  }
}
