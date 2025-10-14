/*
 * TMC2209 Stepper Motor Control for ESP32
 * Drive THREE steppers via STEP/DIR (no UART)
 * 
 * Pin 13: Set HIGH (used as 3.3V output)
 * Motor 1: DIR=12, STEP=14
 * Motor 2: DIR=27, STEP=26
 * Motor 3: DIR=25, STEP=33
 * 
 * Target: 200 RPM continuous rotation
 * MS1/MS2 floating = 16x microstepping
 */

// Pin 13 set HIGH for 3.3V output
const int powerPin = 13;

// Motor pin pairs (DIR, STEP)
const int dirPin1 = 12;
const int stepPin1 = 14;

const int dirPin2 = 27;
const int stepPin2 = 26;

const int dirPin3 = 25;
const int stepPin3 = 33;

// Motor configuration
const int STEPS_PER_REV = 200;
const int MICROSTEPS = 16;
const int ACTUAL_STEPS_PER_REV = STEPS_PER_REV * MICROSTEPS;  // 3200
const int PULSE_WIDTH_US = 100;  // 100 microseconds HIGH/LOW

// Target RPM
const float TARGET_RPM = 200.0;

// Calculate delay between steps for target RPM
// Total time per step = (60 / (RPM * steps_per_rev)) seconds
// Subtract the pulse widths (2 * PULSE_WIDTH_US)
const unsigned long STEP_DELAY_US = (unsigned long)((60000000.0 / (TARGET_RPM * ACTUAL_STEPS_PER_REV)) - (2 * PULSE_WIDTH_US));

unsigned long stepCount = 0;

void setup() {
  Serial.begin(115200);
  
  // Set pin 13 HIGH for 3.3V output
  pinMode(powerPin, OUTPUT);
  digitalWrite(powerPin, HIGH);
  
  // Initialize motor pins
  pinMode(dirPin1, OUTPUT);
  pinMode(stepPin1, OUTPUT);
  pinMode(dirPin2, OUTPUT);
  pinMode(stepPin2, OUTPUT);
  pinMode(dirPin3, OUTPUT);
  pinMode(stepPin3, OUTPUT);
  
  // Set all step pins LOW initially
  digitalWrite(stepPin1, LOW);
  digitalWrite(stepPin2, LOW);
  digitalWrite(stepPin3, LOW);
  
  // Set direction (HIGH = clockwise)
  digitalWrite(dirPin1, HIGH);
  digitalWrite(dirPin2, HIGH);
  digitalWrite(dirPin3, HIGH);
  
  delay(300);  // Allow drivers to settle
  
  Serial.println("TMC2209 - Triple motor control (ESP32)");
  Serial.print("Microstepping: ");
  Serial.print(MICROSTEPS);
  Serial.print("x, steps/rev: ");
  Serial.println(ACTUAL_STEPS_PER_REV);
  Serial.print("Target RPM: ");
  Serial.println(TARGET_RPM);
  Serial.print("Step delay: ");
  Serial.print(STEP_DELAY_US);
  Serial.println(" microseconds");
  Serial.println("Motors running...\n");
}

void loop() {
  // Pulse all three motors simultaneously
  digitalWrite(stepPin1, HIGH);
  digitalWrite(stepPin2, HIGH);
  digitalWrite(stepPin3, HIGH);
  delayMicroseconds(PULSE_WIDTH_US);
  
  digitalWrite(stepPin1, LOW);
  digitalWrite(stepPin2, LOW);
  digitalWrite(stepPin3, LOW);
  delayMicroseconds(PULSE_WIDTH_US);
  
  // Additional delay for speed control
  if (STEP_DELAY_US > 0) {
    delayMicroseconds(STEP_DELAY_US);
  }
  
  // Track revolutions
  stepCount++;
  if (stepCount % ACTUAL_STEPS_PER_REV == 0) {
    Serial.print("Revolutions: ");
    Serial.println(stepCount / ACTUAL_STEPS_PER_REV);
  }
}
