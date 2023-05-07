@app.route("/updateEmp", methods=['POST'])
def updateEmp():
    data = request.form
    emp_id = data['emp_id']
    fname = data['fname']
    ic = data['ic']
    email = data['email']
    location = data['location']
    payscale = data['payscale']
    emp_image_file = request.files.get('emp_image_file')  # Get the uploaded image file

    # Update employee details in the database
    update_sql = "UPDATE info SET fname = %s, ic = %s, email = %s, location = %s, payscale = %s WHERE emp_id = %s"
    cursor = db_conn.cursor()
    try:
        cursor.execute(update_sql, (fname, ic, email, location, payscale, emp_id))
        db_conn.commit()

        if emp_image_file:
            # Uplaod image file in S3 #
            emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
            s3 = boto3.resource('s3')

            try:
                print("Data updated in MySQL RDS... uploading image to S3...")
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
                alert("Employee data and image updated successfully!");
                </script>
                '''

            except Exception as e:
                return jsonify({'error': str(e)})

        else:
            js = '''
            <script>
            alert("Employee data updated successfully!");
            </script>
            '''

    except Exception as e:
        return jsonify({'error': str(e)})

    return jsonify({'status': 'success', 'message': js})
