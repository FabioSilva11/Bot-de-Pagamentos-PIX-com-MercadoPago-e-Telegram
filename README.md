# Bot-de-Pagamentos-PIX-com-MercadoPago-e-Telegram

O uso da API é dividido em duas partes:

## Cobrança
A cobrança é gerada e seu resultado é um código PIX do tipo copia e cola, com valor e validade definidos. Não é possível que o cliente altere qualquer um deles. A validade padrão é de um dia, mas pode ser alterada como demonstrado nos próximos passos.

Para ser gerada uma cobrança é obrigatório o fornecimento de um endereço de e-mail do cliente. Este endereço tem por principal finalidade o envio da cobrança e do comprovante para a pessoa. Para facilitar o uso do bot, sugiro colocar um endereço de e-mail fixo, fazendo com que não seja necessário o fornecimento do dado. O lado negativo desta abordagem é que a pessoa fica restrita a fazer o pagamento pelo bot, não sendo possível ter uma cópia consigo. Ou seja, o modelo de negócio que vai definir a exigência ou não do email da pessoa.

## Pagamento
A cobrança fica pendente até que seja atingida a sua validade ou que seja paga. A parte que gera a cobrança é totalmente separada da verificação. Recomendo ter duas instâncias separadas, uma para o bot e outra apenas para verificações. A cobrança é paga quando seu estado é alterado para approved. Enquanto aguarda o pagamento, o estado é pending. Caso não seja paga, a cobrança terá o estado cancelled ao ser atingida a data de validade.

## Requisitos
- Ter uma conta no Mercado Pago;
- Obter um token de acesso no painel de credenciais;
- Ter uma chave PIX para receber pagamentos cadastrada em sua conta.

## Instalação
Instale a biblioteca oficial do Mercado Pago para utilizar a cobrança via PIX.

```bash
pip install mercadopago
```

Opcionalmente, caso queira gerar a imagem do QRCode, é recomendável instalar também a biblioteca Pillow.

```bash
pip install Pillow
```

## Uso
### Cobrança simples
O script abaixo gera uma cobrança de valor definido na variável valor.

```python
import mercadopago

sdk = mercadopago.SDK(TOKEN)

payment_data = {
    "transaction_amount": valor,
    "description": "descrição",
    "payment_method_id": 'pix',
    "installments": 1,
    "payer": {
        "email": 'email_do_cliente@dominio.xpto'
    }
}
result = sdk.payment().create(payment_data)
print(result['response'])
```

- `transaction_amount`: Valor a ser cobrado;
- `description`: Descrição;
- `payment_method_id`: (Não alterar) Método de pagamento;
- `installments`: (Não alterar) Número de parcelas;
- `payer`:
  - `email`: E-mail do cliente/pagador.

### Cobrança com validade
Abaixo, um script que gera cobrança com validade igual a 30 minutos:

```python
import datetime
import mercadopago

sdk = mercadopago.SDK(TOKEN)

expire = datetime.datetime.now() + datetime.timedelta(minutes=30)
expire = expire.strftime("%Y-%m-%dT%-H:%M:%S.000-03:00")

payment_data = {
    "date_of_expiration": f"{expire}",
    "transaction_amount": valor,
    "description": "descrição",
    "payment_method_id": 'pix',
    "installments": 1,
    "payer": {
        "email": 'email_do_cliente@dominio.xpto'
    }
}
result = sdk.payment().create(payment_data)
print(result['response'])
```

- `date_of_expiration`: Data de validade. Padrão: 1 dia. Formato obrigatório: yyyy-MM-dd'T'HH:mm:ssz

### Resposta
Para fins de simplificação, apenas alguns items da resposta serão tratados aqui. Consulte a lista completa na documentação oficial.

Usando-se qualquer um dos códigos anteriores,

```python
pix_copia_cola = result['response']['point_of_interaction']['transaction_data']['qr_code']
qr_code = result['response']['point_of_interaction']['transaction_data']['qr_code_base64']
```

- `pix_copia_cola`: Valor a ser colado no PIX para ser feito o pagamento já com o valor fixado;
- `qr_code`: QRCode correspondente ao pix copia e cola em base64.

Ou seja, com o pix_copia_cola já é possível fazer o pagamento. A imagem contida em qr_code pode ser usada também. Mais abaixo é demonstrado como ela pode ser enviada.

### Lista cobranças
Para verificar todas as cobranças em sua conta, independente do estado e listadas na ordem em que foram geradas, utilize:

```python
import mercadopago

sdk = mercadopago.SDK(TOKEN_MERCADOPAGO)

payments = sdk.payment().search({'sort':'date_created', 'criteria': 'desc'})

for payment in payments['response']['results']:
    print(payment['id'], payment['status'], payment['description'], payment['date_of_expiration'])
```

### Verifica estado
Uma cobrança de ID específico pode ser verificada usando:

```python
import mercadopago

sdk = mercadopago.SDK(TOKEN_MERCADOPAGO)

result = sdk.payment().get(ID_DO_PAGAMENTO)
payment = result["response"]

print(payment['status'], payment['description'])
```

### Bot
#### Envia PIX Copia e Cola
Este bot irá enviar uma cobrança no valor de R$ 10  para a pessoa que enviar o comando /pagar.

```python
import datetime
import mercadopago
import telebot

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
   

 bot.send_message(message.from_user.id, f'<code>{pix_copia_cola}</code>', parse_mode='HTML')

if __name__ == "__main__":
    bot.infinity_polling()
```

#### Envia QRCode
Semelhante ao exemplo anterior, este bot envia uma cobrança para o usuário que enviar /pagar. A resposta será a imagem do QRCode com o PIX Copia e Cola como legenda.

```python
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
```

### Taxas
Na data em que o texto foi escrito havia uma cobrança de 0.99% por pagamento. Consulte o site oficial para obter informações atualizadas.
