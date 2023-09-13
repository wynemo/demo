import csv
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
sample_data = [
    (2, 'session1', 123, 'client1', 'John Doe', '192.168.0.1',
     456, 'server1', 789, '192.168.0.2', 'Server Name',
     101, 1631568000, 1, 2, 3,
     '1.0', 1001, 987, 100, 200,
     20, f.text(), 'table1', 1, 1,
     1, 0, 'Executed successfully', 10, 5,
     'database1', 'app1', 2, 1, 'acl1', '{}', 'node1',
     '2023-09-13')
]

# Function to generate the CSV file
def generate_csv(filename, data):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(table_schema)  # Write the header row
        writer.writerows(data)  # Write the data rows

# Generate the CSV file
generate_csv('sql_data.csv', sample_data)