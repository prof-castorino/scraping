from requests_html import HTMLSession
import json
session = HTMLSession()


class App:

    def __init__(self, products, url):
        self.product = {}
        self.payload = {}
        self.run(products, url)

    def run(self, products, url):
        for id_product in products:
            try:
                print(f'---------------  start {id_product} --------------- ')
                page = session.get(f'{url}{id_product}')
                self.find_in_scripts(page.html.find("script"), id_product)
                print(f'--------------- exit {id_product} --------------- ')
            except OSError as err:
                print(f'{id_product} - Start - error: {err}')

    def find_in_scripts(self, scripts, id_product):
        try:
            for script in scripts:
                # scraping products
                if 'application/ld+json' in script.html:
                    print(f'-- {id_product} scraping products  -- ')
                    ld = script.text.replace('2" Octa', '2` Octa')
                    self.products(json.loads(ld), id_product)
                # scraping sellers
                if '__PRELOADED_STATE__' in script.text:
                    print(f'-- {id_product} scraping sellers -- ')
                    data = script.text.replace(
                        'window.__PRELOADED_STATE__ = ', '').replace('};', '}').strip()
                    data = json.loads(data.replace(':undefined', ':""'))
                    self.seller(data['entities']['offers']
                                [id_product], id_product)
        except OSError as err:
            print(f'{id_product} - Find in scripts - error: ',
                  sys.exc_info()[0])

    def seller(self, offers, id_product):
        for index, offer in enumerate(offers):
            try:
                id_seller = offer["_embedded"]["seller"]["id"]
                print(f'-- process seller - {id_seller}')
                origem = 'buybox'
                if offer['_embedded']['seller']['name'] == 'B2W':
                    origem = 'ecommerce'
                seller = self.product[id_product].copy()
                # check options payments
                boleto, payment = self.payments(
                    offer['paymentOptions'], id_seller, id_product)
                seller.update({
                    'Vendedor': offer['_embedded']['seller']['name'],
                    'Preco Por': offer['salesPrice'],
                    'Preco Boleto ou A vista': boleto,
                    'Opções a prazo': payment,
                    'Origem': origem,
                    'Ranking': index
                })
                self.payload.update({id_product+id_seller: seller})
            except OSError as err:
                print(
                    f'-- {id_product} - item {index} - Seller - error: {err}')

    def payments(self, payments, id_seller, id_product, options={}, boleto=''):
        try:
            for payment in payments:
                print(f'-- {id_product}{id_seller} - process payment {payment}')
                if payment == 'BOLETO':
                    boleto = payments[payment]['price']
                    continue
                else:
                    options[payment] = self.installments(
                        payments[payment]['installments'], id_product, id_seller)
        except OSError as err:
            print(
                f'-- {id_product}{id_seller} - Payments - error: {err}')

        return boleto, options

    def installments(self, installments, id_product, id_seller, parcelas={}):
        try:
            for index, installment in enumerate(installments):
                taxed = 'sem juros'
                if installment['interestRate'] != 0:
                    taxed = 'com juros'
                parcelas.update({index: {
                    'Quantidade de Parcelas': index,
                    'Valor Parcela': installment['value'],
                    'Preco Prazo': installment['total'],
                    'Taxa de Juros': taxed
                }})

            return {
                'Quantidade de parcela': len(installments),
                'Parcelas': parcelas
            }
        except OSError as err:
            print(
                f'-- {id_product}{id_seller} - Installments - error: {err}')
            return {}

    def products(self, data, id_product, product={}):
        try:
            print(f'-- process products {id_product}')
            for item in data['@graph']:
                if item['@type'] == 'BreadcrumbList':
                    department = self.department(item, id_product)
                if item['@type'] == 'Product':
                    product = self.hydrator_product(
                        item, department, id_product)
        except OSError as err:
            print(f'-- {id_product} - Products - error: {err}')
        self.product.update({id_product: product})

    def department(self, item, id_product, department=[]):
        try:
            for item_list in item['itemListElement']:
                department.append(item_list['item']['name'])
        except OSError as err:
            print(f'-- {id_product} - Department - error: {err}')
        return department

    def hydrator_product(self, item, department, id_product, product={}):
        try:
            product = {
                "Nome": item['name'],
                "Url": item['url'],
                "Imagem": item['image'],
                "Categoria": item['category'],
                "Departamento": department
            }
            if 'lowPrice' in item['offers'].keys():
                product["Preco De"] = item['offers']['lowPrice']
        except OSError as err:
            print(
                f'-- {id_product} - Hydrator Product - error: {err}')
        return product


if __name__ == '__main__':

    # 134253960 Smartphone Samsung Galaxy A10 32GB Dual Chip Android 9.0 Tela 6.2" Octa-Core 4G Câmera 13MP – Preto
    # 122262105 Parafusad/Furad 1447 GSR 7-14E 127V Cabo
    run = App(
        ['134253960', '122262105'],
        'https://www.americanas.com.br/produto/'
    )
    print('-- Create file dados.json')
    with open('dados.json', 'w') as json_file:
        json.dump(run.payload, json_file, indent=4)
