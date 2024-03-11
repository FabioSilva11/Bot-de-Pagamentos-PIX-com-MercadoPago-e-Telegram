import datetime
import mercadopago
import telebot
import base64
from PIL import Image
from io import BytesIO

sdk = mercadopago.SDK(TOKEN_MERCADOPAGO)
bot = telebot.TeleBot(TOKEN_BOT)

def create_payment(value):
    expire = datetime.datetime.now() + datetime.timedelta(days=1)
    expire = expire.strftime("%Y-%m-%dT%-H:%M:%S.000-03:00")

    payment_data = {
        "transaction_amount": int(value),
        "payment_method_id": 'pix',
        "installments": 1,
        "description": 'Descrição',
        "date_of_expiration": f"{expire}",
        "payer": {
            "email": 'email@dominio.xpto'
        }
    }
    result = sdk.payment().create(payment_data)
    return result

@bot.message_handler(commands=['pagar'])
def cmd_pagar(message):
    payment = create_payment(10)
    pix_copia_cola = payment['response']['point_of_interaction']['transaction_data']['qr_code']
    qr_code = payment['response']['point_of_interaction']['transaction_data']['qr_code_base64']
    qr_code = base64.b64decode(qr_code)
    qr_code_img = Image.open(BytesIO(qr_code))
    qrcode_output = qr_code_img.convert('RGB')
    bot.send_photo(message.from_user.id, qrcode_output, f'<code>{pix_copia_cola}</code>', parse_mode='HTML')

if __name__ == "__main__":
    bot.infinity_polling()
