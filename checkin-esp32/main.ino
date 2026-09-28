#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>
#include "sound_data.h"
#include "secrets.h"

// --- CẤU HÌNH WIFI & API ---
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;
const String apiUrl = API_URL; 
const String authCode = AUTH_CODE;

// --- CẤU HÌNH CHÂN (PINS) ---
#define RST_PIN         27
#define SS_PIN          5
#define SPEAKER_PIN     26  // DAC2 của ESP32 kết nối ngõ vào âm thanh (L hoặc R) của PAM8403
#define LED_YELLOW_PIN  25
#define LED_GREEN_PIN   33
#define LED_RED_PIN     32

// --- KHỞI TẠO ĐỐI TƯỢNG ---
MFRC522 mfrc522(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(0x27, 16, 2); // Địa chỉ I2C có thể là 0x27 hoặc 0x3F tùy module

void setup() {
  Serial.begin(115200);
  
  // Thiết lập chân âm thanh DAC và LED
  dacWrite(SPEAKER_PIN, 0); // Mức 0V ban đầu để chống rè/ù loa
  pinMode(LED_YELLOW_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);

  // Khởi tạo LCD
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Dang ket noi...");

  // Kết nối WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("connecting...");
  }
  Serial.println("\nWiFi connected");

  // Khởi tạo SPI và RFID
  SPI.begin();
  mfrc522.PCD_Init();
  
  setIdleState(); // Chuyển sang trạng thái chờ
}

void loop() {
  // Kiểm tra xem có thẻ mới không
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }
  // Đọc dữ liệu từ thẻ
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // 1. Đọc thành công -> Phát tiếng bíp ngắn
  playScanSound();
  
  // Tắt đèn vàng, lấy UID của thẻ
  digitalWrite(LED_YELLOW_PIN, LOW);
  String cardID = getCardUID();
  Serial.println("Quet the thanh cong. ID: " + cardID);

  // 2. Hiển thị Loading trên LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Dang xu ly...");
  
  // 3. Gọi API
  checkCardAPI(cardID);
  
  // Reset lại mạch MFRC522 để chuẩn bị đọc thẻ tiếp theo
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  
  // Quay lại trạng thái chờ
  setIdleState(); 
}

// Hàm lấy ID thẻ chuyển thành chuỗi Hex
String getCardUID() {
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    uid += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

// Hàm phát âm thanh dạng xung tần số qua DAC GPIO 26 (thay thế còi Buzzer)
void playToneDAC(uint8_t pin, unsigned int freq, unsigned int durationMs) {
  if (freq == 0 || durationMs == 0) return;
  unsigned long period = 1000000UL / freq;
  unsigned long halfPeriod = period / 2;
  unsigned long cycles = (unsigned long)freq * durationMs / 1000UL;
  for (unsigned long i = 0; i < cycles; i++) {
    dacWrite(pin, 180);
    delayMicroseconds(halfPeriod);
    dacWrite(pin, 70);
    delayMicroseconds(halfPeriod);
  }
  dacWrite(pin, 0);
}

// 1. Âm thanh khi quét thẻ (tiếng bíp ngắn qua loa)
void playScanSound() {
  playToneDAC(SPEAKER_PIN, 1800, 80);
}

// 2. Âm thanh khi Thất bại/Lỗi (tiếng bíp trầm cảnh báo qua loa)
void playErrorSound() {
  playToneDAC(SPEAKER_PIN, 400, 400);
  delay(150);
  playToneDAC(SPEAKER_PIN, 400, 400);
}

// 3. Phát âm thanh WAV trực tiếp từ luồng HTTP nhận về từ Server qua DAC GPIO 26
void playWavStream(WiFiClient* stream, int totalBytes) {
  if (!stream) return;

  // Đọc 44 bytes header của file WAV
  uint8_t header[44];
  size_t bytesRead = stream->readBytes(header, 44);
  if (bytesRead < 44) {
    Serial.println("Loi: Header WAV khong du 44 bytes");
    return;
  }

  // Kiểm tra định dạng RIFF và WAVE
  if (header[0] != 'R' || header[1] != 'I' || header[2] != 'F' || header[3] != 'F' ||
      header[8] != 'W' || header[9] != 'A' || header[10] != 'V' || header[11] != 'E') {
    Serial.println("Loi: Khong phai file WAV hop le");
    return;
  }

  // Trích xuất Sample Rate (mặc định 48000 Hz, 24000 Hz hoặc 16000 Hz)
  uint32_t sampleRate = (uint32_t)header[24] | ((uint32_t)header[25] << 8) |
                        ((uint32_t)header[26] << 16) | ((uint32_t)header[27] << 24);
  uint16_t numChannels = (uint16_t)header[22] | ((uint16_t)header[23] << 8);
  uint16_t bitsPerSample = (uint16_t)header[34] | ((uint16_t)header[35] << 8);

  if (sampleRate == 0 || sampleRate > 96000) sampleRate = 48000;
  if (numChannels == 0) numChannels = 1;
  if (bitsPerSample == 0) bitsPerSample = 16;

  Serial.printf("Phat audio WAV: %u Hz, %u channels, %u bits\n", sampleRate, numChannels, bitsPerSample);

  unsigned long sampleIntervalUs = 1000000UL / sampleRate;
  unsigned long nextMicros = micros();

  // Khử tiếng bụp loa: Fade-in nhẹ từ 0 lên mức 128 (DC bias của DAC)
  for (int v = 0; v <= 128; v += 4) {
    dacWrite(SPEAKER_PIN, v);
    delayMicroseconds(50);
  }

  const size_t BUF_SIZE = 1024;
  uint8_t buffer[BUF_SIZE];
  uint8_t lastSample = 128;

  int remainingBytes = totalBytes > 44 ? totalBytes - 44 : -1;

  while (stream->connected() && (remainingBytes > 0 || remainingBytes == -1 || stream->available())) {
    size_t toRead = sizeof(buffer);
    if (remainingBytes > 0 && (int)toRead > remainingBytes) {
      toRead = remainingBytes;
    }

    size_t n = stream->readBytes(buffer, toRead);
    if (n == 0) break;
    if (remainingBytes > 0) remainingBytes -= n;

    if (bitsPerSample == 16) {
      size_t step = 2 * numChannels;
      for (size_t i = 0; i + 1 < n; i += step) {
        int16_t sample16 = (int16_t)(buffer[i] | (buffer[i + 1] << 8));
        // Chuyển đổi 16-bit signed (-32768 đến 32767) sang 8-bit unsigned (0 đến 255)
        uint8_t dacVal = (uint8_t)((sample16 + 32768) >> 8);
        dacWrite(SPEAKER_PIN, dacVal);
        lastSample = dacVal;

        nextMicros += sampleIntervalUs;
        while ((long)(micros() - nextMicros) < 0) {
          // Chờ đúng thời gian phát mẫu tiếp theo
        }
      }
    } else {
      // 8-bit audio
      for (size_t i = 0; i < n; i += numChannels) {
        uint8_t dacVal = buffer[i];
        dacWrite(SPEAKER_PIN, dacVal);
        lastSample = dacVal;

        nextMicros += sampleIntervalUs;
        while ((long)(micros() - nextMicros) < 0) {
          // Chờ đúng thời gian phát mẫu tiếp theo
        }
      }
    }
  }

  // Khử tiếng bụp loa: Fade-out nhẹ từ mẫu cuối cùng về 0
  for (int v = lastSample; v >= 0; v -= 4) {
    dacWrite(SPEAKER_PIN, v);
    delayMicroseconds(50);
  }
  dacWrite(SPEAKER_PIN, 0); // Đưa về 0V để chống nóng loa và tiết kiệm năng lượng
}

// 4. Âm thanh dự phòng nếu không có audio từ server
void playFallbackSuccessSound() {
  const unsigned long sampleInterval = 1000000UL / SUCCESS_AUDIO_SAMPLE_RATE;
  unsigned long nextMicros = micros();

  uint8_t firstSample = pgm_read_byte(&(success_audio_data[0]));
  for (int v = 0; v <= firstSample; v += 4) {
    dacWrite(SPEAKER_PIN, v);
    delayMicroseconds(100);
  }

  for (uint32_t i = 0; i < SUCCESS_AUDIO_LEN; i++) {
    dacWrite(SPEAKER_PIN, pgm_read_byte(&(success_audio_data[i])));
    nextMicros += sampleInterval;
    while ((long)(micros() - nextMicros) < 0) {
    }
  }

  uint8_t lastSample = pgm_read_byte(&(success_audio_data[SUCCESS_AUDIO_LEN - 1]));
  for (int v = lastSample; v >= 0; v -= 4) {
    dacWrite(SPEAKER_PIN, v);
    delayMicroseconds(100);
  }
  dacWrite(SPEAKER_PIN, 0);
}

// Hàm chuyển về trạng thái chờ quét thẻ
void setIdleState() {
  digitalWrite(LED_YELLOW_PIN, HIGH); // Đèn vàng sáng khi chờ
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("San sang...");
  lcd.setCursor(0, 1);
  lcd.print("Moi quet the!");
}

// Hàm gọi API và xử lý Response
void checkCardAPI(String id) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(apiUrl);
    
    // Thu thập các Header tùy chỉnh trả về từ Server
    const char* headerKeys[] = {"X-Message", "Content-Type"};
    http.collectHeaders(headerKeys, 2);

    http.addHeader("Authorization", "Bearer " + authCode);
    http.addHeader("Content-Type", "application/json");
    
    String jsonBody = "{\"card_code\":\"" + id + "\"}";
    Serial.println("Sending Request Body: " + jsonBody);
    
    int httpResponseCode = http.POST(jsonBody);
    String contentType = http.header("Content-Type");
    String serverMessage = http.header("X-Message");

    lcd.clear();
    lcd.setCursor(0, 0);

    if (httpResponseCode == 200 || httpResponseCode == 201) {
      // Thành công
      digitalWrite(LED_GREEN_PIN, HIGH);
      
      if (serverMessage.length() == 0) {
        serverMessage = "Checkin thanh cong!";
      }

      Serial.println("API Thong bao: " + serverMessage);
      
      // Hiển thị text lên LCD 16x2
      lcd.print(serverMessage.substring(0, 16));
      if (serverMessage.length() > 16) {
        lcd.setCursor(0, 1);
        lcd.print(serverMessage.substring(16, 32));
      }
      
      // Phát trực tiếp luồng Audio WAV nhận về từ Server qua DAC GPIO 26
      if (contentType.indexOf("audio") >= 0 || contentType.indexOf("wav") >= 0 || http.getSize() > 100) {
        WiFiClient* stream = http.getStreamPtr();
        playWavStream(stream, http.getSize());
      } else {
        playFallbackSuccessSound();
      }
      
      delay(1500);
      
    } else if (httpResponseCode == 400 || httpResponseCode == 404) {
      digitalWrite(LED_RED_PIN, HIGH);
      
      if (serverMessage.length() > 0) {
        Serial.println("Chi tiet loi tu server: " + serverMessage);
        lcd.print(serverMessage.substring(0, 16));
        if (serverMessage.length() > 16) {
          lcd.setCursor(0, 1);
          lcd.print(serverMessage.substring(16, 32));
        }

        if (contentType.indexOf("audio") >= 0 || contentType.indexOf("wav") >= 0) {
          WiFiClient* stream = http.getStreamPtr();
          playWavStream(stream, http.getSize());
        } else {
          playErrorSound();
        }
      } else {
        String payload = http.getString();
        JsonDocument doc;
        DeserializationError error = deserializeJson(doc, payload);
        if (!error && doc["message"].is<String>()) {
          serverMessage = doc["message"].as<String>();
          lcd.print(serverMessage.substring(0, 16));
          if (serverMessage.length() > 16) {
            lcd.setCursor(0, 1);
            lcd.print(serverMessage.substring(16, 32));
          }
        } else {
          lcd.print("Loi the / Meeting!");
        }
        playErrorSound();
      }
      
      delay(3000); 
    } else {
      digitalWrite(LED_RED_PIN, HIGH);
      lcd.print("Loi Server!");
      lcd.setCursor(0, 1);
      lcd.print("Code: " + String(httpResponseCode));
      Serial.println("HTTP Error code: " + String(httpResponseCode));
      playErrorSound();
      delay(3000); 
    }
    
    http.end();
  } else {
    lcd.clear();
    lcd.print("Loi WiFi!");
    Serial.println("Mat ket noi WiFi");
  }
}