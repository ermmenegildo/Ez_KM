from flask import Flask, render_template, request, session, redirect, url_for
from traducciones import TEXTOS
from app_data import CLASES, OBJETOS, ITEMS_CURATIVOS
import random, math, json, os

app = Flask(__name__)
app.secret_key = 'super_zombie_rpg_2026'

RANKING_FILE = 'leaderboard.json'

HABILIDADES = {
    'agricultura': {'nombre': 'Botánico', 'desc': 'Permite plantar en el sector actual.', 'coste': 1},
    'fuerza': {'nombre': 'Músculo', 'desc': '+5 Daño base permanente.', 'coste': 1},
    'carroñero': {'nombre': 'Carroñero', 'desc': 'Encuentras más dinero al matar.', 'coste': 1},
    'supervivencia': {'nombre': 'Metabolismo', 'desc': 'El hambre baja más despacio.', 'coste': 1}
}

# --- FUNCIONES DE APOYO ---
def get_refugio(x, y):
    return round(x / 100) * 100, round(y / 100) * 100

def obtener_distrito(x, y):
    dist = math.sqrt(x**2 + y**2)
    if dist < 40: return "Centro Urbano"
    if x > 40: return "Distrito Financiero"
    if x < -40: return "Zona Industrial"
    return "Periferia"

def guardar_puntuacion(nombre, dias, nivel):
    scores = []
    if os.path.exists(RANKING_FILE):
        try:
            with open(RANKING_FILE, 'r', encoding='utf-8') as f:
                scores = json.load(f)
        except:
            scores = []
    scores.append({'nombre': nombre, 'dias': dias, 'lvl': nivel})
    scores = sorted(scores, key=lambda x: x['dias'], reverse=True)[:10]
    with open(RANKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(scores, f, indent=4)

# --- RUTAS DE SISTEMA (IDIOMA Y RANKING) ---

# RUTA BLINDADA PARA EL IDIOMA
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in TEXTOS:
        session['lang'] = lang
    # Si falla el referrer, vuelve al inicio. No más 404.
    return redirect(request.referrer or url_for('index'))

@app.route('/leaderboard')
def leaderboard():
    lang = session.get('lang', 'es')
    scores = []
    if os.path.exists(RANKING_FILE):
        with open(RANKING_FILE, 'r', encoding='utf-8') as f:
            scores = json.load(f)
    return render_template('leaderboard.html', scores=scores, t=TEXTOS[lang])

@app.route('/comprar_habilidad/<hab_id>')
def comprar_habilidad(hab_id):
    p = session.get('p')
    if p and hab_id in HABILIDADES and p['sp'] >= HABILIDADES[hab_id]['coste']:
        if hab_id not in p['skills']:
            p['sp'] -= HABILIDADES[hab_id]['coste']
            p['skills'].append(hab_id)
            if hab_id == 'fuerza': p['dmg_base'] += 5
            p['log'] = f"Habilidad adquirida: {HABILIDADES[hab_id]['nombre']}"
    session.modified = True
    return redirect(url_for('juego'))

# --- RUTAS DE INICIO Y ESTADO ---

@app.route('/')
def index():
    if 'lang' not in session: session['lang'] = 'es'
    return render_template('index.html', t=TEXTOS[session['lang']], clases=CLASES)

@app.route('/iniciar', methods=['POST'])
def iniciar():
    clase_id = request.form.get('clase')
    clase_data = CLASES[clase_id]
    session['p'] = {
        'nombre': request.form.get('nombre', 'Superviviente'),
        'clase': clase_id,
        'hp': clase_data['hp'], 'max_hp': clase_data['hp'],
        'hambre': 100, 'dinero': 50,
        'x': 0, 'y': 0, 'pasos': 0, 'ciclo_pasos': 0, 'dias': 0,
        'lvl': 1, 'exp': 0, 'sp': 0,
        'skills': [], 'inventario': [], 'max_inventario': 5,
        'estados': [], 'dmg_base': 10, 'defensa': 0,
        'enemigo': None, 'mercader': None, 'interaccion': None,
        'pasos_hambre_cero': 0, # Para inanición
        'edificios_mapa': [{'x': random.randint(-40, 40), 'y': random.randint(-40, 40)} for _ in range(12)],
        'enemigos_mapa': [{'x': random.randint(-15, 15), 'y': random.randint(-15, 15)} for _ in range(5)],
        'log': "Sistemas listos. No dejes que el hambre llegue a cero por mucho tiempo."
    }
    return redirect(url_for('juego'))

@app.route('/juego')
def juego():
    p = session.get('p')
    if not p: return redirect(url_for('index'))
    lang = session.get('lang', 'es')
    t_idioma = TEXTOS.get(lang, TEXTOS['es'])
    rx, ry = get_refugio(p['x'], p['y'])
    return render_template('juego.html', p=p, t=t_idioma, 
                           distrito=obtener_distrito(p['x'], p['y']),
                           es_noche=(p['ciclo_pasos'] >= 100),
                           en_refugio=(p['x']==rx and p['y']==ry),
                           habs=HABILIDADES)

@app.route('/mover/<dir>')
def mover(dir):
    p = session.get('p')
    if not p or p.get('enemigo') or p.get('mercader') or p.get('interaccion'): 
        return redirect(url_for('juego'))

    if dir == 'n': p['y'] += 1
    elif dir == 's': p['y'] -= 1
    elif dir == 'e': p['x'] += 1
    elif dir == 'o': p['x'] -= 1
    
    p['pasos'] += 1
    p['ciclo_pasos'] += 1
    
    # --- MUERTE POR INANICIÓN (740 pasos = 3 días y 2 noches) ---
    if p['hambre'] <= 0:
        p['pasos_hambre_cero'] += 1
        if p['pasos_hambre_cero'] >= 740:
            p['hp'] = 0
            p['log'] = "Has muerto por inanición severa."
            return redirect(url_for('morir'))
    else:
        p['pasos_hambre_cero'] = 0

    # Desgaste normal de hambre
    tasa_hambre = 10 if 'supervivencia' in p['skills'] else 6
    if p['pasos'] % tasa_hambre == 0:
        p['hambre'] = max(0, p['hambre'] - 1)
        if p['hambre'] <= 0: p['hp'] -= 3

    # --- IA DE ZOMBIS (PERSIGUEN Y COMBATEN) ---
    for z in p['enemigos_mapa']:
        dist = math.sqrt((z['x'] - p['x'])**2 + (z['y'] - p['y'])**2)
        if dist < 5:
            if z['x'] < p['x']: z['x'] += 1
            elif z['x'] > p['x']: z['x'] -= 1
            if z['y'] < p['y']: z['y'] += 1
            elif z['y'] > p['y']: z['y'] -= 1
        
        if z['x'] == p['x'] and z['y'] == p['y']:
            p['enemigo'] = {'nombre': "Zombi del Mapa", 'hp': 35 + p['lvl']*5, 'atk': 12}
            p['enemigos_mapa'].remove(z)
            p['log'] = "¡Un zombi te ha alcanzado en el mapa!"

    if len(p['enemigos_mapa']) < 5:
        p['enemigos_mapa'].append({'x': p['x'] + random.choice([-8, 8]), 'y': p['y'] + random.choice([-8, 8])})

    # --- EDIFICIOS (Puntos amarillos) ---
    for ed in p['edificios_mapa']:
        if ed['x'] == p['x'] and ed['y'] == p['y']:
            p['interaccion'] = {'tipo': 'edificio', 'msj': "Edificio detectado. ¿Entrar?", 'zombis': random.random() < 0.3}

    if p['hp'] <= 0: return redirect(url_for('morir'))

    if p['ciclo_pasos'] >= 180:
        p['ciclo_pasos'] = 0
        p['dias'] += 1

    session.modified = True
    return redirect(url_for('juego'))

@app.route('/atacar')
def atacar():
    p = session['p']
    if not p.get('enemigo'): return redirect(url_for('juego'))
    dmg = p['dmg_base'] + p['lvl']
    p['enemigo']['hp'] -= dmg
    if p['enemigo']['hp'] <= 0:
        loot = random.randint(5, 15)
        p['dinero'] += int(loot * 1.5) if 'carroñero' in p['skills'] else loot
        p['exp'] += 35
        p['enemigo'] = None
        if p['exp'] >= 100:
            p['lvl'] += 1; p['exp'] %= 100; p['sp'] += 1; p['max_hp'] += 10; p['hp'] = p['max_hp']
    else:
        p['hp'] -= max(1, p['enemigo']['atk'] - p['defensa'])
    if p['hp'] <= 0: return redirect(url_for('morir'))
    session.modified = True
    return redirect(url_for('juego'))

@app.route('/morir')
def morir():
    p = session.get('p')
    if p: guardar_puntuacion(p['nombre'], p['dias'], p['lvl'])
    session.pop('p', None)
    return render_template('muerte.html', t=TEXTOS[session.get('lang', 'es')])

if __name__ == '__main__':
    app.run(debug=True)