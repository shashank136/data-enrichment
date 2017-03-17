import csv, glob
import requests, os, sys

csv.field_size_limit(sys.maxint)


class MailBoxLayer():
    def __init__(self):
        self.mailboxlayer_keys = ['0eaa85637e28454a8d3da514886aef05',
                                  '394487293b11acb76240b6ed0cb835ec',
                                  '9cb7265fe01d95352b11dbe9b3886562',
                                  'd0755ea283d1e6b8cea6d7ff34e50539',
                                  '2da012b04eef57ab12946ecbd112aa29',
                                  'be350a30f8cae030a4b9c6b952ec98dd',
                                  '59dcddca95be071e23c2dea22acec4e2',
                                  '5f55cf133b45733576985808275e49b8',
                                  '030267187df9a54dd1567ece3922bac3',
                                  '6281eff921beae96733a4754d60fa795',
                                  '9e8a82cb4285e6fc0df0caee069b2953',
                                  '2c5206386a10e6aa81c5163c411a15d5',
                                  '20ad8e198e2e39b7f529031efd3b0a9b',
                                  'b5eab49c30fd9b21013d8bc18a202e5e',
                                  'c28cb83580216ad625c2f880942ff726',
                                  'ac61b4894204a5887b9ed8fcd967f427',
                                  '2ac91f6f812d093b23fc1fd4837a7e4a',
                                  '36b9aec93b5ba88a2f7e9ada9b51b5d5',
                                  '30eba518bde66ebda780bcd3a699f2ec']
        self.mailboxlayer_key_index = 0

    def mailbox_request(self, email):
        if not email:
            return None
        while True:
            url = "https://apilayer.net/api/check?access_key=" + self.mailboxlayer_keys[
                self.mailboxlayer_key_index] + "&email=" + email
            resp = requests.get(url).json()
            if 'error' not in resp:
                return resp['smtp_check']
            if resp['error']['code'] in [101, 104]:
                self.mailboxlayer_key_index = (self.mailboxlayer_key_index + 1) % len(self.mailboxlayer_keys)
                print '\tCHANGING KEY'
                print '\tNEW KEY : ', self.mailboxlayer_keys[self.mailboxlayer_key_index]
            else:
                print '\t## ERROR :', resp['error']['info']
                return None


class Validate:
    def __init__(self):
        self.mb_layer = MailBoxLayer()

    def read_csv(self, file_path, fields, rows):
        with open(file_path, 'rb') as csvFile:
            reader = csv.DictReader(csvFile, dialect=csv.excel)
            fields.extend(reader.fieldnames)
            rows.extend(reader)

    def write_csv(self, file_path, fields, rows):
        with open(file_path, 'wb') as csvFile:
            writer = csv.DictWriter(csvFile, fieldnames=fields)
            writer.writerow(dict(zip(fields, fields)))
            for row in rows:
                writer.writerow(row)

    def multi_idx_delete(self, rows, indexes):
        rev_indexes = sorted(indexes, reverse=True)
        for index in rev_indexes:
            del rows[index]

    def remove_junk(self, rows):
        print "\tInitial Records :", len(rows)
        indexes = []
        sub_count = 0
        for idx, row in enumerate(rows):
            if not self.mb_layer.mailbox_request(row[' Email_id']):
                indexes.append(idx)
                sub_count += 1
                # print row['Mail']
        self.multi_idx_delete(rows, indexes)
        print '\tRemoved :', sub_count
        print '\tFinal Records :', len(rows)

    def main(self):
        files = glob.glob("/home/eduser/shashank/Filtered_email_list/shashank_kumar.csv")
        for file_path in files:
            print file_path
            fields = []
            rows = []
            self.read_csv(file_path, fields, rows)
            self.remove_junk(rows)
            self.write_csv(file_path, fields, rows)
            print '\n'


if __name__ == '__main__':
    v = Validate()
    v.main()
