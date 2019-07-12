import requests
import re
import json
import time
import random
import os


def capture_spans(s):
    open_iters = re.finditer(r'<span[^>]*>', s)
    open_indexes = [m for m in open_iters]
    close_iters = re.finditer(r'</ *span *>', s)
    close_indexes = [m for m in close_iters]
    if len(close_indexes) != len(open_indexes):
        return s

    s = re.sub(r'<span[^>]*>', '', s)
    s = re.sub(r'</ *span> *', '',  s)
    return s


def get_availability():
    url_main = "https://www.kimsufi.com/es/servidores.xml"
    url_avaliavility = "https://www.ovh.com/engine/api/dedicated/server/availabilities?country=es"
    response = requests.get(url_main)

    if response.status_code != 200:
        return None

    data = response.text
    matches = re.findall(r'<tr[^>]*>(.+?)</tr>', data, flags=re.DOTALL)

    items = []
    for row in matches:
        row = re.sub(r'> +<', '', row)
        row = re.sub(r'^[ \n]+', '', row)
        row = re.sub(r'  +', ' ', row)
        row = re.sub(r'\n', '', row)
        row = re.sub(r'\xa0', ' ', row)
        row = re.sub(r'<br>', '', row)
        cells = re.findall(r'<td[^>]*>(.+?)</ *td *>', row, flags=re.DOTALL)
        cells = [cell for cell in cells]
        #cells = [ re.sub(r'<span[^>]*>(.+?)</span>', r'\1', cell, flags=re.DOTALL) for cell in cells]
        cells = [capture_spans(cell) for cell in cells]
        cells = [re.sub(r'\\[tn]', '', cell) for cell in cells]

        if len(cells) == 11:
            price_without_tax = re.sub(
                r'([,0-9])€.+IVA.+([,0-9]+)€ IVA incl.+', r'\1', cells[8])
            price_with_tax = re.sub(
                r'([,0-9])€.+IVA.+([,0-9]+)€ IVA incl.+', r'\2', cells[8])
            price_without_tax = float(re.sub(r',', '.', price_without_tax))
            price_with_tax = float(re.sub(r',', '.', price_with_tax))

            cells[8] = price_without_tax
            cells.insert(9, price_with_tax)
            cells[10] = re.sub(
                r'.+data-ref="([a-z0-9A-Z]+)".+', r'\1', cells[10])
            items.append({
                'hardware': cells[10],
                'price': cells[9],
                'price_without_tax': cells[8],
            })

    response = requests.get(url_avaliavility)
    
    if response.status_code != 200:
        return None
    
    data = json.loads(response.content)
    parsed_data = list()
    for row in data:
        if row.get('region', None) == 'europe':

            availavility = 'unavailable'
            for datacenter in row.get('datacenters', []):
                if datacenter.get('availability', None) not in [None, 'unavailable']:
                    availavility = datacenter.get('availability', None)

            parsed_data.append({
                'region': row.get('region', None),
                'hardware': row.get('hardware', None),
                'availability': availavility
            })

    for availavility_data in parsed_data:

        item = next(
            (
                item
                for item in items
                if availavility_data.get('hardware') == item.get('hardware', None)
            ),
            None
        )

        if item is not None:
            item['availability'] = availavility_data.get('availability')

    items.sort(key=lambda x: x['hardware'])
    return items


def inform(*args, **kwargs):
    print(*args, **kwargs)
    api_token = os.getenv('API_TOKEN')
    chat_id = os.getenv('CHAT_ID')

    if api_token is not None and chat_id is not None:
        url = 'https://api.telegram.org/bot{}'.format(api_token)
        response = requests.post(
            url + '/sendMessage',
            json={
                'chat_id': chat_id,
                'text': args[0],
                'parse_mode': 'Markdown'
            }
        )
        if response.status_code is not 200:
            print(url)
            print(response.status_code)
            print(response.content)


def main():

    items = get_availability()

    items = {
        item['hardware']: item
        for item in items
    }

    initial_message = 'Kimsufi server prices and availability:\n\n'
    for key, item in items.items():
        initial_message += '\t- {} (*{}e*): `{}`\n'.format(item.get('hardware'),
                                                       item.get('price'), item.get('availability'))
    inform(initial_message)
    while True:
        time.sleep(60 + random.randrange(-5, 5))
        try:
            new_items = get_availability()
            if new_items is not None:
                new_items = {
                    item['hardware']: item
                    for item in new_items
                }

                for key in items:
                    if key not in new_items:
                        inform('Hardware {} ({}e) is not in the list anymore!'.format(
                            key, items.get(key).get('price')))
                    elif new_items[key].get('availability') != items[key].get('availability'):
                        inform('Hardware {} ({}e) has changed its availability from {} to {}'.format(key, new_items.get(
                            key).get('price'), items[key].get('availability'), new_items[key].get('availability')))

                for key in new_items:
                    if key not in items:
                        inform('Hardware {} ({}e) has been added to the list!'.format(
                            key, new_items.get(key).get('price')))

                items = new_items.copy()
        except:
            print('Failed at getting items. Will try it later.')


if __name__ == "__main__":
    main()
