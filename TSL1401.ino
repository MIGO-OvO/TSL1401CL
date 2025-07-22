#include <avr/pgmspace.h>

// 引脚定义
#define SI_PIN 2     // SI -> Digital Pin 2
#define CLK_PIN 3    // CLK -> Digital Pin 3
#define AO_PIN A0    // AO -> Analog Pin A0
#define NPIXELS 128  // 128像素传感器

// 全局变量
bool continuousCapture = false;
int frameDelay = 20;  // 默认20ms帧间隔

void setup() {
  // 初始化引脚
  pinMode(SI_PIN, OUTPUT);
  pinMode(CLK_PIN, OUTPUT);
  pinMode(AO_PIN, INPUT);
  
  // 初始状态
  digitalWrite(SI_PIN, LOW);
  digitalWrite(CLK_PIN, LOW);
  
  // 串口初始化
  Serial.begin(115200);
  while (!Serial); // 等待串口连接
}

void loop() {
  // 命令处理
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    switch (command) {
      case 'S': // 开始连续采集
        continuousCapture = true;
        Serial.println("CMD: Continuous capture started");
        break;
        
      case 'X': // 停止采集
        continuousCapture = false;
        Serial.println("CMD: Capture stopped");
        break;
        
      case 'T': // 设置间隔时间
        setFrameDelay();
        break;
    }
  }
  
  // 连续数据采集模式
  if (continuousCapture) {
    captureFrame();
    delay(frameDelay); // 帧间延迟
  }
}

// 设置帧间隔时间
void setFrameDelay() {
  delay(10); // 等待数据到达
  if (Serial.available() >= 3) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    int newDelay = input.toInt();
    
    if (newDelay >= 0 && newDelay <= 1000) {
      frameDelay = newDelay;
      Serial.print("CMD: Frame delay set to ");
      Serial.print(frameDelay);
      Serial.println("ms");
    }
  }
}

// 捕获一帧数据
void captureFrame() {
  // 触发传感器采集
  digitalWrite(SI_PIN, HIGH);
  digitalWrite(CLK_PIN, HIGH);
  digitalWrite(SI_PIN, LOW);
  digitalWrite(CLK_PIN, LOW);
  
  // 读取128个像素
  for (int i = 0; i < NPIXELS; i++) {
    // 时钟上升沿读取数据
    digitalWrite(CLK_PIN, HIGH);
    int value = analogRead(AO_PIN); // 10位ADC值(0-1023)
    digitalWrite(CLK_PIN, LOW);
    
    // 发送数据到上位机
    Serial.print(value);
    if (i < NPIXELS - 1) Serial.print(",");
  }
  Serial.println(); // 结束帧
}