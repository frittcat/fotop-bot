import json
import time
import yagmail
import schedule
import os
from datetime import datetime
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

# Configurações do email SMTP
EMAIL_REMETENTE = "script@mj3dlab.fr"
SENHA_REMETENTE = "I2&M2U0He"
SMTP_SERVER = "smtp.hostinger.com"
SMTP_PORT = 587

# Caminhos
CAMINHO_USUARIOS = "usuarios.json"
CAMINHO_LOG = "logs"

# Cria pasta de logs se não existir
if not os.path.exists(CAMINHO_LOG):
    os.makedirs(CAMINHO_LOG)

# Função para logar as mensagens
def log(mensagem):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(os.path.join(CAMINHO_LOG, "log.txt"), "a", encoding="utf-8") as f:
        f.write(f"[{now}] {mensagem}\n")
    print(f"[{now}] {mensagem}")

# Função para enviar email
def enviar_email(destinatario, assunto, corpo):
    try:
        yag = yagmail.SMTP(EMAIL_REMETENTE, SENHA_REMETENTE, host=SMTP_SERVER, port=SMTP_PORT)
        yag.send(
            to=destinatario,
            subject=assunto,
            contents=corpo
        )
        log(f"Email enviado para {destinatario}: {assunto}")
    except Exception as e:
        log(f"Erro ao enviar email: {e}")

# Função principal do bot
def rodar_bot():
    log("Iniciando ciclo de execução...")
    try:
        with open(CAMINHO_USUARIOS, "r", encoding="utf-8") as file:
            usuarios = json.load(file)

        for usuario_data in usuarios:
            if not usuario_data["ids"]:
                continue

            log(f"Tentando login para {usuario_data['usuario']}...")

            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.binary_location = "/usr/bin/chromium" # local do Chrome no Railway

            driver = uc.Chrome(
                options=options,
                browser_executable_path="/usr/bin/chromium"
            )

            driver.get("https://dashboard.fotop.com/login")
            time.sleep(2)

            # Login
            driver.find_element(By.NAME, "email").send_keys(usuario_data["usuario"])
            driver.find_element(By.NAME, "password").send_keys(usuario_data["senha"])
            driver.find_element(By.TAG_NAME, "form").submit()
            time.sleep(4)

            # Vai para a página de eventos
            driver.get("https://dashboard.fotop.com/eventos/proximos")
            time.sleep(4)

            novos_ids = []
            for evento_id in usuario_data["ids"]:
                try:
                    evento_url = f"https://dashboard.fotop.com/eventos/{evento_id}"
                    driver.get(evento_url)
                    time.sleep(2)

                    # Inscrever-se no evento (botão "Participar")
                    botao_participar = driver.find_element(By.XPATH, "//button[contains(text(), 'Participar')]")
                    botao_participar.click()
                    time.sleep(2)

                    # Email de sucesso
                    enviar_email(
                        destinatario=usuario_data["email_notificacao"],
                        assunto="Inscrição Realizada com Sucesso!",
                        corpo=f"Usuário: {usuario_data['usuario']}\nEvento ID: {evento_id}\nData/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                    )
                    log(f"Inscrição feita no evento {evento_id} para {usuario_data['usuario']}")

                except Exception as e:
                    log(f"Falha ao tentar evento {evento_id} para {usuario_data['usuario']}: {e}")
                    novos_ids.append(evento_id)

            usuario_data["ids"] = novos_ids

            driver.quit()

        with open(CAMINHO_USUARIOS, "w", encoding="utf-8") as file:
            json.dump(usuarios, file, indent=4, ensure_ascii=False)

    except Exception as e:
        log(f"Erro geral: {e}")

# Agenda para rodar a cada 1 minuto
schedule.every(1).minutes.do(rodar_bot)

if __name__ == "__main__":
    log("Bot Fotop iniciado.")
    while True:
        schedule.run_pending()
        time.sleep(1)
