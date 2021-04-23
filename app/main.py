"""The Flask App."""

# pylint: disable=broad-except

from flask import Flask, abort, jsonify, request
from rq.job import Job

from .functions import predict_func
from .redis_resc import redis_conn, redis_queue
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Admin123'
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)

@app.errorhandler(404)
def resource_not_found(exception):
    return jsonify(error=str(exception)), 404


@app.route("/")
def home():
    
    return "App Home"


@app.route("/enqueue", methods=["POST", "GET"])
def enqueue():
    if request.method == "GET":
        query_param = request.args.get("image_data")
        if not query_param:
            abort(
                404,
                description=(
                    "No query parameter external_id passed. "
                    "Send a value to the external_id query parameter."
                ),
            )
        data = {"external_id": query_param}
    if request.method == "POST":
        data = request.get_json(force=True)
        print(data)

    job = redis_queue.enqueue(predict_func, data,result_ttl=100)
    return jsonify({"job_id": job.id})


@app.route("/check_status")
def check_status():
    job_id = request.args["job_id"]
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception as exception:
        abort(404, description=exception)

    return jsonify({"job_id": job.id, "job_status": job.get_status()})


@app.route("/get_result")
def get_result():
    """Takes a job_id and returns the job's result."""
    job_id = request.args["job_id"]
    result = {}
    job = None
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        result = job.result
        print(job.result)
    except Exception as exception:
        cur = mysql.connection.cursor()
        cur.execute("select * from results where job_id like '{}'".format(job_id))
        rv = cur.fetchall()
        print(rv[0])
        print(jsonify(rv[0]))
        result = rv[0]
    if not result:
        abort(
            404,
            description=f"No result found for job_id {job.id}. Try checking the job's status.",
        )
    return jsonify(result)

@app.route("/get_all_results",methods=["GET"])
def get_all_results():
    cur = mysql.connection.cursor()
    cur.execute('''select * from results''')
    rv = cur.fetchall()
    print(rv)
    return jsonify(rv)

@app.route("/get_hosp_list", methods=["GET"])
def get_hosp_list():
    return jsonify({"data":["a","b","c","d"]})

@app.route("/get_details", methods=["GET"])
def get_details():
    cur = mysql.connection.cursor()
    cur.execute("select * from diseases")
    rv = cur.fetchall()
    return jsonify({"data": rv})


    


if __name__ == "__main__":
    app.run(debug=True)
