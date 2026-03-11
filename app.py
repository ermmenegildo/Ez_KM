from flask import Flask, render_template, request, session, redirect, url_for
from traducciones import TEXTOS
from app_data import CLASES, OBJETOS, ITEMS_CURATIVOS
import random, math

app = Flask(__name__)
app.secret_key = 'super_zombie_rpg_2026'

# --- CONFIGURACIÓN DE HABILIDADES ---
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
        'skills': [], 
        'inventario': [],  # NUEVO: Lista de mochila
        'max_inventario': 5,
        'estados': [], 
        'dmg_base': 10, 'defensa': 0,
        'enemigo': None, 'mercader': None,
        'log': "Sistemas listos. El hambre aprieta, busca comida."
    }
    return redirect(url_for('juego'))

@app.route('/juego')
def juego():
    p = session.get('p')
    if not p: return redirect(url_for('index'))
    
    lang = session.get('lang', 'es')
    t_idioma = TEXTOS.get(lang, TEXTOS['es'])
    rx, ry = get_refugio(p['x'], p['y'])
    
    return render_template('juego.html', 
                           p=p, 
                           t=t_idioma, 
                           distrito=obtener_distrito(p['x'], p['y']),
                           es_noche=(p['ciclo_pasos'] >= 100),
                           en_refugio=(p['x']==rx and p['y']==ry),
                           habs=HABILIDADES)

# --- MOVIMIENTO Y EVENTOS ---
@app.route('/mover/<dir>')
def mover(dir):
    p = session.get('p')
    if not p or p.get('enemigo') or p.get('mercader'): return redirect(url_for('juego'))

    if dir == 'n': p['y'] += 1
    elif dir == 's': p['y'] -= 1
    elif dir == 'e': p['x'] += 1
    elif dir == 'o': p['x'] -= 1
    
    p['pasos'] += 1
    p['ciclo_pasos'] += 1
    
    if 'herida_abierta' in p['estados']:
        p['hp'] -= 4
        p['log'] = "SANGRE DETECTADA. El movimiento empeora la herida."

    dist_total = math.sqrt(p['x']**2 + p['y']**2)
    if dist_total > 80:
        if 'irradiado' not in p['estados']:
            p['estados'].append('irradiado')
            p['log'] = "¡ALERTA RADIACIÓN! Niveles críticos en este sector."
    
    if 'irradiado' in p['estados']:
        p['hp'] -= 2
        if p['pasos'] % 5 == 0: p['max_hp'] = max(10, p['max_hp'] - 1)

    tasa_hambre = 10 if 'supervivencia' in p['skills'] else 6
    if p['pasos'] % tasa_hambre == 0:
        p['hambre'] = max(0, p['hambre'] - 1)
        if p['hambre'] <= 0: p['hp'] -= 3

    if p['hp'] <= 0: return redirect(url_for('morir'))

    if p['ciclo_pasos'] >= 180:
        p['ciclo_pasos'] = 0
        p['dias'] += 1

    rand = random.random()
    if rand < 0.05:
        p['mercader'] = {
            'items': {'Botiquín': 40, 'Comida': 20, 'Vendas': 15},
            'oferta': random.choice(['Botiquín', 'Comida', 'Vendas'])
        }
    elif rand < 0.25:
        dist = abs(p['x']) + abs(p['y'])
        es_noche = p['ciclo_pasos'] >= 100
        mult = 1.5 if es_noche else 1.0
        p['enemigo'] = {
            'nombre': "Acechador" if es_noche else "Infectado",
            'hp': int((20 + dist) * mult),
            'atk': int((10 + dist//2) * mult)
        }
    
    session.modified = True
    return redirect(url_for('juego'))

# --- SISTEMA DE INVENTARIO (NUEVO) ---
@app.route('/comprar')
def comprar():
    p = session['p']
    item = p['mercader']['oferta']
    precio = p['mercader']['items'][item]
    
    if p['dinero'] >= precio:
        if len(p['inventario']) < p['max_inventario']:
            p['dinero'] -= precio
            p['inventario'].append(item)
            p['log'] = f"Comprado: {item}. Guardado en mochila."
            p['mercader'] = None
        else:
            p['log'] = "Mochila llena. No puedes comprar más."
    
    session.modified = True
    return redirect(url_for('juego'))

@app.route('/usar/<int:idx>')
def usar(idx):
    p = session['p']
    if 0 <= idx < len(p['inventario']):
        item = p['inventario'].pop(idx)
        if item == 'Comida':
            p['hambre'] = min(100, p['hambre'] + 40)
            p['log'] = "Has comido. +40 Nutrición."
        elif item in ['Botiquín', 'Vendas']:
            p['hp'] = min(p['max_hp'], p['hp'] + 50)
            if 'herida_abierta' in p['estados']: p['estados'].remove('herida_abierta')
            p['log'] = f"Has usado {item}. +50 HP y hemorragia detenida."
    
    session.modified = True
    return redirect(url_for('juego'))

# --- COMBATE, CURACIÓN Y OTROS ---
@app.route('/atacar')
def atacar():
    p = session['p']
    if not p.get('enemigo'): return redirect(url_for('juego'))
    
    dmg = p['dmg_base'] + p['lvl']
    p['enemigo']['hp'] -= dmg
    
    if p['enemigo']['hp'] <= 0:
        loot = random.randint(5, 15)
        if 'carroñero' in p['skills']: loot = int(loot * 1.5)
        p['dinero'] += loot
        p['exp'] += 30
        p['enemigo'] = None
        if p['exp'] >= 100:
            p['lvl'] += 1
            p['exp'] %= 100
            p['sp'] += 1
            p['max_hp'] += 10
            p['hp'] = p['max_hp']
    else:
        dano_recibido = max(1, p['enemigo']['atk'] - p['defensa'])
        p['hp'] -= dano_recibido
        if dano_recibido > 10 and random.random() < 0.3:
            if 'herida_abierta' not in p['estados']:
                p['estados'].append('herida_abierta')

    if p['hp'] <= 0: return redirect(url_for('morir'))
    session.modified = True
    return redirect(url_for('juego'))

@app.route('/curar_herida')
def curar_herida():
    # Esta ruta ahora es un "acceso rápido" si tienes botiquines en mochila
    p = session['p']
    if 'Botiquín' in p['inventario']:
        p['inventario'].remove('Botiquín')
        if 'herida_abierta' in p['estados']: p['estados'].remove('herida_abierta')
        p['hp'] = min(p['max_hp'], p['hp'] + 50)
        p['log'] = "Has usado un botiquín de emergencia."
    elif 'Vendas' in p['inventario']:
        p['inventario'].remove('Vendas')
        if 'herida_abierta' in p['estados']: p['estados'].remove('herida_abierta')
        p['log'] = "Has usado vendas para parar el sangrado."
    else:
        p['log'] = "No tienes suministros médicos en la mochila."
    
    session.modified = True
    return redirect(url_for('juego'))

@app.route('/dormir')
def dormir():
    p = session['p']
    if 'herida_abierta' in p['estados']:
        p['log'] = "No puedes dormir mientras sangras."
    else:
        p['hp'] = min(p['max_hp'], p['hp'] + 30)
        p['hambre'] = max(0, p['hambre'] - 20)
        p['ciclo_pasos'] += 60
        p['log'] = "Has descansado."
    
    session.modified = True
    return redirect(url_for('juego'))

@app.route('/ignorar_mercader')
def ignorar_mercader():
    session['p']['mercader'] = None
    return redirect(url_for('juego'))

@app.route('/morir')
def morir():
    session.pop('p', None)
    return "<h1>HAS MUERTO</h1><a href='/'>Reintentar</a>"

if __name__ == '__main__':
    app.run(debug=True)