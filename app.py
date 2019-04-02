from flask import Flask, request, render_template, send_from_directory, g
from werkzeug import secure_filename
import os,json, zipfile, random, string
import sqlite3

DATABASE = './db/database.db'
UPLOAD_FOLDER = './uploads'
DOWNLOAD_FOLDER = './results'
ALLOWED_EXTENSIONS = set(['png', 'zip'])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
conn = sqlite3.connect('db/database.db')
conn.execute('CREATE TABLE IF NOT EXISTS models (ID INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, scheduling_detail TEXT, deployed_by TEXT, path TEXT, status TEXT)')
conn.close()


@app.route('/')
def index():
    return render_template('index.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def add_record(model_name, scheduling_detail, user, path):
    print(model_name, scheduling_detail, user, path)
    #try:
    con = get_db()
    cur = con.cursor()
    cur.execute("INSERT INTO models (name, scheduling_detail, deployed_by, path, status) VALUES(?, ?, ?, ?, ?)",
                (model_name, scheduling_detail, user, path, 'INIT'))
    con.commit()



def store_zip_file(model_file, filename):
    username = "admin"
    rand_dir_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    path_to_store_unzip_files = os.path.join(app.config['UPLOAD_FOLDER'], username, rand_dir_name)

    temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp')
    model_file.save(os.path.join(temp_dir, filename))
    #unzip file and store
    print(path_to_store_unzip_files)
    if not os.path.exists(path_to_store_unzip_files):
        os.makedirs(path_to_store_unzip_files)
        zip_ref = zipfile.ZipFile(os.path.join(temp_dir, filename), 'r')
        zip_ref.extractall(path_to_store_unzip_files)
        zip_ref.close()

        config = open(os.path.join(path_to_store_unzip_files, 'config.json'), 'r')
        config_json = json.loads(config.read())
        model_detail_list = config_json['ModelList']
        for eachModel in model_detail_list:
            add_record(eachModel['Modelname'], json.dumps(eachModel), username, path_to_store_unzip_files)

    else:
        print("directory exists")


@app.route('/deploy', methods=['GET', 'POST'])
def deploy():
    if request.method == 'GET':
        return "Bad Request"
    else:

        if 'model_file' not in request.files:
            return "No model_file file uploaded"

        model_file = request.files['model_file']

        if model_file.filename == '':
            return "No model_file selected file"

        if model_file and allowed_file(model_file.filename):
            filename = secure_filename(model_file.filename)
            store_zip_file(model_file, filename)
            # model_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print(filename)

        return render_template('index.html')

    return "404"


@app.route('/downloadresult/<filename>', methods=['GET'])
def download_result(filename=None):
    if filename is None:
        return "Please provide file name"
    else:
        return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)
    return "404 ERROR"


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


if __name__ == '__main__':
    app.run(debug=True)
