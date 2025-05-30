from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

DB_FILE = 'turnos.json'

SERVICIOS = {
    "Esmaltado permanente": 2,
    "Kapping": 4,
    "Acrílicas": 7,
    "Soft gel": 7,
    "Poli gel": 7,
    "Manicura para varones": 4
}

def cargar_turnos():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def guardar_turnos(turnos):
    with open(DB_FILE, 'w') as f:
        json.dump(turnos, f, indent=4)

def hora_a_minutos(hora):
    h, m = map(int, hora.split(":"))
    return h * 60 + m

def minutos_a_hora(minutos):
    h = minutos // 60
    m = minutos % 60
    return f"{h:02d}:{m:02d}"

def bloques_ocupados(turnos, fecha):
    bloques = set()
    for turno in turnos:
        if turno['fecha'] == fecha:
            duracion = SERVICIOS.get(turno['servicio'], 1)
            inicio = hora_a_minutos(turno['hora'])
            for i in range(duracion):
                bloques.add(inicio + i * 30)
    return bloques

@app.route('/')
def index():
    turnos = cargar_turnos()
    return render_template('index.html', servicios=SERVICIOS.keys(), turnos=turnos)

@app.route('/agendar', methods=['POST'])
def agendar():
    nombre = request.form['nombre']
    fecha = request.form['fecha']
    hora = request.form['hora']
    servicio = request.form['servicio']

    turnos = cargar_turnos()
    nuevos_bloques = set()
    inicio = hora_a_minutos(hora)
    for i in range(SERVICIOS[servicio]):
        nuevos_bloques.add(inicio + i * 30)

    ocupados = bloques_ocupados(turnos, fecha)
    if nuevos_bloques & ocupados:
        return "Turno se superpone con otro", 400

    turnos.append({
        "nombre": nombre,
        "fecha": fecha,
        "hora": hora,
        "servicio": servicio
    })
    guardar_turnos(turnos)
    return redirect('/')

@app.route('/eliminar', methods=['POST'])
def eliminar():
    fecha = request.form['fecha']
    hora = request.form['hora']
    turnos = cargar_turnos()
    turnos = [t for t in turnos if not (t['fecha'] == fecha and t['hora'] == hora)]
    guardar_turnos(turnos)
    return redirect('/')

@app.route('/ver_disponibilidad')
def ver_disponibilidad():
    fecha = request.args.get('fecha')
    turnos = cargar_turnos()
    ocupados = bloques_ocupados(turnos, fecha)
    bloques = []
    inicio = hora_a_minutos("09:00")
    fin = hora_a_minutos("20:00")
    for t in range(inicio, fin, 30):
        estado = "ocupado" if t in ocupados else "libre"
        bloques.append({"hora": minutos_a_hora(t), "estado": estado})
    return jsonify(bloques)

if __name__ == '__main__':
    app.run(debug=True)