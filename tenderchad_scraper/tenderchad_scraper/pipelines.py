# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import re
import logging

from datetime import datetime, timedelta


class TenderchadScraperPipeline:
    def process_item(self, item, spider):
        return item

class HeaderClearDataPipeline:
    def process_item(self, item, spider):
        if item['number'] is not None:
            if number := re.findall(r'\d+', item['number']):
                item['number'] = number[0]

        if item['price'] is not None:
            price = item['price']
            if price is list:
                price = price[0]
            try:
                price = price.strip()
            except Exception:
                pass
            try:
                price = price.replace(u'\xa0', u'').replace(" ", "")
            except Exception:
                pass

            try:
                price = re.search(r'[\d.,]+', price).group(0)
            except Exception:
                pass

            item['price'] = price

        if item['stage'] is not None:
            item['stage'] = item['stage'].strip()


        # if tender was placed two months ago and still on submission
        if (item['date_placed'] is not None) and (item['stage'] is not None):
            if (datetime.strptime(item['date_placed'], "%d.%m.%Y") < (datetime.now() - timedelta(days=60))) and (item['stage'] == 'Подача заявок'):
                item['stage'] = 'Закупка отменена'
            
        return item
    

class FullpageClearDataPipeline:
    def process_item(self, item, spider):
        if item.get('law') is not None:
            item['law'] = item['law'].strip()

        if item.get('supplier') is not None:
            item['supplier'] = item['supplier'].strip()
        else:
            item['supplier'] = ""

        if item.get('law_and_supplier') is not None:
            law_and_supplier = item['law_and_supplier'].split()
            law = law_and_supplier[0]
            supplier = " ".join(law_and_supplier[1:])
            item['law'] = law
            item['supplier'] = supplier

        if item.get('description') is not None:
            item['description'] = item['description'].strip()
        else:
            item['description'] = ""

        if item.get('customer') is not None:
            item['customer'] = item['customer'].strip()
        else:
            item['customer'] = ""

        if item.get('platform') is not None:
            item['platform'] = item['platform'].strip()
        else:
            item['platform'] = ""

        if item.get('platform_url') is not None:
            item['platform_url'] = item['platform_url'].strip()
        else:
            item['platform_url'] = ""
        
        if item.get('deadline') is not None:
            item['deadline'] = item['deadline'].strip()

            try:
                item['deadline'] = re.search(r'\d+\.\d+\.\d+', item['deadline']).group(0)
            except Exception:
                try:
                    item['deadline'] = re.search(r'\d+', item['deadline']).group(0)
                except Exception:
                    pass

                pass
        else:
            item['deadline'] = ""

        if item.get('date_summing_up') is not None:
            item['date_summing_up'] = item['date_summing_up'].strip()
        else:
            item['date_summing_up'] = ""
            
        if item.get('contract_enforcement') is not None and type(item.get('contract_enforcement')) is not int:
            contract_enforcement = item['contract_enforcement'].strip().replace(u'\xa0', '')
            contract_enforcement = re.findall(r'\d+', contract_enforcement)
            item['contract_enforcement'] = contract_enforcement[0]

        else: 
            item['contract_enforcement'] = 0

        return item
    
class DocsClearDataPipeline:

    def process_item(self, item, spider):

        if item.get('all_attached_files') is not None:
            docs = item.get('all_attached_files')
            flat_docs = self.flatten_and_remove_empty(docs)

            logging.warning(flat_docs)
            
            item['all_attached_files'] = flat_docs

        return item

    def flatten_and_remove_empty(self, input_list):
        result = []
        for item in input_list:
            if isinstance(item, list):
                # Recursively flatten the nested list
                result.extend(self.flatten_and_remove_empty(item))
            elif item:  # Only add non-empty elements
                result.append(item)
        return result