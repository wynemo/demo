import csv
import datetime
import os.path
import os
import time
import uuid

import faker

# Define the table schema
table_schema = [
    'id', 'sessionrid', 'clientuid', 'clientuser', 'clientname', 'clientip',
    'serveruid', 'serveruser', 'serverhid', 'serverip', 'servername',
    'serverappid', 'eventtime', 'eventtype', 'sessiontype', 'sessionproto',
    'sessionversion', 'eventid', 'departmentid', 'sqlprocesstime', 'sqltype',
    'sqllen', 'sqltext', 'affecttable', 'affecttables', 'isautocmd',
    'sqlresult', 'statuscode', 'execresult', 'affectrows', 'auditrows',
    'dbname', 'appname', 'loglevel', 'action', 'acl', 'acltag', 'nodeid',
    'datekey'
]

f = faker.Faker()

# Sample data for the CSV file
sample_data = [2, 'session1', 123, 'client1', 'John Doe', '192.168.0.1',
    456, 'server1', 789, '192.168.0.2', 'Server Name',
    101, 1631568000, 1, 2, 3,
    '1.0', 1001, 987, 100, 200,
    20, f.text(), 'table1', 1, 1,
    1, 0, 'Executed successfully', 10, 5,
    'database1', 'app1', 2, 1, 'acl1', '{}', 'node1',
    '2023-09-13']


# Function to generate the CSV file
def generate_csv(filename, data):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(table_schema)  # Write the header row
        writer.writerow(data)  # Write the data rows

# Generate the CSV file
# generate_csv('sql_data.csv', sample_data)


if __name__ == "__main__":
    now_date = datetime.datetime.now().date()
    # 6亿数据
    days = 600
    day_count = 1000 * 1000
    count = 30
    step = int(days/count)
    i, write_total = 0, days * day_count
    batch_size = 1000

    for each in range(0, days, step):
        _path = f'data_{each}.csv'
        if os.path.exists(_path + '.gz'):
            print(_path, 'exsist')
            i += step * day_count
            continue
        with open(_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(table_schema)  # Write the header row
            for day in range(each, each + step):
                write_date = now_date - datetime.timedelta(days=day)
                write_ts = time.mktime(write_date.timetuple())
                for index in range(day_count):
                    event_time = int(write_ts * 1000)
                    datekey = write_date
                    # 填写uuid4的字段用于标记不同的数据
                    session_rid = uuid.uuid4().hex + str(index)
                    client_name = uuid.uuid4().hex
                    sample_data[12] = event_time
                    sample_data[-1] = datekey
                    sample_data[4] = client_name
                    sample_data[1] = session_rid
                    sample_data[0] = i
                    sample_data[22] = f.text()
                    writer.writerow(sample_data)
                    i += 1
                    if i % batch_size == 0:
                        print(
                            "\rwrite process: {:.2%}".format(i / write_total),
                            end="",
                            flush=True,
                        )
                        
        os.system(f'gzip {_path}')
