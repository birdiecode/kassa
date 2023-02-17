#  It was written by Birdiecode in 2022.
import os
import re
import time

import bcrypt
from flask import Flask, render_template, session, redirect, url_for, request
from flaskext.mysql import MySQL

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = os.getenv('DATABASE_USER')
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('DATABASE_PASSWORD')
app.config['MYSQL_DATABASE_DB'] = os.getenv('DATABASE_DB')
app.config['MYSQL_DATABASE_HOST'] = os.getenv('DATABASE_HOST')
mysql.init_app(app)

lang_serch_pars = r'([a-zA-Z]+):\"([^\"]+)\"'

def parse_search(s):
    if s == '':
        return ''
    result = re.findall(lang_serch_pars, s)
    all_search = re.sub(lang_serch_pars, '', s).strip()
    search_arg = {
        "contrnum": all_search,
        "name": all_search,
        "lastname": all_search,
        "macadress": all_search,
        "ip": all_search,
        "phone": all_search,
        "email": all_search,
        "address": all_search,
        "id": all_search
    }
    for rs in result:
        try:
            search_arg[rs[0]] = rs[1]
        except Exception:
            pass

    for key in search_arg.copy():
        if search_arg[key] == '':
            search_arg.pop(key)
    return "WHERE " + ' or '.join([key + " like \"%" + search_arg[key] + "%\"" for key in search_arg])


@app.template_filter('ctime')
def timectime(s):
    return time.ctime(s)


def parse_search_2(options, s):
    opr = options.copy()
    if s == '':
        return '', []

    result = re.findall(lang_serch_pars, s)
    all_search = re.sub(lang_serch_pars, '', s).strip()
    erf = {}
    for resf in result:
        opr.remove(resf[0])
        erf[resf[0]] = resf[1]

    exeins = []
    erfk = " WHERE"
    for gh in erf.keys():
        exeins.append("%" + erf[gh] + "%")
        erfk += " " + gh + ' LIKE %s AND'

    erfk += " ("
    for oprf in opr:
        exeins.append("%" + all_search + "%")
        erfk += " " + oprf + ' LIKE %s'

        if oprf != opr[-1]:
            erfk += " OR"

    erfk += " )"
    return erfk, exeins


@app.route('/user/add', methods=['POST'])
def r_user_add():
    if not 'userid' in session:
        return redirect(url_for('r_login'))

    mys = mysql.get_db()
    cursor = mys.cursor()

    sql = "INSERT INTO quotes.`user` (macadress,ip,contrnum,idTariff,login,pass,name,lastname,gender,phone,email,address,birthdate,timeAdd,comment,pass1) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    try:
        val = (
            request.form.get('nu_macadress', "DEFAULT"),
            request.form.get('nu_ip'),
            request.form.get('nu_contrnum'),
            request.form.get('nu_tariff_old', None),
            request.form.get('login', ''),
            request.form.get('passwd', ''),
            request.form.get('nu_name'),
            request.form.get('nu_lastname'),
            request.form.get('nu_gender'),
            request.form.get('nu_phone'),
            request.form.get('nu_email'),
            request.form.get('nu_address'),
            int(request.form.get('nu_birthdate')),
            int(time.time()),
            request.form.get('nu_comment'),
            request.form.get('passwd', ''))
        cursor.execute(sql, val)
        mys.commit()
    except Exception as e:
        return str(e)

    return redirect(url_for('r_index'))


@app.route('/transactions/add', methods=['POST'])
def r_transactions_add():
    if not 'userid' in session:
        return redirect(url_for('r_login'))

    mys = mysql.get_db()
    cursor = mys.cursor()

    sql = "INSERT INTO quotes.`transact` (idUser,type,name,pay,timeadd,status,comment) VALUES (%s,%s,%s,%s,%s,%s,%s)"
    uid = dict()
    for f in re.findall(lang_serch_pars, session['tsearch']):
        uid[f[0]] = f[1]

    if not 'iduser' in uid:
        return "no select user"

    try:
        val = (
            uid['iduser'],
            request.form.get('nu_type'),
            request.form.get('nu_name'),
            float(request.form.get('nu_pay')),
            int(time.time()),
            int(request.form.get('nu_status')),
            request.form.get('nu_comment'))
        cursor.execute(sql, val)
        mys.commit()
    except Exception as e:
        return str(e)

    return redirect(url_for('r_transactions'))


@app.route('/transactions')
def r_transactions():
    if not 'userid' in session:
        return redirect(url_for('r_login'))

    linecount = int(request.args.get('lines', session.get('tlines', 15)))
    pagenum = int(request.args.get('page', session.get('tpage', 1)))
    search = request.args.get('search', session.get('tsearch', ''))

    session['tpage'] = pagenum
    session['tlines'] = linecount
    session['tsearch'] = search

    cursor = mysql.get_db().cursor()

    searchexe, exeval = parse_search_2(['iduser', 'type', 'name', 'pay', 'timeadd', 'comment'], search)
    print(searchexe, exeval)
    cursor.execute("SELECT COUNT(*) FROM transact " + searchexe, exeval)
    usercount = int(cursor.fetchone()[0])

    usersinfo = None
    for par in re.findall(lang_serch_pars, search):
        if par[0] == 'iduser':
            cursor.execute(
                "SELECT contrnum, name, lastname FROM `user` WHERE id = %s;", [par[1]])
            userinf = cursor.fetchone()
            usersinfo = str(userinf[1]) + " " + str(userinf[2]) + " (Договор " + str(userinf[0]) + ")"
            break

    cursor.execute(
        "SELECT * FROM transact" + searchexe + " ORDER BY timeAdd DESC LIMIT " + str(
            linecount * (pagenum - 1)) + ", " + str(linecount * pagenum) + ";", exeval)
    transacline = cursor.fetchall()
    cursor.close()

    pc = int(usercount / linecount)
    pc += 1 if (usercount) % linecount > 0 else 0

    nu_types = ["яндекс деньги", "оплата услуг"]
    nu_status = [{"id": 0, "name": "проводка прошла"}, {"id": 1, "name": "проводка в ожидании"}, {"id": 1, "name": "ошибка проводки"}]
    return render_template('transactions.html', linecount=linecount, pagenum=pagenum, pagecount=pc,
                           transacline=transacline, searchtext=search, userinfo=usersinfo, nu_types=nu_types,
                           nu_status=nu_status)



@app.route('/')
def r_index():
    if not 'userid' in session:
        return redirect(url_for('r_login'))

    linecount = int(request.args.get('lines', session.get('lines', 15)))
    pagenum = int(request.args.get('page', session.get('page', 1)))
    search = request.args.get('search', session.get('search', ''))

    session['page'] = pagenum
    session['lines'] = linecount
    session['search'] = search

    searchexe = parse_search(search)

    cursor = mysql.get_db().cursor()
    cursor.execute("SELECT COUNT(*) FROM `user` " + searchexe)
    usercount = int(cursor.fetchone()[0])

    cursor.execute(
        "SELECT contrnum, name, lastname, macadress, ip, phone, email, address, id FROM `user`" + searchexe + " ORDER BY id DESC LIMIT " + str(
            linecount * (pagenum - 1)) + ", " + str(linecount * pagenum) + ";")
    userrow = cursor.fetchall()
    cursor.close()

    tariff = ["test min", "test oldfag", "test testov"]

    pc = int(usercount / linecount)
    pc += 1 if (usercount) % linecount > 0 else 0

    return render_template('users.html', linecount=linecount, pagenum=pagenum, pagecount=pc, userrow=userrow,
                           searchtext=search, tariffes=tariff)



@app.route('/login', methods=['GET', 'POST'])
def r_login():
    if 'userid' in session:
       return redirect(url_for('r_index'))

    if request.method == 'POST':
        form_nickname = request.form.get('username', '')
        form_password = request.form.get('password', '')

        if form_nickname != '' and form_password != '':
            cursor = mysql.get_db().cursor()
            cursor.execute("SELECT id, password FROM admins WHERE nickname = %s;", [form_nickname])
            data = cursor.fetchone()
            cursor.close()
            if data is not None and bcrypt.checkpw(form_password.encode(), data[1].encode()):
                session['userid'] = data[0]
                return redirect(url_for('r_index'))

        return render_template('login.html', errout=True)

    return render_template('login.html', errout=False)


@app.route('/logout')
def r_logout():
    session.pop('userid', None)
    session.pop('lines', None)
    session.pop('page', None)
    session.pop('search', None)
    session.pop('tlines', None)
    session.pop('tpage', None)
    session.pop('tsearch', None)
    return redirect(url_for('r_login'))


if __name__ == '__main__':
    app.run()
