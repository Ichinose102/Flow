#include <SPI.h>
#include <MFRC522.h>
#include <DHT.h>
#include <IRremote.hpp>

// --- CONFIGURATION DES BROCHES ---
#define RST_PIN         9          // Reset du module RFID
#define SS_PIN          10         // SS (SDA) du module RFID
#define DHTPIN          2          // Broche DATA du DHT11
#define DHTTYPE         DHT11      // Type de capteur
#define IR_RECEIVE_PIN  4          // Broche du récepteur IR

// Initialisation des objets
MFRC522 mfrc522(SS_PIN, RST_PIN);
DHT dht(DHTPIN, DHTTYPE);

// Variable pour gérer le temps sans bloquer le code (non-blocking)
unsigned long lastSensorRead = 0;
const unsigned long interval = 2000; // Lire les capteurs toutes les 2 secondes

void setup() {
  Serial.begin(9600);   // Communication avec le PC (Python)
  
  // Initialisation SPI et RFID
  SPI.begin();
  mfrc522.PCD_Init();
  
  // Initialisation DHT11
  dht.begin();
  
  // Initialisation Récepteur IR
  IrReceiver.begin(IR_RECEIVE_PIN, ENABLE_LED_FEEDBACK);
  
  // Petit message de démarrage (optionnel)
  // Serial.println("SYSTEM:FLOW_START");
}

void loop() {
  // --- 1. LECTURE INFRAROUGE (Priorité haute) ---
  if (IrReceiver.decode()) {
    Serial.print("IR:");
    Serial.println(IrReceiver.decodedIRData.decodedRawData, HEX);
    IrReceiver.resume(); // Prêt pour le prochain code
  }

  // --- 2. LECTURE RFID ---
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    Serial.print("RFID:");
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      // Formate l'ID en Hexadécimal
      if(mfrc522.uid.uidByte[i] < 0x10) Serial.print("0");
      Serial.print(mfrc522.uid.uidByte[i], HEX);
    }
    Serial.println();
    
    mfrc522.PICC_HaltA();      // Arrête la lecture de la carte
    mfrc522.PCD_StopCrypto1(); // Arrête le chiffrement
  }

  // --- 3. LECTURE TEMPÉRATURE & HUMIDITÉ (Toutes les 2s) ---
  unsigned long currentMillis = millis();
  if (currentMillis - lastSensorRead >= interval) {
    lastSensorRead = currentMillis;

    float h = dht.readHumidity();
    float t = dht.readTemperature();

    // Vérifie si la lecture a réussi avant d'envoyer
    if (!isnan(h) && !isnan(t)) {
      Serial.print("TEMP:");
      Serial.println(t, 1); // 1 décimale
      
      Serial.print("HUM:");
      Serial.println(h, 0); // 0 décimale (ex: 45%)
    }
  }
}