# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import re
import logging
import psycopg2

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from scrapy.exceptions import DropItem
from scrapy import signals

from tenderchad_scraper.settings import DATABASE_NAME, DATABASE_PASSWORD, DATABASE_USER, DATABASE_HOST, AWS_DOCS_FOLDER, AWS_DOCS
from tenderchad_scraper.database import PostgresConnection 


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
                price = price.replace(',', '.')
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
            if (datetime.strptime(item['date_placed'], "%d.%m.%Y") < (datetime.now() - timedelta(days=60))) and (item['stage'] == 'Подача заявок' or 'Работа комиссии'):
                item['stage'] = 'Закупка отменена'
            
        return item
    
class FullpageClearDataPipeline:
    def process_item(self, item, spider):
        if item.get('law') is not None:
            item['law'] = item['law'].strip()

        if item.get('law') == '223-ФЗ' and item.get('supplier_extended') == "Прочие":
            item['supplier'] = 'Прочие'

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
            if not item.get('supplier_extended'):
                item['supplier_extended'] = item['supplier']

        if not item.get('supplier_extended'):
            if item.get('supplier'):
                item['supplier_extended'] = item['supplier']

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
            item['deadline'] = "-1"

        if item.get('date_summing_up') is not None:
            item['date_summing_up'] = item['date_summing_up'].strip()
            try:
                if deadline_date_str := re.search(r'\d+\.\d+\.\d+', item['deadline']).group(0):
                    date_format = "%d.%m.%Y"
                    deadline_date = datetime.strptime(deadline_date_str, date_format)
                    summing_date = datetime.strptime(item['date_summing_up'], date_format)
                    item['deadline'] = (deadline_date - summing_date).days
            except:
                item['deadline'] = -1

        else:
            item['date_summing_up'] = ""
            
        if item.get('contract_enforcement') is not None and type(item.get('contract_enforcement')) is not int:
            contract_enforcement = item['contract_enforcement'].strip().replace(u'\xa0', '')

            item['contract_enforcement'] = 0
            found_ce = False
            try:
                contract_enforcement_match = re.findall(r'\d+\s?%', contract_enforcement)
                contract_enforcement_match = contract_enforcement_match[0]
                item['contract_enforcement'] = re.findall(r'\d+', contract_enforcement_match)[0]

                found_ce = True
            except:
                pass

            try:
                if not found_ce:
                    contract_enforcement_match = re.findall(r'[0-9\s?\.,?]+', contract_enforcement)[0]
                    contract_enforcement = contract_enforcement.replace(',', '.').replace(' ', '')
                    ce_percent = float(contract_enforcement_match) / float (item['price']) * 100
                    item['contract_enforcement'] = ce_percent

            except:
                pass


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


class PostgresPipeline:

    def __init__(self):
        
        self.connection = PostgresConnection()._instance.connection
        
        ## Create cursor, used to execute commands
        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        
        self.cursor.close()

    def process_item(self, item, spider):
        try:
            # retrieve tender
            self.cursor.execute("SELECT * FROM parser_script_tender WHERE number = %s", (item["number"],))
            existing_item = self.cursor.fetchone()
            
            # get law id
            self.cursor.execute("SELECT id FROM parser_script_federallaw WHERE name = %s", (item["law"],))
            law_id = self.cursor.fetchone()
            logging.warning(f'law_id: {law_id}')

            # get purchase stage id
            if stage_name := item.get('stage'):
                if stage_name == 'Определение поставщика завершено':
                    stage_name = 'Закупка завершена'
                if stage_name == 'Определение поставщика отменено':
                    stage_name = 'Закупка отменена'

                logging.warning(f'stage: {stage_name}')

                self.cursor.execute("SELECT id FROM parser_script_purchasestage WHERE name = %s", (stage_name,))
                stage_id = self.cursor.fetchone()
                logging.warning(f'stage_id: {stage_id}')

            # get supplier definition
            self.cursor.execute("SELECT id, alt_name FROM parser_script_supplierdefinition")
            supplier_alt_names =  [(r[0], r[1]) for r in self.cursor.fetchall()]

            for id, alt_name in supplier_alt_names:
                if alt_name.lower() in item["supplier"].lower():
                    supplier_id = id
                    item['supplier_extended'] = item["supplier"]
                    break
                elif not item.get("supplier") and item.get("supplier_extended") and alt_name.lower() in item["supplier_extended"].lower():
                    item['supplier'] = alt_name
                    supplier_id = id
                    break

            logging.warning(f'supplier: {item["supplier"]}')
            logging.warning(f'supplier_extended: {item["supplier_extended"]}')
            logging.warning(f'supplier_id: {supplier_id}')

            if existing_item:
                logging.warning('in database')
            else:
                logging.warning('insert triggered')
                # If item doesn't exist, insert it
                insert_query = 'INSERT INTO parser_script_tender (number, name, customer_name, platform_name, "platform_URL", price, placement_date, end_date, federal_law_id, purchase_stage_id, supplier_definition_id, supplier_definition_extended, percentage_application_security, deadline) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id'
                self.cursor.execute(insert_query, (item["number"], item["description"], item["customer"], item["platform"], item["platform_url"], item["price"], item['date_placed'], item['date_end'], law_id, stage_id, supplier_id, item['supplier_extended'] or "", item['contract_enforcement'], item['deadline']))
                item_id = self.cursor.fetchone()[0]

                try:
                    for title in item['all_attached_files']:

                        tender_document_query = "SELECT id FROM parser_script_tenderdocument WHERE title = %s AND tender_id = %s"
                        self.cursor.execute(tender_document_query, (title, item_id))
                        tender_document_id = self.cursor.fetchone()

                        if not tender_document_id:
                            insert_tender_document_query = "INSERT INTO parser_script_tenderdocument (title, document, tender_id) VALUES (%s, %s, %s)" 
                            document_path = AWS_DOCS + item['number'] + '/' + title
                            self.cursor.execute(insert_tender_document_query, (title, document_path, item_id))
 
                except Exception as e:
                    raise Exception(f'Exception in saving files: {e}')
                
                self.connection.commit()
            

        except Exception as e:
            self.connection.rollback()
            raise DropItem(f"Failed to process item {item['number']}: {e}")
        

        return item
    

class SaveStagePipeline:

    def __init__(self):
        self.connection = PostgresConnection()._instance.connection
        
        ## Create cursor, used to execute commands
        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        
        self.cursor.close()
        self.connection.close()

    def process_item(self, item, spider):
        try:
            # retrieve tender
            self.cursor.execute("SELECT * FROM parser_script_tender WHERE number = %s", (item["number"],))
            existing_item = self.cursor.fetchone()

            # get purchase stage id
            if stage_name := item.get('stage'):
                if stage_name == 'Определение поставщика завершено':
                    stage_name = 'Закупка завершена'
                if stage_name == 'Определение поставщика отменено':
                    stage_name = 'Закупка отменена'

                logging.warning(f'stage: {stage_name}')

                self.cursor.execute("SELECT id FROM parser_script_purchasestage WHERE name = %s", (stage_name,))
                stage_id = self.cursor.fetchone()
                logging.warning(f'stage_id: {stage_id}')

            if existing_item:
                logging.warning('update triggered')
                item_id = existing_item[0]
                # If item exists, update it
                update_query = 'UPDATE parser_script_tender SET purchase_stage_id = %s WHERE number = %s'
                self.cursor.execute(update_query, (stage_id, item["number"]))

            self.connection.commit()
            
        except Exception as e:
            self.connection.rollback()
            raise DropItem(f"Failed to process item: {e}")
        
        return item