#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <Wire.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>
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
LiquidCrystal_I2C lcd(0x27, 16, 2); // Khởi tạo mặc định, sẽ tự quét lại ở setup

// Hàm tự động quét tìm địa chỉ I2C của màn hình LCD (0x27 hoặc 0x3F)
uint8_t findI2CLCDAddress() {
  Wire.begin();
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      if (addr == 0x27 || addr == 0x3F) {
        return addr;
      }
    }
  }
  return 0x27; // Mặc định nếu không tìm thấy
}

void setup() {
  Serial.begin(115200);
  delay(100);
  
  // Thiết lập chân âm thanh DAC và LED
  dacWrite(SPEAKER_PIN, 0); // Mức 0V ban đầu để chống rè/ù loa
  pinMode(LED_YELLOW_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);

  // Tự động nhận diện địa chỉ I2C và khởi tạo LCD
  uint8_t lcdAddr = findI2CLCDAddress();
  Serial.printf("LCD I2C Address: 0x%02X\n", lcdAddr);
  lcd = LiquidCrystal_I2C(lcdAddr, 16, 2);
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("DUT AI Manager");
  lcd.setCursor(0, 1);
  lcd.print("Dang ket noi...");

  // Kết nối WiFi
  Serial.println("Dang ket noi WiFi: " + String(ssid));
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);
  WiFi.setSleep(false); // Tắt chế độ tiết kiệm năng lượng của WiFi để giữ kết nối socket HTTPS ổn định
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected! IP: " + WiFi.localIP().toString());

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

// --- CẤU HÌNH ÂM LƯỢNG ---
#define TTS_VOLUME_GAIN      5.0f  // Khuếch đại giọng nói TTS (gấp đôi mức cũ để loa kêu to rõ)
#define BEEP_HIGH            146   // Mức cao tiếng bíp (giảm nhẹ để bíp êm tai, thanh thoát, không lấn át tiếng nói)
#define BEEP_LOW             110   // Mức thấp tiếng bíp

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

// 3. Phát âm thanh WAV trực tiếp từ mảng RAM qua DAC GPIO 26 (chống giật lag, rè rè do mạng)
void playWavFromRAM(const uint8_t* wav, size_t totalBytes) {
  if (!wav || totalBytes < 44) return;

  // Kiểm tra định dạng RIFF và WAVE
  if (wav[0] != 'R' || wav[1] != 'I' || wav[2] != 'F' || wav[3] != 'F' ||
      wav[8] != 'W' || wav[9] != 'A' || wav[10] != 'V' || wav[11] != 'E') {
    Serial.println("Loi: Du lieu khong phai file WAV hop le");
    return;
  }

  uint16_t audioFormat = 1; // 1 = PCM
  uint16_t numChannels = 1;
  uint32_t sampleRate = 24000;
  uint16_t bitsPerSample = 16;
  size_t dataOffset = 0;
  size_t dataSize = 0;

  // Quét chính xác vị trí chunk "fmt " và "data" (tránh lệch byte gây tiếng xào xạc / rè)
  size_t offset = 12;
  while (offset + 8 <= totalBytes) {
    char chunkId[5];
    memcpy(chunkId, &wav[offset], 4);
    chunkId[4] = '\0';
    uint32_t chunkSize = (uint32_t)wav[offset + 4] |
                         ((uint32_t)wav[offset + 5] << 8) |
                         ((uint32_t)wav[offset + 6] << 16) |
                         ((uint32_t)wav[offset + 7] << 24);

    if (strcmp(chunkId, "fmt ") == 0 && offset + 8 + 14 <= totalBytes) {
      audioFormat   = (uint16_t)wav[offset + 8] | ((uint16_t)wav[offset + 9] << 8);
      numChannels   = (uint16_t)wav[offset + 10] | ((uint16_t)wav[offset + 11] << 8);
      sampleRate    = (uint32_t)wav[offset + 12] | ((uint32_t)wav[offset + 13] << 8) |
                      ((uint32_t)wav[offset + 14] << 16) | ((uint32_t)wav[offset + 15] << 24);
      if (offset + 8 + 16 <= totalBytes) {
        bitsPerSample = (uint16_t)wav[offset + 22] | ((uint16_t)wav[offset + 23] << 8);
      }
    } else if (strcmp(chunkId, "data") == 0) {
      dataOffset = offset + 8;
      dataSize = chunkSize;
      break;
    }

    offset += 8 + chunkSize;
    if (chunkSize & 1) offset++; // Padding byte nếu chunkSize là số lẻ (chuẩn RIFF)
  }

  // Fallback nếu không quét được chunk data
  if (dataOffset == 0 || dataOffset >= totalBytes) {
    dataOffset = 44;
    dataSize = totalBytes > 44 ? totalBytes - 44 : 0;
  }
  if (dataOffset + dataSize > totalBytes) {
    dataSize = totalBytes - dataOffset;
  }

  if (sampleRate == 0 || sampleRate > 96000) sampleRate = 24000;
  if (numChannels == 0) numChannels = 1;
  if (bitsPerSample == 0) bitsPerSample = 16;

  Serial.printf("Phat audio tu RAM: %u Hz, %u channels, %u bits, Data size: %u bytes\n",
                sampleRate, numChannels, bitsPerSample, dataSize);

  unsigned long sampleIntervalUs = 1000000UL / sampleRate;

  // Khử tiếng bụp loa: Fade-in nhẹ từ 0 lên mức trung tính 128 (DC bias)
  for (int v = 0; v <= 128; v += 4) {
    dacWrite(SPEAKER_PIN, v);
    delayMicroseconds(50);
  }

  const uint8_t* pData = &wav[dataOffset];
  uint8_t lastSample = 128;
  unsigned long nextMicros = micros();

  if (bitsPerSample == 16) {
    size_t bytesPerFrame = 2 * numChannels;
    size_t totalFrames = dataSize / bytesPerFrame;

    for (size_t f = 0; f < totalFrames; f++) {
      size_t idx = f * bytesPerFrame;
      int32_t sample16 = 0;

      if (numChannels == 1) {
        sample16 = (int16_t)(pData[idx] | (pData[idx + 1] << 8));
      } else {
        int16_t left  = (int16_t)(pData[idx] | (pData[idx + 1] << 8));
        int16_t right = (int16_t)(pData[idx + 2] | (pData[idx + 3] << 8));
        sample16 = ((int32_t)left + (int32_t)right) / 2;
      }

      // Khuếch đại âm lượng giọng nói TTS (Digital Pre-amp)
      int32_t boosted = (int32_t)(sample16 * TTS_VOLUME_GAIN);
      if (boosted > 32767) boosted = 32767;
      else if (boosted < -32768) boosted = -32768;

      int32_t dacVal32 = 128 + (boosted >> 8);
      if (dacVal32 < 0) dacVal32 = 0;
      else if (dacVal32 > 255) dacVal32 = 255;

      dacWrite(SPEAKER_PIN, (uint8_t)dacVal32);
      lastSample = (uint8_t)dacVal32;

      nextMicros += sampleIntervalUs;
      while ((long)(micros() - nextMicros) < 0) {
        // Canh chuẩn micro-giây
      }

      // Định kỳ yield() reset watchdog để không bị crash khi audio dài
      if ((f & 0x3FF) == 0) {
        yield();
        nextMicros = micros();
      }
    }
  } else {
    // 8-bit unsigned PCM
    size_t bytesPerFrame = numChannels;
    size_t totalFrames = dataSize / bytesPerFrame;

    for (size_t f = 0; f < totalFrames; f++) {
      size_t idx = f * bytesPerFrame;
      int32_t sample8 = (int32_t)pData[idx] - 128;
      sample8 = (int32_t)(sample8 * TTS_VOLUME_GAIN);
      if (sample8 > 127) sample8 = 127;
      else if (sample8 < -128) sample8 = -128;

      int32_t dacVal32 = 128 + sample8;
      if (dacVal32 < 0) dacVal32 = 0;
      else if (dacVal32 > 255) dacVal32 = 255;

      dacWrite(SPEAKER_PIN, (uint8_t)dacVal32);
      lastSample = (uint8_t)dacVal32;

      nextMicros += sampleIntervalUs;
      while ((long)(micros() - nextMicros) < 0) {
        // Canh chuẩn micro-giây
      }

      if ((f & 0x3FF) == 0) {
        yield();
        nextMicros = micros();
      }
    }
  }

  // Khử tiếng bụp loa: Fade-out nhẹ từ mẫu cuối cùng về 0
  for (int v = lastSample; v >= 0; v -= 4) {
    dacWrite(SPEAKER_PIN, v);
    delayMicroseconds(50);
  }
  dacWrite(SPEAKER_PIN, 0); // Ngắt điện áp DC trên loa để chống nóng và rè
}

// Tải toàn bộ file WAV từ server vào bộ nhớ RAM rồi mới phát (giải quyết triệt để giật/rè do mạng)
void downloadAndPlayWav(HTTPClient &http) {
  int totalBytes = http.getSize();
  Stream* stream = http.getStreamPtr();
  if (!stream) {
    Serial.println("Loi: Stream audio khong kha dung");
    return;
  }

  const size_t MAX_AUDIO_SIZE = 250 * 1024; // Giới hạn tối đa 250KB RAM
  if (totalBytes > (int)MAX_AUDIO_SIZE) {
    Serial.printf("Canh bao: File audio qua lon (%d bytes), vuot gioi han RAM\n", totalBytes);
    playFallbackSuccessSound();
    return;
  }

  size_t allocSize = (totalBytes > 0) ? (size_t)totalBytes : MAX_AUDIO_SIZE;

  // Kiểm tra heap trống (giữ lại tối thiểu 25KB cho hệ điều hành)
  size_t freeHeap = ESP.getFreeHeap();
  Serial.printf("Free Heap truoc khi tai Audio: %u bytes (Can: %u bytes)\n", freeHeap, allocSize);
  if (freeHeap < allocSize + 25000) {
    Serial.println("Loi: Khong du RAM de chua toan bo file audio!");
    playFallbackSuccessSound();
    return;
  }

  uint8_t* audioBuf = (uint8_t*)malloc(allocSize);
  if (!audioBuf) {
    Serial.printf("Loi: malloc that bai! Khoi nho lien tuc lon nhat (MaxAllocHeap): %u bytes\n", ESP.getMaxAllocHeap());
    playFallbackSuccessSound();
    return;
  }

  // Tải toàn bộ luồng audio vào RAM
  size_t bytesLoaded = 0;
  unsigned long startDownload = millis();
  unsigned long lastDataTime = millis();

  while ((totalBytes <= 0 || (int)bytesLoaded < totalBytes) && (millis() - lastDataTime < 4000)) {
    if (stream->available() > 0) {
      size_t toRead = stream->available();
      if (totalBytes > 0 && bytesLoaded + toRead > (size_t)totalBytes) {
        toRead = (size_t)totalBytes - bytesLoaded;
      } else if (totalBytes <= 0 && bytesLoaded + toRead > MAX_AUDIO_SIZE) {
        toRead = MAX_AUDIO_SIZE - bytesLoaded;
      }

      size_t n = stream->readBytes((char*)(audioBuf + bytesLoaded), toRead);
      if (n > 0) {
        bytesLoaded += n;
        lastDataTime = millis();
      }
    } else {
      delay(1);
    }

    if (totalBytes <= 0 && !http.connected() && stream->available() == 0) {
      break;
    }
  }

  Serial.printf("Da tai %u bytes WAV vao RAM trong %lu ms\n", bytesLoaded, millis() - startDownload);

  // Đóng kết nối HTTP trước khi phát để giải phóng tài nguyên SSL/mạng cho CPU
  http.end();

  // Phát audio mượt mà từ RAM
  if (bytesLoaded >= 44) {
    playWavFromRAM(audioBuf, bytesLoaded);
  } else {
    Serial.println("Loi: Du lieu audio tai ve qua ngan (< 44 bytes)");
    playFallbackSuccessSound();
  }

  // Giải phóng RAM
  free(audioBuf);
  Serial.printf("Free Heap sau khi phat audio: %u bytes\n", ESP.getFreeHeap());
}

// 4. Âm thanh dự phòng nếu không có audio từ server (2 tiếng bíp vui tai)
void playFallbackSuccessSound() {
  playToneDAC(SPEAKER_PIN, 1200, 120);
  delay(60);
  playToneDAC(SPEAKER_PIN, 1800, 180);
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
    WiFiClientSecure client;
    client.setInsecure(); // Cho phép HTTPS không cần nạp chứng chỉ SSL CA
    client.setHandshakeTimeout(45); 
    client.setTimeout(45);

    HTTPClient http;
    http.setTimeout(45000); // 45000ms
    http.setReuse(false);

    Serial.println("\n--- [START API REQUEST] ---");
    Serial.printf("Free Heap RAM truoc khi goi API: %u bytes\n", ESP.getFreeHeap());
    Serial.println("Target URL: " + apiUrl);

    if (!http.begin(client, apiUrl)) {
      Serial.println("Loi: Khong the khoi tao HTTP Client");
      lcd.clear();
      lcd.print("Loi ket noi!");
      playErrorSound();
      delay(2000);
      return;
    }

    // Thiết lập User-Agent trình duyệt để Cloudflare không chặn mã lỗi 1010
    http.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");
    http.addHeader("Authorization", "Bearer " + authCode);
    http.addHeader("Content-Type", "application/json");

    // Thu thập các Header tùy chỉnh trả về từ Server
    const char* headerKeys[] = {"X-Message", "x-message", "Content-Type", "Content-Length"};
    http.collectHeaders(headerKeys, 4);
    
    String jsonBody = "{\"card_code\":\"" + id + "\"}";
    Serial.println("Request Body: " + jsonBody);
    
    int httpResponseCode = http.POST(jsonBody);
    Serial.printf("HTTP Response Code: %d (%s)\n", httpResponseCode, http.errorToString(httpResponseCode).c_str());

    String contentType = http.header("Content-Type");
    String serverMessage = http.header("X-Message");
    if (serverMessage.length() == 0) {
      serverMessage = http.header("x-message");
    }

    Serial.println("Content-Type: " + contentType);
    Serial.println("Header X-Message: " + serverMessage);
    Serial.printf("Content-Length: %d\n", http.getSize());

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
      
      // Tải toàn bộ audio WAV vào RAM rồi phát qua DAC GPIO 26
      if (contentType.indexOf("audio") >= 0 || contentType.indexOf("wav") >= 0 || http.getSize() > 100) {
        downloadAndPlayWav(http);
      } else {
        playFallbackSuccessSound();
      }
      
      delay(1500);
      
    } else if (httpResponseCode == 400 || httpResponseCode == 404) {
      digitalWrite(LED_RED_PIN, HIGH);
      
      if (serverMessage.length() > 0) {
        Serial.println("Chi tiet loi tu server (Header): " + serverMessage);
        lcd.print(serverMessage.substring(0, 16));
        if (serverMessage.length() > 16) {
          lcd.setCursor(0, 1);
          lcd.print(serverMessage.substring(16, 32));
        }

        if (contentType.indexOf("audio") >= 0 || contentType.indexOf("wav") >= 0 || http.getSize() > 100) {
          downloadAndPlayWav(http);
        } else {
          playErrorSound();
        }
      } else {
        String payload = http.getString();
        Serial.println("Server Response Payload: " + payload);
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
          lcd.print("The chua dang ky!");
        }
        playErrorSound();
      }
      
      delay(3000); 
    } else {
      digitalWrite(LED_RED_PIN, HIGH);
      lcd.print("Loi Server!");
      lcd.setCursor(0, 1);
      lcd.print("Code: " + String(httpResponseCode));
      
      if (httpResponseCode > 0) {
        String payload = http.getString();
        Serial.println("Server Response Payload: " + payload);
      } else {
        Serial.printf("HTTP Client Error Detail: %s (Mã lỗi: %d)\n", http.errorToString(httpResponseCode).c_str(), httpResponseCode);
      }
      
      playErrorSound();
      delay(3000); 
    }
    
    http.end();
    Serial.println("--- [END API REQUEST] ---\n");
  } else {
    lcd.clear();
    lcd.print("Loi WiFi!");
    Serial.println("Mat ket noi WiFi");
  }
}