#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>

// ---- Paramètres WiFi ----
const char* ssid = "Ooredoo 5G_864CE3";        
const char* password = "4KVXEK8TZA";

// ---- Broches ----
#define SS_PIN  21
#define RST_PIN 22
#define LED_VERTE  16
#define LED_ROUGE  2
#define LED_BLEUE  4
#define BUZZER     15

MFRC522 mfrc522(SS_PIN, RST_PIN);

// Clignotement LED bleue
unsigned long previousMillis = 0;
const long interval = 300;

// URL serveur
const char* serverURL = "http://192.168.1.221:8000/rfid";

// Fonction pour faire sonner le buzzer 
void beep(int freq, int duration_ms){
  tone(BUZZER, freq, duration_ms);
  delay(duration_ms + 50);
  noTone(BUZZER);
}

// Formate UID en AA:BB:CC:DD
String uidToString(MFRC522::Uid &uid){
  String s = "";
  for(byte i=0; i<uid.size; i++){
    if(uid.uidByte[i]<0x10) s += "0";
    s += String(uid.uidByte[i], HEX);
  }
  s.toUpperCase();
  return s;
}

// Fonction qui envoie l'UID et idtache
bool sendUID(String uid){
  if(WiFi.status() != WL_CONNECTED){
    Serial.println("WiFi non connecté");
    return false;
  }

  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  String payload = "{\"uid\":\"" + uid + "\",\"idtache\":5}";
  Serial.println("Envoi UID au serveur : " + payload);

  int httpResponseCode = http.POST(payload);

  if(httpResponseCode > 0){
    Serial.print("Réponse serveur : ");
    Serial.println(httpResponseCode);
    String response = http.getString();
    Serial.println("Contenu : " + response);
    http.end();
    return true;
  } else {
    Serial.print("Erreur envoi HTTP : ");
    Serial.println(httpResponseCode);
    http.end();
    return false;
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(LED_VERTE, OUTPUT);
  pinMode(LED_ROUGE, OUTPUT);
  pinMode(LED_BLEUE, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  digitalWrite(LED_VERTE, LOW);
  digitalWrite(LED_ROUGE, LOW);
  digitalWrite(LED_BLEUE, LOW);

  SPI.begin();
  mfrc522.PCD_Init();
  Serial.println("RC522 prêt.");

  WiFi.begin(ssid, password);
  Serial.print("Connexion WiFi");
  while (WiFi.status() != WL_CONNECTED){
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nWiFi connecté !");
}

void loop() {
  // Clignotement LED bleue pendant inactivité
  unsigned long currentMillis = millis();
  if(currentMillis - previousMillis >= interval){
    previousMillis = currentMillis;
    digitalWrite(LED_BLEUE, !digitalRead(LED_BLEUE));
  }

  if(!mfrc522.PICC_IsNewCardPresent()) return;
  if(!mfrc522.PICC_ReadCardSerial()){
    Serial.println("Erreur lecture carte !");
    digitalWrite(LED_BLEUE, LOW);
    digitalWrite(LED_ROUGE, HIGH);
    beep(500,400);      // même bip que ton code
    digitalWrite(LED_ROUGE, LOW);
    return;
  }

  String uidStr = uidToString(mfrc522.uid);
  Serial.println("Carte détectée : " + uidStr);

  // LED verte allumée pendant envoi
  digitalWrite(LED_VERTE, HIGH);
  digitalWrite(LED_BLEUE, LOW);  // stop clignotement pendant l'envoi
  beep(1000,150);                // même bip que ton code

  bool ok = sendUID(uidStr);

  if(ok){
    Serial.println("UID enregistré avec succès !");
  } else {
    Serial.println("Échec enregistrement UID !");
    digitalWrite(LED_ROUGE, HIGH);
    beep(500,400);                // même bip que ton code pour erreur
    digitalWrite(LED_ROUGE, LOW);
  }

  digitalWrite(LED_VERTE, LOW);   // LED verte s’éteint après envoi
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  delay(500);
}
