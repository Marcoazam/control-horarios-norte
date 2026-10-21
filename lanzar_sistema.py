import http.server
import socketserver
import sqlite3
import json
import webbrowser
import threading
import csv
import io
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import os
PORT = int(os.environ.get("PORT", 8080))
DB_FILE = "horarios_centro.db"
ADMIN_PASSWORD = "admin123"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            horario TEXT,
            p1_alumno TEXT, p1_estado TEXT, p1_prof TEXT, p1_bloqueado INTEGER,
            p2_alumno TEXT, p2_estado TEXT, p2_prof TEXT, p2_bloqueado INTEGER,
            p3_alumno TEXT, p3_estado TEXT, p3_prof TEXT, p3_bloqueado INTEGER,
            p4_alumno TEXT, p4_estado TEXT, p4_prof TEXT, p4_bloqueado INTEGER,
            p5_alumno TEXT, p5_estado TEXT, p5_prof TEXT, p5_bloqueado INTEGER,
            p6_alumno TEXT, p6_estado TEXT, p6_prof TEXT, p6_bloqueado INTEGER,
            p7_alumno TEXT, p7_estado TEXT, p7_prof TEXT, p7_bloqueado INTEGER
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM horarios")
    if cursor.fetchone()[0] == 0:
        hoy = datetime.now().strftime("%Y-%m-%d")
        datos = [
            (hoy, "09:00 - 10:00", 
             "", "NORMAL", "1", 0, "", "NORMAL", "2", 0, "", "NORMAL", "3", 0, "", "NORMAL", "4", 0, "", "NORMAL", "5", 0, "", "NORMAL", "6", 0, "", "NORMAL", "7", 0),
            (hoy, "10:00 - 10:00", 
             "", "NORMAL", "1", 0, "", "NORMAL", "2", 0, "", "NORMAL", "3", 0, "", "NORMAL", "4", 0, "", "NORMAL", "5", 0, "", "NORMAL", "6", 0, "", "NORMAL", "7", 0),
            (hoy, "11:00 - 12:00", 
             "", "NORMAL", "1", 0, "", "NORMAL", "2", 0, "", "NORMAL", "3", 0, "", "NORMAL", "4", 0, "", "NORMAL", "5", 0, "", "NORMAL", "6", 0, "", "NORMAL", "7", 0),
            (hoy, "12:00 - 13:00", 
             "", "NORMAL", "1", 0, "", "NORMAL", "2", 0, "", "NORMAL", "3", 0, "", "NORMAL", "4", 0, "", "NORMAL", "5", 0, "", "NORMAL", "6", 0, "", "NORMAL", "7", 0),
            (hoy, "15:00 - 16:00", 
             "", "NORMAL", "1", 0, "", "NORMAL", "2", 0, "", "NORMAL", "3", 0, "", "NORMAL", "4", 0, "", "NORMAL", "5", 0, "", "NORMAL", "6", 0, "", "NORMAL", "7", 0),
            (hoy, "16:00 - 17:00", 
             "", "NORMAL", "1", 0, "", "NORMAL", "2", 0, "", "NORMAL", "3", 0, "", "NORMAL", "4", 0, "", "NORMAL", "5", 0, "", "NORMAL", "6", 0, "", "NORMAL", "7", 0),
            (hoy, "17:00 - 18:00", 
             "", "NORMAL", "1", 0, "", "NORMAL", "2", 0, "", "NORMAL", "3", 0, "", "NORMAL", "4", 0, "", "NORMAL", "5", 0, "", "NORMAL", "6", 0, "", "NORMAL", "7", 0),
            (hoy, "18:00 - 19:00", 
             "", "NORMAL", "1", 0, "", "NORMAL", "2", 0, "", "NORMAL", "3", 0, "", "NORMAL", "4", 0, "", "NORMAL", "5", 0, "", "NORMAL", "6", 0, "", "NORMAL", "7", 0),
            (hoy, "19:00 - 20:00", 
             "", "NORMAL", "1", 0, "", "NORMAL", "2", 0, "", "NORMAL", "3", 0, "", "NORMAL", "4", 0, "", "NORMAL", "5", 0, "", "NORMAL", "6", 0, "", "NORMAL", "7", 0),
        ]
        cursor.executemany('''
            INSERT INTO horarios (
                fecha, horario, 
                p1_alumno, p1_estado, p1_prof, p1_bloqueado,
                p2_alumno, p2_estado, p2_prof, p2_bloqueado,
                p3_alumno, p3_estado, p3_prof, p3_bloqueado,
                p4_alumno, p4_estado, p4_prof, p4_bloqueado,
                p5_alumno, p5_estado, p5_prof, p5_bloqueado,
                p6_alumno, p6_estado, p6_prof, p6_bloqueado,
                p7_alumno, p7_estado, p7_prof, p7_bloqueado
            ) VALUES (?, ?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?)
        ''', datos)
        conn.commit()
    conn.close()

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>ASSD Asesores | Control de Horarios y Clases (7 Espacios)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body class="bg-gray-100 min-h-screen font-sans" x-data="app()">
    <header class="bg-indigo-900 text-white shadow-lg">
        <div class="max-w-[95%] mx-auto px-4 py-4 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-bold">ASSD Asesores | Control de Horarios (7 Alumnos por Horario)</h1>
                <p class="text-xs text-indigo-200">Independencia Total por Espacio y Calendario</p>
            </div>
            <div class="flex items-center gap-4">
                <div class="text-sm bg-indigo-800 px-3 py-1.5 rounded-lg border border-indigo-700">
                    Rol: <span class="font-bold uppercase text-yellow-300" x-text="isAdmin ? 'Administrador / Direccion' : 'Alumno / Usuario'"></span>
                </div>
                <button @click="toggleAdminMode()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg text-sm font-semibold transition">
                    <span x-text="isAdmin ? 'Cerrar Sesion Admin' : 'Acceso Admin'"></span>
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-[95%] mx-auto px-4 py-6">
        <div x-show="notification.show" :class="notification.success ? 'bg-green-100 border-green-400 text-green-700' : 'bg-red-100 border-red-400 text-red-700'" class="border px-4 py-3 rounded relative mb-4 shadow-sm flex justify-between items-center transition">
            <span x-text="notification.msg"></span>
            <button @click="notification.show = false" class="font-bold">&times;</button>
        </div>

        <div class="bg-white rounded-xl shadow-sm p-4 mb-6 flex flex-wrap justify-between items-center gap-4">
            <div class="flex items-center gap-3">
                <label class="text-sm font-semibold text-gray-700">Seleccionar Fecha:</label>
                <input type="date" x-model="fechaSeleccionada" @change="cargarDatos()" class="border rounded-lg px-3 py-1.5 text-sm bg-gray-50 focus:ring-2 focus:ring-indigo-500 font-semibold text-indigo-900">
            </div>
            <div class="flex items-center gap-3 flex-wrap">
                <template x-if="isAdmin">
                    <div class="flex gap-2 items-center flex-wrap">
                        <button @click="crearHorariosDia()" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-3 py-2 rounded-lg font-bold shadow transition">
                            + Plantilla Dia
                        </button>
                        <button @click="crearHorariosSemana()" class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-2 rounded-lg font-bold shadow transition">
                            + Plantilla Semana
                        </button>
                        <label class="bg-amber-600 hover:bg-amber-700 text-white text-xs px-3 py-2 rounded-lg font-bold shadow transition cursor-pointer flex items-center gap-1">
                            📁 Subir Excel/CSV Mensual
                            <input type="file" accept=".csv" @change="subirExcel($event)" class="hidden">
                        </label>
                    </div>
                </template>
                <div class="flex items-center gap-4 text-xs text-gray-600">
                    <span class="flex items-center gap-1.5"><span class="w-3 h-3 bg-red-100 border border-red-300 rounded-full inline-block"></span> Ocupado / Bloqueado</span>
                    <span class="flex items-center gap-1.5"><span class="w-3 h-3 bg-green-100 border border-green-300 rounded-full inline-block"></span> Libre</span>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 text-xs">
                    <thead class="bg-gray-50 text-gray-700 uppercase font-semibold text-center">
                        <tr>
                            <th class="px-3 py-3 border-r">Horario</th>
                            <!-- Repetido para P1 a P7 -->
                            <template x-for="p in [1,2,3,4,5,6,7]">
                                <th class="px-2 py-3 border-r bg-indigo-50/50" colspan="4" x-text="'Espacio ' + p"></th>
                            </template>
                            <th class="px-3 py-3 bg-gray-100">Accion</th>
                        </tr>
                        <tr class="bg-gray-100 text-[10px] text-gray-600">
                            <th class="border-r"></th>
                            <template x-for="p in [1,2,3,4,5,6,7]">
                                <template x-init="">
                                    <span style="display:none"></span>
                                </template>
                            </template>
                            <!-- Subcolumnas repetidas 7 veces -->
                            <template x-for="p in [1,2,3,4,5,6,7]">
                                <>
                                    <th class="px-1 py-2 border-r bg-gray-50">Alumno</th>
                                    <th class="px-1 py-2 border-r bg-gray-50">Estado</th>
                                    <th class="px-1 py-2 border-r bg-gray-50">Prof</th>
                                    <th class="px-1 py-2 border-r bg-gray-50">Bloq</th>
                                </>
                            </template>
                            <th class="px-2 py-2 bg-gray-50">Guardar</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 bg-white">
                        <template x-for="item in registros" :key="item.id">
                            <tr class="hover:bg-gray-50 transition text-center">
                                <td class="px-3 py-3 border-r font-semibold text-indigo-600 whitespace-nowrap" x-text="item.horario"></td>
                                
                                <!-- Generación dinámica de celdas P1 a P7 con Alpine -->
                                <template x-for="p in [1,2,3,4,5,6,7]">
                                    <tr style="display:contents">
                                        <!-- Alumno -->
                                        <td class="px-1 py-2 border-r">
                                            <input type="text" x-model="item['p' + p + '_alumno']" 
                                                :disabled="!isAdmin && (item['p' + p + '_bloqueado'] == 1 || item['p' + p + '_original'] !== '')" 
                                                placeholder="Libre" 
                                                :class="!isAdmin && item['p' + p + '_original'] !== '' ? 'bg-gray-100 text-gray-500 font-bold text-[11px]' : 'bg-white text-gray-800 border-indigo-200 text-[11px]'"
                                                class="w-28 border rounded px-1.5 py-1">
                                        </td>
                                        <!-- Estado -->
                                        <td class="px-1 py-2 border-r">
                                            <select x-model="item['p' + p + '_estado']" :disabled="!isAdmin && (item['p' + p + '_bloqueado'] == 1 || item['p' + p + '_original'] !== '')" class="border rounded px-1 py-1 text-[10px] bg-white disabled:bg-gray-100">
                                                <option value="NORMAL">NORMAL</option>
                                                <option value="REPOSICION">REP</option>
                                                <option value="CANCELADO">CANC</option>
                                            </select>
                                        </td>
                                        <!-- Prof -->
                                        <td class="px-1 py-2 border-r">
                                            <input type="text" x-model="item['p' + p + '_prof']" :disabled="!isAdmin" class="w-8 text-center border rounded bg-white disabled:bg-gray-100 text-[11px]">
                                        </td>
                                        <!-- Bloqueado -->
                                        <td class="px-1 py-2 border-r">
                                            <input type="checkbox" :checked="item['p' + p + '_bloqueado'] == 1" @change="item['p' + p + '_bloqueado'] = $event.target.checked ? 1 : 0" :disabled="!isAdmin" class="rounded text-indigo-600">
                                        </td>
                                    </tr>
                                </template>

                                <!-- Botón Guardar por Fila -->
                                <td class="px-2 py-2 bg-gray-50 align-middle">
                                    <button @click="guardarFila(item)" class="bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] px-2 py-1.5 rounded shadow transition font-bold">
                                        Guardar
                                    </button>
                                </td>
                            </tr>
                        </template>
                        <template x-if="registros.length === 0">
                            <tr>
                                <td colspan="30" class="text-center py-8 text-gray-500">
                                    No hay horarios configurados para esta fecha. 
                                    <span x-show="isAdmin" class="block text-xs text-indigo-600 mt-1">Usa los botones superiores para generar plantillas o subir tu archivo mensual.</span>
                                </td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <script>
        function app() {
            return {
                isAdmin: false,
                fechaSeleccionada: new Date().toISOString().split('T')[0],
                registros: [],
                notification: { show: false, msg: '', success: true },
                init() {
                    this.cargarDatos();
                },
                cargarDatos() {
                    fetch('/api/get?fecha=' + encodeURIComponent(this.fechaSeleccionada))
                        .then(res => res.json())
                        .then(data => { 
                            this.registros = data.map(r => {
                                let obj = { ...r };
                                for(let i=1; i<=7; i++) {
                                    obj['p' + i + '_original'] = r['p' + i + '_alumno'] || '';
                                }
                                return obj;
                            }); 
                        });
                },
                crearHorariosDia() {
                    fetch('/api/init_day', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ fecha: this.fechaSeleccionada })
                    })
                    .then(res => res.json())
                    .then(res => {
                        this.notification.msg = res.message;
                        this.notification.success = res.success;
                        this.notification.show = true;
                        this.cargarDatos();
                        setTimeout(() => this.notification.show = false, 4000);
                    });
                },
                crearHorariosSemana() {
                    fetch('/api/init_week', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ fecha: this.fechaSeleccionada })
                    })
                    .then(res => res.json())
                    .then(res => {
                        this.notification.msg = res.message;
                        this.notification.success = res.success;
                        this.notification.show = true;
                        this.cargarDatos();
                        setTimeout(() => this.notification.show = false, 4000);
                    });
                },
                subirExcel(event) {
                    const file = event.target.files[0];
                    if (!file) return;

                    const reader = new FileReader();
                    reader.onload = (e) => {
                        const csvContent = e.target.result;
                        fetch('/api/upload_csv', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ csvData: csvContent })
                        })
                        .then(res => res.json())
                        .then(res => {
                            this.notification.msg = res.message;
                            this.notification.success = res.success;
                            this.notification.show = true;
                            this.cargarDatos();
                            event.target.value = '';
                            setTimeout(() => this.notification.show = false, 5000);
                        });
                    };
                    reader.readAsText(file, 'utf-8');
                },
                toggleAdminMode() {
                    if (this.isAdmin) {
                        this.isAdmin = false;
                        this.notification = { show: true, msg: 'Sesion de administrador cerrada.', success: true };
                        setTimeout(() => this.notification.show = false, 3000);
                    } else {
                        let pwd = prompt("Ingrese la contrasena de Administrador:");
                        if (pwd !== null) {
                            fetch('/api/login', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ password: pwd })
                            })
                            .then(res => res.json())
                            .then(res => {
                                if (res.success) {
                                    this.isAdmin = true;
                                }
                                this.notification.msg = res.message;
                                this.notification.success = res.success;
                                this.notification.show = true;
                                setTimeout(() => this.notification.show = false, 4000);
                            });
                        }
                    }
                },
                guardarFila(item) {
                    fetch('/api/update', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ item: item, isAdmin: this.isAdmin })
                    })
                    .then(res => res.json())
                    .then(res => {
                        this.notification.msg = res.message;
                        this.notification.success = res.success;
                        this.notification.show = true;
                        this.cargarDatos();
                        setTimeout(() => this.notification.show = false, 4000);
                    });
                }
            }
        }
    </script>
</body>
</html>
"""

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif parsed.path == '/api/get':
            query = parse_qs(parsed.query)
            fecha = query.get('fecha', [datetime.now().strftime("%Y-%m-%d")])[0]
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM horarios WHERE fecha = ? ORDER BY horario ASC", (fecha,))
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(rows).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            if data.get('password') == ADMIN_PASSWORD:
                response = {"success": True, "message": "Acceso concedido como Administrador!"}
            else:
                response = {"success": False, "message": "Contrasena incorrecta."}
            self.send_json(response)
            
        elif parsed.path == '/api/init_day':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            fecha = data.get('fecha')
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM horarios WHERE fecha = ?", (fecha,))
            if cursor.fetchone()[0] == 0:
                bloques = [
                    "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00", "12:00 - 13:00",
                    "15:00 - 16:00", "16:00 - 17:00", "17:00 - 18:00", "18:00 - 19:00", "19:00 - 20:00"
                ]
                for b in bloques:
                    cursor.execute('''
                        INSERT INTO horarios (
                            fecha, horario, 
                            p1_alumno, p1_estado, p1_prof, p1_bloqueado,
                            p2_alumno, p2_estado, p2_prof, p2_bloqueado,
                            p3_alumno, p3_estado, p3_prof, p3_bloqueado,
                            p4_alumno, p4_estado, p4_prof, p4_bloqueado,
                            p5_alumno, p5_estado, p5_prof, p5_bloqueado,
                            p6_alumno, p6_estado, p6_prof, p6_bloqueado,
                            p7_alumno, p7_estado, p7_prof, p7_bloqueado
                        ) VALUES (?, ?, '', 'NORMAL', '1', 0, '', 'NORMAL', '2', 0, '', 'NORMAL', '3', 0, '', 'NORMAL', '4', 0, '', 'NORMAL', '5', 0, '', 'NORMAL', '6', 0, '', 'NORMAL', '7', 0)
                    ''', (fecha, b))
                conn.commit()
                msg = "Plantilla de horarios (7 espacios) generada para este dia."
                success = True
            else:
                msg = "Este dia ya cuenta con horarios registrados."
                success = False
            conn.close()
            self.send_json({"success": success, "message": msg})

        elif parsed.path == '/api/init_week':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            fecha_str = data.get('fecha')
            
            try:
                fecha_base = datetime.strptime(fecha_str, "%Y-%m-%d")
            except:
                fecha_base = datetime.now()
                
            lunes = fecha_base - timedelta(days=fecha_base.weekday())
            bloques = [
                "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00", "12:00 - 13:00",
                "15:00 - 16:00", "16:00 - 17:00", "17:00 - 18:00", "18:00 - 19:00", "19:00 - 20:00"
            ]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            dias_agregados = 0
            
            for i in range(7):
                dia_actual = (lunes + timedelta(days=i)).strftime("%Y-%m-%d")
                cursor.execute("SELECT COUNT(*) FROM horarios WHERE fecha = ?", (dia_actual,))
                if cursor.fetchone()[0] == 0:
                    for b in bloques:
                        cursor.execute('''
                            INSERT INTO horarios (
                                fecha, horario, 
                                p1_alumno, p1_estado, p1_prof, p1_bloqueado,
                                p2_alumno, p2_estado, p2_prof, p2_bloqueado,
                                p3_alumno, p3_estado, p3_prof, p3_bloqueado,
                                p4_alumno, p4_estado, p4_prof, p4_bloqueado,
                                p5_alumno, p5_estado, p5_prof, p5_bloqueado,
                                p6_alumno, p6_estado, p6_prof, p6_bloqueado,
                                p7_alumno, p7_estado, p7_prof, p7_bloqueado
                            ) VALUES (?, ?, '', 'NORMAL', '1', 0, '', 'NORMAL', '2', 0, '', 'NORMAL', '3', 0, '', 'NORMAL', '4', 0, '', 'NORMAL', '5', 0, '', 'NORMAL', '6', 0, '', 'NORMAL', '7', 0)
                        ''', (dia_actual, b))
                    dias_agregados += 1
                    
            conn.commit()
            conn.close()
            
            if dias_agregados > 0:
                self.send_json({"success": True, "message": f"Plantilla generada para toda la semana ({dias_agregados} dias)."})
            else:
                self.send_json({"success": False, "message": "Los dias de esta semana ya contaban con registros."})

        elif parsed.path == '/api/upload_csv':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            csv_text = data.get('csvData', '')
            
            try:
                f = io.StringIO(csv_text)
                reader = csv.DictReader(f)
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                count = 0
                for row in reader:
                    fecha = row.get('fecha', '').strip()
                    horario = row.get('horario', '').strip()
                    if not fecha or not horario:
                        continue
                    
                    vals = [fecha, horario]
                    cols_sql = "fecha, horario"
                    placeholders = "?, ?"
                    
                    for i in range(1, 8):
                        alu = row.get(f'p{i}_alumno', '').strip()
                        est = row.get(f'p{i}_estado', 'NORMAL').strip()
                        prf = row.get(f'p{i}_prof', str(i)).strip()
                        blo = int(row.get(f'p{i}_bloqueado', 0) or 0)
                        vals.extend([alu, est, prf, blo])
                        cols_sql += f", p{i}_alumno, p{i}_estado, p{i}_prof, p{i}_bloqueado"
                        placeholders += ", ?, ?, ?, ?"

                    cursor.execute("SELECT id FROM horarios WHERE fecha = ? AND horario = ?", (fecha, horario))
                    existe = cursor.fetchone()
                    
                    if existe:
                        set_clause = ", ".join([f"p{i}_alumno = ?, p{i}_estado = ?, p{i}_prof = ?, p{i}_bloqueado = ?" for i in range(1, 8)])
                        update_vals = []
                        for i in range(1, 8):
                            update_vals.extend([
                                row.get(f'p{i}_alumno', '').strip(),
                                row.get(f'p{i}_estado', 'NORMAL').strip(),
                                row.get(f'p{i}_prof', str(i)).strip(),
                                int(row.get(f'p{i}_bloqueado', 0) or 0)
                            ])
                        update_vals.append(existe[0])
                        cursor.execute(f"UPDATE horarios SET {set_clause} WHERE id = ?", update_vals)
                    else:
                        cursor.execute(f"INSERT INTO horarios ({cols_sql}) VALUES ({placeholders})", vals)
                    count += 1
                    
                conn.commit()
                conn.close()
                self.send_json({"success": True, "message": f"Archivo procesado con exito! {count} registros actualizados."})
            except Exception as ex:
                self.send_json({"success": False, "message": f"Error al procesar el archivo CSV."})

        elif parsed.path == '/api/update':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            item = data['item']
            is_admin = data['isAdmin']
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Consultar originales para validar bloqueos de los 7 espacios
            sel_cols = ", ".join([f"p{i}_alumno, p{i}_bloqueado" for i in range(1, 8)])
            cursor.execute(f"SELECT {sel_cols} FROM horarios WHERE id = ?", (item['id'],))
            orig = cursor.fetchone()
            if not orig:
                conn.close()
                self.send_json({"success": False, "message": "Registro no encontrado."})
                return
                
            update_vals = []
            set_clauses = []
            
            for i in range(1, 8):
                orig_alu = orig[(i-1)*2] or ""
                orig_bloq = orig[(i-1)*2 + 1]
                
                nuevo_alu = (item.get(f'p{i}_alumno') or '').strip()
                
                if is_admin:
                    bloq_final = item[f'p{i}_bloqueado']
                else:
                    bloq_final = orig_bloq
                    if orig_bloq == 1 or orig_alu != "":
                        if nuevo_alu != orig_alu:
                            conn.close()
                            self.send_json({"success": False, "message": f"Operacion denegada: El espacio {i} ya esta ocupado."})
                            return
                    else:
                        if nuevo_alu != "":
                            bloq_final = 1
                
                set_clauses.append(f"p{i}_alumno = ?, p{i}_estado = ?, p{i}_prof = ?, p{i}_bloqueado = ?")
                update_vals.extend([nuevo_alu, item[f'p{i}_estado'], item[f'p{i}_prof'], bloq_final])
                
            update_vals.append(item['id'])
            sql = f"UPDATE horarios SET {', '.join(set_clauses)} WHERE id = ?"
            
            cursor.execute(sql, update_vals)
            conn.commit()
            conn.close()
            
            self.send_json({"success": True, "message": "Horarios guardados y bloqueados con exito!"})

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        return

if __name__ == '__main__':
    # Borrar base de datos vieja si existía con estructura de 2 columnas para recrearla limpia con 7 espacios
    # (Opcional: Si prefieres conservar datos viejos, comenta la siguiente línea o bórrala manualmente)
    # import os; if os.path.exists(DB_FILE): os.remove(DB_FILE)
    
    init_db()
    print(f"Servidor iniciado en http://localhost:{PORT}")
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
   with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
    print(f"Servidor iniciado en puerto {PORT}")
    httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")