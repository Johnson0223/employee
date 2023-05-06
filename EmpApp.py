from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')

@app.route("/employees", methods=['GET'])
def employees():
    select_sql = "SELECT * FROM employee"
    cursor = db_conn.cursor()
    cursor.execute(select_sql)
    results = cursor.fetchall()

    s3 = boto3.resource('s3')

    table_html = "<table class='emp_list'><tr><th>Employee ID</th><th>Name</th><th>IC No</th><th>Primary Skill</th><th>Address</th><th>Pay Scale</th><th>Employee Image</th></tr>"
    for result in results:
        emp_id = result[0]
        fname = result[1]
        ic = result[2]
        email = result[3]
        address = result[4]
        payscale = result[5]
        emp_image_url = s3.generate_presigned_url('get_object', Params={'Bucket': custombucket, 'Key': 'emp-id-' + str(emp_id) + '_image_file'})

        table_html += "<tr><td>{}</td><td>{}</td><td><img src='{}' width='100'></td></tr>".format(emp_id, fname, ic, email, address, payscale, emp_image_url)

    table_html += "</table>"

    cursor.close()

    return render_template('info.html', table_html=table_html)

@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    fname = request.form['fname']
    ic = request.form['ic']
    email = request.form['email']
    location = request.form['location']
    payscale = request.form['payscale']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        cursor.execute(insert_sql, (emp_id, fname, ic, email, location, payscale))
        db_conn.commit()
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)
            
            js = '''
            <script>
            alert("Employee added successfully!");
            </script>
            '''

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return js

@app.route('/findemp', methods=['POST'])
def find_employee():
    emp_id = request.form['emp_id']

    select_sql = "SELECT * FROM employee WHERE emp_id = %s"
    cursor = db_conn.cursor()
    cursor.execute(select_sql, (emp_id,))
    result = cursor.fetchone()

    if result:
        # Employee found, populate form fields with employee details
        return render_template('update_employee.html', result=result)
    else:
        # Employee not found
        return render_template('employee_not_found.html')


@app.route("/rmvemp", methods=['POST'])
def RmvEmp():
    emp_id = request.form['emp_id']

    select_sql = "SELECT * FROM employee WHERE emp_id=%s"
    cursor = db_conn.cursor()
    cursor.execute(select_sql, (emp_id,))
    result = cursor.fetchone()

    emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
    s3 = boto3.resource('s3')

    if result is None:
        return "Employee not found"

    try:
        delete_sql = "DELETE FROM employee WHERE emp_id=%s"
        cursor.execute(delete_sql, (emp_id,))
        db_conn.commit()
        emp_name = result[1]

        s3.delete_object(Bucket=custombucket, Key=emp_image_file_name_in_s3)
    finally:
        cursor.close()

    print("Employee removed from database")
    return "Employee " + emp_name + " removed successfully"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

