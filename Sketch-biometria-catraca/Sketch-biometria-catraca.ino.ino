// Versão melhorada do código para Arduino com:
// - Suporte dinâmico ao tamanho da biblioteca (ex: 200 slots)
// - Comando especial para contar quantos templates estão salvos
// - Interface serial para comandos externos via Python
// - Controle de LED RGB para cada etapa do processo de registro, com distinção de cores por contexto

#include <Adafruit_Fingerprint.h>
#include <SoftwareSerial.h>
#define PINO_RELE 4

// Cria uma conexão serial com o sensor usando os pinos digitais 2 (RX) e 3 (TX)
SoftwareSerial mySerial(2, 3);
Adafruit_Fingerprint finger(&mySerial);
volatile bool cancelarOperacao = false;
String comandoSerial = "";


void setup() {
  Serial.begin(9600); // Inicializa a serial para comunicação com o PC
  while (!Serial);    // Aguarda inicialização completa da serial

  finger.begin(57600); // Inicializa o sensor biométrico
  if (finger.verifyPassword()) {
    Serial.println("Sensor pronto");
  } else {
    Serial.println("Falha no sensor");
    while (1) { delay(1); } // Trava o loop se não conseguir comunicar com o sensor
  }
  finger.LEDcontrol(FINGERPRINT_LED_OFF, 0, 0); // Garante que o LED comece desligado
  pinMode(PINO_RELE, OUTPUT);
  travarTrava(); // Inicia com a trava ativada (fechada)

}

void loop() {
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    comando.trim(); // Remove espaços extras e quebras de linha

    if (comando == "count") {
      if (finger.getTemplateCount() == FINGERPRINT_OK) {
        Serial.print("Templates salvos: ");
        Serial.print(finger.templateCount);
        Serial.print("/");
        Serial.println(finger.capacity);
      } else {
        Serial.println("Erro ao contar templates");
      }
    }
    else if (comando == "scan") {
      verificarDigital();
    }
    else if (comando.startsWith("delete ")) {
      int id = comando.substring(7).toInt();
      apagarDigital(id);
    }
    else if (comando.startsWith("enroll ")) {
      int id = comando.substring(7).toInt();
      registrarDigital(id);
    }
    else if (comando == "travar") {
      travarTrava();
    }
    else if (comando == "destravar") {
      destravarTrava();
    }
    else if (comando == "cancelar") {
      cancelarOperacao = true;
      Serial.println("Operação cancelada");
}

    else {
      Serial.println("Comando desconhecido");
    }
  }
}

void verificarDigital() {
  Serial.println("scan");
  cancelarOperacao = false;
  comandoSerial = "";
  travarTrava();
  setVerificando();

  while (true) {
    if (finger.getImage() == FINGERPRINT_OK) {
      break;
    }

    while (Serial.available()) {
      char c = Serial.read();
      if (c == '\n') {
        comandoSerial.trim();
        if (comandoSerial == "cancelar") {
          cancelarOperacao = true;
        }
        comandoSerial = "";
      } else {
        comandoSerial += c;
      }
    }

    if (cancelarOperacao) {
      Serial.println("Leitura cancelada");
      setErro();
      return;
    }

    delay(100);
  }

  setCapturando(); // LED azul piscando: capturando imagem

  if (finger.image2Tz() != FINGERPRINT_OK || finger.fingerSearch() != FINGERPRINT_OK) {
    Serial.println("Digital não encontrada");
    setErro();
    return;
  }

  Serial.print("ID encontrado: ");
  Serial.println(finger.fingerID);
  destravarTrava();  // Destrava se encontrado
  setSucesso();
}

void registrarDigital(int id) {
  Serial.println("Coloque o dedo...");
  setEsperando(); // LED azul respirando: aguardando dedo para registro
  while (finger.getImage() != FINGERPRINT_OK);
  setCapturando();
  if (finger.image2Tz(1) != FINGERPRINT_OK) {
    setErro();
    return;
  }

  Serial.println("Remova...");
  delay(2000);
  while (finger.getImage() != FINGERPRINT_NOFINGER);

  Serial.println("Coloque novamente...");
  setEsperando();
  while (finger.getImage() != FINGERPRINT_OK);
  setCapturando();
  if (finger.image2Tz(2) != FINGERPRINT_OK) {
    setErro();
    return;
  }

  if (finger.createModel() != FINGERPRINT_OK || finger.storeModel(id) != FINGERPRINT_OK) {
    Serial.println("Falha ao salvar digital");
    setErro();
    return;
  }

  Serial.print("digital-cadastrada:");
  Serial.println(id);

  setSucesso();
}

void apagarDigital(int id) {
  if (finger.deleteModel(id) == FINGERPRINT_OK) {
    Serial.println("Digital apagada com sucesso");
  } else {
    Serial.println("Erro ao apagar");
  }
}

void travarTrava() {
  digitalWrite(PINO_RELE, HIGH); // HIGH ativa o relé (pode ser LOW dependendo do modelo)
  Serial.println("Trava ativada");
}

void destravarTrava() {
  digitalWrite(PINO_RELE, LOW); // LOW desativa o relé (libera)
  Serial.println("Trava desativada");
}

// LED roxo: sucesso
void setSucesso() {
  finger.LEDcontrol(FINGERPRINT_LED_FLASHING, 50, FINGERPRINT_LED_PURPLE, 5);
  delay(2000);
  finger.LEDcontrol(FINGERPRINT_LED_OFF, 0, 0);
}

// LED vermelho: erro
void setErro() {
  finger.LEDcontrol(FINGERPRINT_LED_ON, 0, FINGERPRINT_LED_RED);
  delay(2000);
  finger.LEDcontrol(FINGERPRINT_LED_OFF, 0, 0);
}

// LED azul respirando: aguardando dedo para registro
void setEsperando() {
  finger.LEDcontrol(FINGERPRINT_LED_BREATHING, 200, FINGERPRINT_LED_BLUE);
}

// LED azul piscando rapidamente: capturando imagem
void setCapturando() {
  finger.LEDcontrol(FINGERPRINT_LED_FLASHING, 10, FINGERPRINT_LED_BLUE, 200);
}

// LED azul fixo: aguardando dedo para leitura
void setVerificando() {
  finger.LEDcontrol(FINGERPRINT_LED_ON, 0, FINGERPRINT_LED_BLUE);
}
