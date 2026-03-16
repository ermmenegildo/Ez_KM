# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from traducciones import TEXTOS
from app_data import CLASES, OBJETOS, ITEMS_CURATIVOS
import random, math, json, os

app = Flask(__name__)
app.secret_key = 'super_zombie_rpg_2026'

RANKING_FILE = 'leaderboard.json'
DEATHS_FILE  = 'deaths.json'

# ============================================================
# DATOS ESTÁTICOS
# ============================================================

DISTRITOS = {
    'Parque Central':      {'color':'#2ecc71','peligro':0,'desc':'Zona segura. Sin zombis.'},
    'Centro Urbano':       {'color':'#e74c3c','peligro':3,'desc':'Epicentro del brote. Loot alto.'},
    'Distrito Financiero': {'color':'#f39c12','peligro':2,'desc':'Torres en ruinas. Mercaderes.'},
    'Zona Militar':        {'color':'#c0392b','peligro':4,'desc':'Base abandonada. Armamento.'},
    'Puerto Fluvial':      {'color':'#16a085','peligro':2,'desc':'Suministros cerca del agua.'},
    'Hospital':            {'color':'#1abc9c','peligro':3,'desc':'Medicamentos. Muy infestado.'},
    'Zona Industrial':     {'color':'#8e44ad','peligro':3,'desc':'Fabricas. Materiales.'},
    'Cementerio':          {'color':'#7f8c8d','peligro':2,'desc':'Zombis mas resistentes.'},
    'Barrio Residencial':  {'color':'#27ae60','peligro':1,'desc':'Mas tranquilo.'},
    'Periferia':           {'color':'#2980b9','peligro':1,'desc':'Campos abiertos.'},
}

ZONAS_SEGURAS = [(0,0),(0,50),(-50,0),(50,0),(0,-50),(50,50),(-50,50),(50,-50),(-50,-50)]

HABILIDADES = {
    'fuerza':        {'nombre':'Musculo',     'desc':'+5 Dano base.',             'coste':1,'cat':'combate',      'req':None},
    'fuerza2':       {'nombre':'Bruto',        'desc':'+8 Dano adicional.',        'coste':2,'cat':'combate',      'req':'fuerza'},
    'esquivar':      {'nombre':'Evasor',       'desc':'15% de evadir ataques.',    'coste':1,'cat':'combate',      'req':None},
    'golpe_critico': {'nombre':'Ojo Clinico',  'desc':'20% de dano doble.',        'coste':2,'cat':'combate',      'req':'fuerza'},
    'sigilo':        {'nombre':'Sombra',       'desc':'Zombis no te ven a dist>3.','coste':2,'cat':'combate',      'req':'esquivar'},
    'supervivencia': {'nombre':'Metabolismo',  'desc':'Hambre baja mas despacio.', 'coste':1,'cat':'supervivencia','req':None},
    'supervivencia2':{'nombre':'Ayuno Extremo','desc':'Hambre baja aun menos.',    'coste':2,'cat':'supervivencia','req':'supervivencia'},
    'resistencia':   {'nombre':'Piel Dura',    'desc':'+20 HP maximo.',            'coste':1,'cat':'supervivencia','req':None},
    'medicina':      {'nombre':'Paramedico',   'desc':'Curativos curan +30%.',     'coste':2,'cat':'supervivencia','req':'resistencia'},
    'inmunidad':     {'nombre':'Inmune',       'desc':'Infeccion avanza 50% mas despacio.','coste':2,'cat':'supervivencia','req':'resistencia'},
    'carronero':     {'nombre':'Carronero',    'desc':'Mas creditos al matar.',    'coste':1,'cat':'recursos',     'req':None},
    'mochila_ext':   {'nombre':'Mochilero',    'desc':'+2 slots inventario.',      'coste':1,'cat':'recursos',     'req':None},
    'mochila_ext2':  {'nombre':'Cargador',     'desc':'+3 slots adicionales.',     'coste':2,'cat':'recursos',     'req':'mochila_ext'},
    'mochila_ext3':  {'nombre':'Camionero',    'desc':'+5 slots adicionales.',     'coste':3,'cat':'recursos',     'req':'mochila_ext2'},
    'ganzua':        {'nombre':'Cerrajero',    'desc':'Ganzua con 1 fallo menos.', 'coste':2,'cat':'recursos',     'req':None},
    'agricultura':   {'nombre':'Botanico',     'desc':'Halla plantas medicinales.','coste':1,'cat':'exploracion',  'req':None},
    'navegacion':    {'nombre':'Orientacion',  'desc':'Mayor radio de deteccion.', 'coste':1,'cat':'exploracion',  'req':None},
    'velocidad':     {'nombre':'Corredor',     'desc':'Huida garantizada.',        'coste':2,'cat':'exploracion',  'req':None},
    'carisma':       {'nombre':'Carisma',      'desc':'Superv. dan item extra.',   'coste':2,'cat':'exploracion',  'req':None},
}

# --- TIPOS DE ZOMBI ---
TIPOS_ZOMBI = {
    'normal':   {'nombre':'Zombi',          'hp':35,'atk':12,'xp':35, 'inf_chance':0.013,'color':'#ff3131','ef':None},
    'corredor': {'nombre':'Zombi Corredor', 'hp':22,'atk':18,'xp':45, 'inf_chance':0.020,'color':'#ff8800','ef':None},
    'gordo':    {'nombre':'Zombi Bloated',  'hp':80,'atk':8, 'xp':60, 'inf_chance':0.000,'color':'#8e44ad','ef':'explota'},
    'nuclear':  {'nombre':'Zombi Nuclear',  'hp':50,'atk':15,'xp':70, 'inf_chance':0.010,'color':'#f1c40f','ef':'irradiado'},
    'soldado':  {'nombre':'Zombi Soldado',  'hp':65,'atk':22,'xp':80, 'inf_chance':0.015,'color':'#c0392b','ef':None},
    'nino':     {'nombre':'Zombi Pequeno',  'hp':18,'atk':10,'xp':25, 'inf_chance':0.018,'color':'#e74c3c','ef':'evasion'},
    'mutante':  {'nombre':'Zombi Mutante',  'hp':90,'atk':25,'xp':100,'inf_chance':0.020,'color':'#2ecc71','ef':None},
    'toxico':   {'nombre':'Zombi Toxico',   'hp':40,'atk':14,'xp':55, 'inf_chance':0.000,'color':'#27ae60','ef':'infectado'},
}

ZOMBI_POOL = {
    0:[('normal',100)],
    1:[('normal',70),('corredor',20),('gordo',10)],
    2:[('normal',50),('corredor',25),('gordo',10),('nuclear',8),('toxico',7)],
    3:[('normal',35),('corredor',20),('soldado',15),('nuclear',12),('toxico',10),('gordo',5),('nino',3)],
    4:[('normal',20),('soldado',20),('mutante',15),('nuclear',15),('toxico',12),('corredor',8),('gordo',5),('nino',5)],
}

# --- ENFERMEDADES ---
ENFERMEDADES = {
    'gripe':       {'nombre':'Gripe',        'dano':1,'cada':20,'dura':60,'cura':'Antibioticos'},
    'intoxicacion':{'nombre':'Intoxicacion', 'dano':2,'cada':15,'dura':40,'cura':'Carbon Activado'},
    'neumonia':    {'nombre':'Neumonia',      'dano':2,'cada':12,'dura':80,'cura':'Antibioticos'},
}

# --- LOOT ---
LOOT_EDIFICIO = [
    'Trapo','Trapo','Botella vacia','Alcohol','Alcohol','Palo','Cuerda',
    'Chatarra metalica','Lata vacia','Lata de comida','Lata de comida',
    'Venda','Venda','Agua sucia','Gasolina','Cable','Azucar',
    'Pastilla potabilizadora','Botiquin','Antibioticos','Morfina','Cuchillo',
    'Vial de Retencion','Vial de Retencion',
]
LOOT_CADAVER = [
    'Venda','Lata de comida','Trapo','Alcohol','Cuerda',
    'Botiquin','Antibioticos','Cuchillo','Gasolina','Chatarra metalica',
]
LOOT_COCHE = [
    'Gasolina','Gasolina','Chatarra metalica','Cuerda','Trapo',
    'Lata de comida','Venda','Botiquin','Cuchillo','Cable',
    'Antibioticos','Alcohol','Vial de Retencion','Morfina',
]

RECOMPENSAS_SUPERV = [
    ['Botiquin','Venda'],['Lata de comida','Agua Purificada'],
    ['Cuchillo','Trapo'],['Antibioticos','Venda'],
    ['Gasolina','Botella vacia','Trapo'],['Cuerda','Palo','Lata de comida'],
    ['Vial de Retencion'],['Racion Energetica','Agua Purificada'],
    ['Chatarra metalica','Cable'],['Rifle'],
]
NOMBRES_SUPERV = ['Ana','Marcos','Lucia','Ivan','Sara','Dani','Carlos','Miren',
                   'Txema','Iker','Amaia','Gorka','Elena','Pablo','Nerea','Jon']

# ============================================================
# FUNCIONES BASE
# ============================================================

def get_refugio(x,y): return round(x/100)*100, round(y/100)*100

def obtener_distrito(x,y):
    dist=math.sqrt(x**2+y**2); ang=math.degrees(math.atan2(y,x))%360
    if dist<15:  return 'Parque Central'
    if dist<38:  return 'Centro Urbano'
    if 0<=ang<45 or 315<=ang<360: return 'Distrito Financiero'
    if 45<=ang<90:  return 'Zona Militar'
    if 90<=ang<135: return 'Puerto Fluvial'
    if 135<=ang<180:return 'Hospital'
    if 180<=ang<225:return 'Zona Industrial'
    if 225<=ang<270:return 'Cementerio'
    if 270<=ang<315:return 'Barrio Residencial'
    return 'Periferia'

def es_zona_segura(x,y):
    return any(abs(x-zx)<=3 and abs(y-zy)<=3 for zx,zy in ZONAS_SEGURAS)

def guardar_puntuacion(nombre,dias,nivel):
    scores=[]
    if os.path.exists(RANKING_FILE):
        try:
            with open(RANKING_FILE,'r',encoding='utf-8') as f: scores=json.load(f)
        except: pass
    scores.append({'nombre':nombre,'dias':dias,'lvl':nivel})
    scores=sorted(scores,key=lambda x:x['dias'],reverse=True)[:10]
    with open(RANKING_FILE,'w',encoding='utf-8') as f: json.dump(scores,f,indent=2)

def guardar_muerte(nombre,x,y,dias,nivel):
    deaths=[]
    if os.path.exists(DEATHS_FILE):
        try:
            with open(DEATHS_FILE,'r',encoding='utf-8') as f: deaths=json.load(f)
        except: pass
    deaths.append({'nombre':nombre,'x':x,'y':y,'dias':dias,'lvl':nivel})
    deaths=deaths[-20:]
    with open(DEATHS_FILE,'w',encoding='utf-8') as f: json.dump(deaths,f,indent=2)

def cargar_muertes():
    if os.path.exists(DEATHS_FILE):
        try:
            with open(DEATHS_FILE,'r',encoding='utf-8') as f: return json.load(f)
        except: pass
    return []

def recalcular_stats(p):
    p.setdefault('equipo',{'cabeza':None,'torso':None,'mano_der':None,'espalda':None,'pies':None})
    p['defensa']=0; p['evasion']=0.0
    for slot,item in p['equipo'].items():
        if item and item in OBJETOS:
            obj=OBJETOS[item]; p['defensa']+=obj.get('defensa',0); p['evasion']+=obj.get('evasion',0.0)
    b=0; sk=p.get('skills',[])
    if 'mochila_ext' in sk:  b+=2
    if 'mochila_ext2' in sk: b+=3
    if 'mochila_ext3' in sk: b+=5
    p['max_inventario']=5+b

def add_item(p,item):
    if len(p.get('inventario',[]))<p.get('max_inventario',5):
        p['inventario'].append(item); return True
    return False

def _juego_vars(p):
    d=obtener_distrito(p['x'],p['y']); rx,ry=get_refugio(p['x'],p['y'])
    return dict(
        distrito=d, info_distrito=DISTRITOS.get(d,{}),
        es_noche=(p['ciclo_pasos']>=100),
        en_refugio=(p['x']==rx and p['y']==ry),
        zona_segura=es_zona_segura(p['x'],p['y']),
        habs=HABILIDADES, distritos=DISTRITOS,
        zonas_seguras=ZONAS_SEGURAS, recetas={},
        enfermedades=ENFERMEDADES,
    )

def spawn_zombi(p, tipo_forzado=None):
    """Crea un dict de zombi según el peligro del distrito actual."""
    dist   = obtener_distrito(p['x'],p['y'])
    peligro= DISTRITOS.get(dist,{}).get('peligro',1)
    pool   = ZOMBI_POOL.get(peligro, ZOMBI_POOL[1])
    if tipo_forzado and tipo_forzado in TIPOS_ZOMBI:
        tipo_k = tipo_forzado
    else:
        tipo_k = random.choices([x[0] for x in pool], weights=[x[1] for x in pool])[0]
    tz   = TIPOS_ZOMBI[tipo_k]
    lvl  = p.get('lvl',1)
    hp_f = tz['hp'] + lvl*4
    return {
        'nombre':   tz['nombre'],
        'tipo':     tipo_k,
        'hp':       hp_f,
        'hp_max':   hp_f,
        'atk':      tz['atk'] + lvl,
        'xp':       tz['xp'],
        'inf_chance': tz['inf_chance'],
        'color':    tz['color'],
        'ef':       tz['ef'],
    }

# ============================================================
# INFECCIÓN Y ENFERMEDADES
# ============================================================

def tick_infeccion(p, pasos=1):
    """Avanza la infección y enfermedades cada paso."""
    logs = []

    # Infección zombi
    if p.get('infeccion',0) > 0:
        vel = 1
        if 'inmunidad' in p.get('skills',[]): vel = 0.5
        # Vial activo frena la progresión a 0
        if p.get('vial_activo',0) > 0:
            p['vial_activo'] -= pasos
            if p['vial_activo'] <= 0:
                p['vial_activo'] = 0
                logs.append("El efecto del Vial de Retencion ha caducado.")
        else:
            p['infeccion'] = min(100, p['infeccion'] + vel * pasos)
            if p['infeccion'] >= 100:
                p['hp'] = 0
                p['log'] = "La infeccion ha consumido tu organismo. Has muerto."
                return logs, True  # muerte

        # Daño progresivo cuando infección > 50
        if p['infeccion'] >= 50 and p['pasos'] % 15 == 0:
            dmg = int((p['infeccion'] - 40) / 10)
            p['hp'] -= dmg
            logs.append(f"Infeccion: -{dmg}HP ({int(p['infeccion'])}%)")

    # Enfermedades activas
    enfs = p.get('enfermedades_activas', {})
    for eid, edata in list(enfs.items()):
        edata['restante'] -= pasos
        if edata['restante'] <= 0:
            del enfs[eid]
            logs.append(f"{ENFERMEDADES[eid]['nombre']} curada (expiracion).")
            continue
        cada = ENFERMEDADES[eid]['cada']
        if p['pasos'] % cada == 0:
            dmg = ENFERMEDADES[eid]['dano']
            p['hp'] -= dmg
            logs.append(f"{ENFERMEDADES[eid]['nombre']}: -{dmg}HP")

    return logs, False

def aplicar_mordisco(p, zombi):
    """Intenta infectar al jugador al recibir mordisco. Devuelve log o None."""
    chance = zombi.get('inf_chance', 0.013)
    if random.random() < chance:
        if p.get('infeccion', 0) == 0:
            p['infeccion'] = 1
            return "MORDISCO INFECTADO. Busca un Vial de Retencion urgente."
        else:
            p['infeccion'] = min(100, p['infeccion'] + 5)
            return f"Mordisco: infeccion +5% ({int(p['infeccion'])}%)"
    return None

def intentar_enfermedad(p):
    """Pequeña probabilidad de contraer enfermedad cada N pasos."""
    if random.random() < 0.004:  # ~1 cada 250 pasos
        enfs_activas = p.get('enfermedades_activas', {})
        posibles = [eid for eid in ENFERMEDADES if eid not in enfs_activas]
        if posibles:
            eid = random.choice(posibles)
            info = ENFERMEDADES[eid]
            enfs_activas[eid] = {'restante': info['dura']}
            p['enfermedades_activas'] = enfs_activas
            return f"Has contraido {info['nombre']}. Cura: {info['cura']}."
    return None

# ============================================================
# EVENTOS ALEATORIOS
# ============================================================

def generar_evento(p):
    dist   = obtener_distrito(p['x'],p['y'])
    peligro= DISTRITOS.get(dist,{}).get('peligro',1)
    pool=[('superviviente',max(1,6-peligro)),('cadaver',2+peligro),
          ('radio',2),('lluvia',2),('explosion',2)]
    if peligro>=2: pool+=[('trampa',3),('manada',peligro)]
    if 'agricultura' in p.get('skills',[]): pool.append(('planta',4))
    tipo=random.choices([x[0] for x in pool],weights=[x[1] for x in pool])[0]
    nombre=random.choice(NOMBRES_SUPERV)
    if tipo=='superviviente':
        r=random.choice(RECOMPENSAS_SUPERV); ep=random.random()<0.5
        return {'tipo':'superviviente','nombre':nombre,'recompensa':r,'en_peligro':ep,
                'msj':f"{nombre} esta acorralado." if ep else f"{nombre} te observa."}
    elif tipo=='cadaver':
        loot=random.sample(LOOT_CADAVER,k=random.randint(1,2))
        return {'tipo':'cadaver','loot':loot,'msj':"Un cadaver reciente bloquea el camino."}
    elif tipo=='trampa':
        d=random.randint(8,20)
        return {'tipo':'trampa','dano':d,'msj':f"Trampa de cables. -{d}HP si pisas."}
    elif tipo=='radio':
        msgs=["'...sector 7... supervivientes...'",
              "'PROTOCOLO OMEGA. EVACUACION CANCELADA.'",
              "'...vacuna... laboratorio...'",
              "'...papa no vuelve... tengo hambre...'"]
        return {'tipo':'radio','msj':random.choice(msgs)}
    elif tipo=='lluvia':
        d=random.randint(3,10)
        return {'tipo':'lluvia','dano':d,'msj':f"Lluvia acida. -{d}HP."}
    elif tipo=='manada':
        n=random.randint(2,4)
        return {'tipo':'manada','n_zombis':n,'msj':f"Manada de {n} zombis detectada."}
    elif tipo=='explosion':
        return {'tipo':'explosion','msj':"Explosion lejana. El suelo tiembla."}
    elif tipo=='planta':
        item=random.choice(['Venda','Agua Purificada','Antibioticos'])
        return {'tipo':'planta','item':item,'msj':"Planta medicinal encontrada."}
    return None

def _dar_recompensa_superv(p, inter):
    r=inter.get('recompensa',['Venda']); dados=[]
    for it in r:
        if add_item(p,it): dados.append(it)
    if 'carisma' in p.get('skills',[]):
        b=random.choice(['Lata de comida','Trapo','Alcohol','Cuerda','Vial de Retencion'])
        if add_item(p,b): dados.append(b)
    n=inter.get('nombre','Superviviente')
    p['log']=f"{n} recompensa: {', '.join(dados) if dados else 'mochila llena'}."
    p['exp']=p.get('exp',0)+20
    if p['exp']>=100:
        p['lvl']+=1; p['exp']%=100; p['sp']+=1; p['max_hp']+=10
        p['hp']=p['max_hp']; p['log']+=f" NIVEL {p['lvl']}! +1SP"

# ============================================================
# PARTES COMBATE
# ============================================================

PARTES_BONUS={
    'cabeza':   {'mult':2.5,'efecto':'aturdir'},
    'torso':    {'mult':1.0,'efecto':None},
    'brazo_izq':{'mult':0.7,'efecto':'desarmar'},
    'brazo_der':{'mult':0.7,'efecto':'desarmar'},
    'pierna_izq':{'mult':0.8,'efecto':'ralentizar'},
    'pierna_der':{'mult':0.8,'efecto':'ralentizar'},
}

# ============================================================
# RUTAS
# ============================================================

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in TEXTOS: session['lang']=lang
    return redirect(request.referrer or url_for('index'))

@app.route('/leaderboard')
def leaderboard():
    lang=session.get('lang','es'); scores=[]
    if os.path.exists(RANKING_FILE):
        try:
            with open(RANKING_FILE,'r',encoding='utf-8') as f: scores=json.load(f)
        except: pass
    return render_template('leaderboard.html',scores=scores,t=TEXTOS[lang])

@app.route('/comprar_habilidad/<hab_id>')
def comprar_habilidad(hab_id):
    p=session.get('p')
    if not p: return redirect(url_for('juego'))
    hab=HABILIDADES.get(hab_id)
    if hab and p.get('sp',0)>=hab['coste']:
        req=hab.get('req')
        if req is None or req in p.get('skills',[]):
            if hab_id not in p.get('skills',[]):
                p['sp']-=hab['coste']; p.setdefault('skills',[]).append(hab_id)
                if hab_id=='fuerza':      p['dmg_base']=p.get('dmg_base',10)+5
                if hab_id=='fuerza2':     p['dmg_base']=p.get('dmg_base',10)+8
                if hab_id=='resistencia': p['max_hp']+=20; p['hp']=min(p['hp']+20,p['max_hp'])
                recalcular_stats(p); p['log']=f"Habilidad: {hab['nombre']}"
    session.modified=True; return redirect(url_for('juego'))

@app.route('/')
def index():
    if 'lang' not in session: session['lang']='es'
    return render_template('index.html',t=TEXTOS[session['lang']],clases=CLASES)

@app.route('/iniciar', methods=['POST'])
def iniciar():
    cid=request.form.get('clase')
    if cid not in CLASES: return redirect(url_for('index'))
    cd=CLASES[cid]; hp=cd['hp']; item=cd.get('item','')
    session['p']={
        'nombre':request.form.get('nombre','Superviviente'),'clase':cid,
        'hp':hp,'max_hp':hp,'hambre':100,'dinero':50,
        'x':0,'y':0,'pasos':0,'ciclo_pasos':0,'dias':0,
        'lvl':1,'exp':0,'sp':0,'skills':[],
        'inventario':[item] if item else [],'max_inventario':5,
        'estados':[],'dmg_base':10,'defensa':0,'evasion':0.0,
        'equipo':{'cabeza':None,'torso':None,'mano_der':None,'espalda':None,'pies':None},
        'enemigo':None,'mercader':None,'interaccion':None,
        'pasos_hambre_cero':0,'log_combate':[],
        # Infección
        'infeccion':0,           # 0-100
        'vial_activo':0,         # pasos restantes del vial
        # Enfermedades
        'enfermedades_activas':{},
        # Edificios y coches
        'edificios_mapa':[{'x':random.randint(-60,60),'y':random.randint(-60,60),'saqueado':False} for _ in range(16)],
        'coches_mapa':[{'x':random.randint(-70,70),'y':random.randint(-70,70),'forzado':False} for _ in range(10)],
        'enemigos_mapa':[{'x':random.randint(-15,15),'y':random.randint(-15,15)} for _ in range(5)],
        'muertes_mapa':cargar_muertes(),
        'log':"Sistemas listos. Protocolo C.R.T. activo.",
    }
    return redirect(url_for('juego'))

@app.route('/juego')
def juego():
    p=session.get('p')
    if not p: return redirect(url_for('index'))
    lang=session.get('lang','es'); t_idioma=TEXTOS.get(lang,TEXTOS['es'])
    p['muertes_mapa']=cargar_muertes()
    # Backfill
    p.setdefault('equipo',{'cabeza':None,'torso':None,'mano_der':None,'espalda':None,'pies':None})
    p.setdefault('defensa',0); p.setdefault('evasion',0.0)
    p.setdefault('log_combate',[]); p.setdefault('muertes_mapa',[])
    p.setdefault('infeccion',0); p.setdefault('vial_activo',0)
    p.setdefault('enfermedades_activas',{})
    p.setdefault('coches_mapa',[])
    for ed in p.get('edificios_mapa',[]): ed.setdefault('saqueado',False)
    for c  in p.get('coches_mapa',[]):    c.setdefault('forzado',False)
    session.modified=True
    return render_template('juego.html',p=p,t=t_idioma,**_juego_vars(p))

@app.route('/mover/<dir>')
def mover(dir):
    p=session.get('p')
    if not p or p.get('enemigo') or p.get('mercader') or p.get('interaccion'):
        return redirect(url_for('juego'))
    if dir=='n': p['y']+=1
    elif dir=='s': p['y']-=1
    elif dir=='e': p['x']+=1
    elif dir=='o': p['x']-=1
    p['pasos']+=1; p['ciclo_pasos']+=1; p['log_combate']=[]

    # Superviviente pendiente
    if p.get('superviviente_pendiente') and not p.get('enemigo'):
        sv=p.pop('superviviente_pendiente'); _dar_recompensa_superv(p,sv)

    # Inanición
    if p['hambre']<=0:
        p['pasos_hambre_cero']=p.get('pasos_hambre_cero',0)+1
        if p['pasos_hambre_cero']>=740:
            p['hp']=0; p['log']="Muerte por inanicion."; return redirect(url_for('morir'))
    else: p['pasos_hambre_cero']=0
    tasa=10 if 'supervivencia2' in p.get('skills',[]) else (8 if 'supervivencia' in p.get('skills',[]) else 6)
    if p['pasos']%tasa==0:
        p['hambre']=max(0,p['hambre']-1)
        if p['hambre']<=0: p['hp']-=3

    # Zona segura
    if es_zona_segura(p['x'],p['y']):
        if p['hp']<p['max_hp']: p['hp']=min(p['max_hp'],p['hp']+2)

    # Infección y enfermedades
    inf_logs, muerte_inf = tick_infeccion(p)
    if muerte_inf: return redirect(url_for('morir'))
    if inf_logs: p['log']=inf_logs[-1]

    # Probabilidad de enfermedad
    enf_msg = intentar_enfermedad(p)
    if enf_msg: p['log']=enf_msg

    # IA zombis
    ddet=3 if 'sigilo' in p.get('skills',[]) else 6
    for z in list(p['enemigos_mapa']):
        if math.sqrt((p['x']-z['x'])**2+(p['y']-z['y'])**2)<ddet:
            if z['x']<p['x']: z['x']+=1
            elif z['x']>p['x']: z['x']-=1
            if z['y']<p['y']: z['y']+=1
            elif z['y']>p['y']: z['y']-=1
        if z['x']==p['x'] and z['y']==p['y']:
            p['enemigo']=spawn_zombi(p)
            p['enemigos_mapa'].remove(z)
            p['log']=f"{p['enemigo']['nombre']} te intercepta!"
            session.modified=True; return redirect(url_for('juego'))
    while len(p['enemigos_mapa'])<5:
        ox=random.choice([-10,-8,8,10]); oy=random.choice([-10,-8,8,10])
        p['enemigos_mapa'].append({'x':p['x']+ox,'y':p['y']+oy})

    # Edificios
    for ed in p['edificios_mapa']:
        if ed['x']==p['x'] and ed['y']==p['y'] and not ed.get('saqueado'):
            p['interaccion']={'tipo':'edificio','msj':'Edificio detectado. Entrar?',
                              'zombis':random.random()<0.3,'ed_x':ed['x'],'ed_y':ed['y']}
            session.modified=True; return redirect(url_for('juego'))

    # Coches
    for c in p['coches_mapa']:
        if c['x']==p['x'] and c['y']==p['y'] and not c.get('forzado'):
            combo = [random.choice(['w','a','s','d']) for _ in range(random.randint(4,6))]
            p['interaccion']={'tipo':'coche','msj':'Coche detectado. Usar ganzua para abrir?',
                              'combo':combo,'intentos':0,
                              'max_intentos': 3 if 'ganzua' not in p.get('skills',[]) else 4,
                              'progreso':[],'c_x':c['x'],'c_y':c['y']}
            session.modified=True; return redirect(url_for('juego'))

    # Eventos aleatorios
    if p['pasos']%8==0 and not es_zona_segura(p['x'],p['y']):
        ev=generar_evento(p)
        if ev:
            if ev['tipo']=='lluvia':
                p['hp']=max(1,p['hp']-ev['dano']); p['log']=ev['msj']
            elif ev['tipo'] in ('explosion','radio'):
                p['log']=ev['msj']
            elif ev['tipo']=='planta':
                if add_item(p,ev['item']): p['log']=ev['msj']+f" +{ev['item']}"
                else: p['log']=ev['msj']+" (mochila llena)"
            elif ev['tipo']=='manada':
                for _ in range(ev['n_zombis']):
                    ox=random.choice([-6,-4,4,6]); oy=random.choice([-6,-4,4,6])
                    p['enemigos_mapa'].append({'x':p['x']+ox,'y':p['y']+oy})
                p['log']=ev['msj']
            else:
                p['interaccion']=ev

    if p['hp']<=0: return redirect(url_for('morir'))
    if p['ciclo_pasos']>=180:
        p['ciclo_pasos']=0; p['dias']+=1
        if random.random()<0.25:
            its=random.sample(['Botiquin','Lata de comida','Venda','Antibioticos','Cuerda','Vial de Retencion'],3)
            p['mercader']={'items':its,'precios':{'Botiquin':30,'Lata de comida':15,'Venda':10,'Antibioticos':40,'Cuerda':12,'Vial de Retencion':50}}
            p['log']="Un mercader aparece al amanecer."
    session.modified=True; return redirect(url_for('juego'))

# --- DORMIR ---
@app.route('/dormir')
def dormir():
    p=session.get('p')
    if not p: return redirect(url_for('juego'))
    if p.get('enemigo') or p.get('interaccion') or p.get('mercader'):
        p['log']="No puedes dormir con amenazas activas."; session.modified=True; return redirect(url_for('juego'))

    es_noche = p['ciclo_pasos'] >= 100
    if not es_noche and not es_zona_segura(p['x'],p['y']):
        p['log']="Solo puedes dormir de noche o en una zona segura."; session.modified=True; return redirect(url_for('juego'))

    # Avanzar hasta amanecer (ciclo_pasos -> 0, dias +1)
    pasos_saltados = 180 - p['ciclo_pasos'] if es_noche else (180 - p['ciclo_pasos'] + 100)
    pasos_saltados = max(10, min(pasos_saltados, 180))

    p['ciclo_pasos'] = 0
    p['dias'] += 1
    p['pasos'] += pasos_saltados

    # Regen al dormir
    regen = int(p['max_hp'] * 0.25)
    p['hp'] = min(p['max_hp'], p['hp'] + regen)
    p['hambre'] = max(0, p['hambre'] - 15)  # Dormir da hambre

    # Infección y enfermedades avanzan mientras duermes
    inf_logs, muerte = tick_infeccion(p, pasos=pasos_saltados)
    if muerte: return redirect(url_for('morir'))

    p['log'] = f"Duermes hasta el amanecer. +{regen}HP. Hambre -15."
    if inf_logs: p['log'] += f" | {inf_logs[-1]}"

    session.modified=True; return redirect(url_for('juego'))

# --- COMBATE ---
@app.route('/atacar')
@app.route('/atacar/<parte>')
def atacar(parte='torso'):
    p=session.get('p')
    if not p or not p.get('enemigo'): return redirect(url_for('juego'))
    enemigo=p['enemigo']; logs=p.get('log_combate',[]); bonus=PARTES_BONUS.get(parte,PARTES_BONUS['torso'])
    dmg=p.get('dmg_base',10)+p.get('lvl',1)
    arma=p.get('equipo',{}).get('mano_der')
    if arma and arma in OBJETOS: dmg+=OBJETOS[arma].get('dmg',0)
    dmg=int(dmg*bonus['mult'])
    if 'golpe_critico' in p.get('skills',[]) and random.random()<0.20:
        dmg*=2; logs.append(f"CRITICO! {parte.upper()} -{dmg}HP")
    else: logs.append(f"{parte.upper()} -{dmg}HP")
    enemigo['hp']-=dmg

    if enemigo['hp']<=0:
        loot=int(random.randint(5,20)*(1.5 if 'carronero' in p.get('skills',[]) else 1.0))
        p['dinero']+=loot; p['exp']=p.get('exp',0)+enemigo.get('xp',35)
        # Zombi gordo explota
        if enemigo.get('ef')=='explota':
            daño_exp = random.randint(10,20)
            p['hp'] -= daño_exp
            logs.append(f"Zombi explota! -{daño_exp}HP")
        logs.append(f"Eliminado. +{enemigo.get('xp',35)}XP +{loot}CC")
        if random.random()<0.35:
            it=random.choice(LOOT_CADAVER)
            if add_item(p,it): logs.append(f"Loot: {it}")
        p['enemigo']=None
        if p.get('superviviente_pendiente'):
            sv=p.pop('superviviente_pendiente'); _dar_recompensa_superv(p,sv)
        if p['exp']>=100:
            p['lvl']+=1; p['exp']%=100; p['sp']+=1; p['max_hp']+=10
            p['hp']=p['max_hp']; logs.append(f"NIVEL {p['lvl']}! +1SP")
    else:
        # Turno enemigo
        ev=p.get('evasion',0.0)
        if 'esquivar' in p.get('skills',[]): ev=max(ev,0.15)
        # Zombi pequeño tiene evasion extra
        if enemigo.get('ef')=='evasion': ev=max(ev,0.25)
        if random.random()<ev:
            logs.append("Esquivaste!")
        else:
            dr=max(1,enemigo['atk']-p.get('defensa',0)); p['hp']-=dr
            logs.append(f"{enemigo['nombre']}: -{dr}HP")
            # Infección por mordisco
            inf_msg=aplicar_mordisco(p,enemigo)
            if inf_msg: logs.append(inf_msg)
            # Efecto especial del zombi
            ef=enemigo.get('ef')
            if ef=='irradiado' and 'irradiado' not in p.get('estados',[]): p.setdefault('estados',[]).append('irradiado'); logs.append("IRRADIADO!")
            if ef=='infectado':
                p['infeccion']=min(100,p.get('infeccion',0)+10); logs.append(f"Veneno zombi: infeccion +10% ({int(p['infeccion'])}%)")
    p['log_combate']=logs[-5:]
    if p['hp']<=0: return redirect(url_for('morir'))
    session.modified=True; return redirect(url_for('juego'))

@app.route('/huir')
def huir():
    p=session.get('p')
    if not p or not p.get('enemigo'): return redirect(url_for('juego'))
    if 'velocidad' in p.get('skills',[]) or random.random()<0.55:
        dr=random.randint(3,8); p['hp']-=dr; p['enemigo']=None; p['log']=f"Huiste. -{dr}HP."
        dx,dy=random.choice([(1,0),(-1,0),(0,1),(0,-1)]); p['x']+=dx; p['y']+=dy
    else:
        dr=max(1,p['enemigo']['atk']-p.get('defensa',0)); p['hp']-=dr; p['log']=f"No pudiste huir. -{dr}HP."
    if p['hp']<=0: return redirect(url_for('morir'))
    session.modified=True; return redirect(url_for('juego'))

# --- INVENTARIO ---
@app.route('/usar_item/<item>')
def usar_item(item):
    p=session.get('p')
    if not p or item not in p.get('inventario',[]): return redirect(url_for('juego'))
    curativos=ITEMS_CURATIVOS if isinstance(ITEMS_CURATIVOS,dict) else {}
    mult=1.3 if 'medicina' in p.get('skills',[]) else 1.0

    if item=='Vial de Retencion':
        p['vial_activo']=p.get('vial_activo',0)+120
        p['log']="Vial de Retencion usado. Infeccion frenada 120 pasos."
        p['inventario'].remove(item); session.modified=True; return redirect(url_for('juego'))

    if item=='Antibioticos':
        cured=[]
        enfs=p.get('enfermedades_activas',{})
        for eid in list(enfs.keys()):
            if ENFERMEDADES[eid]['cura']=='Antibioticos':
                del enfs[eid]; cured.append(ENFERMEDADES[eid]['nombre'] if eid in ENFERMEDADES else eid)
        p['log']=f"Antibioticos: {', '.join(cured) if cured else 'no habia enfermedades bacterianas'} curado."
        p['inventario'].remove(item); session.modified=True; return redirect(url_for('juego'))

    if item in curativos:
        data=curativos[item]
        hpc=int((data.get('hp',0) if isinstance(data,dict) else data)*mult)
        ham=data.get('hambre',0) if isinstance(data,dict) else 0
        p['hp']=min(p['max_hp'],p['hp']+hpc); p['hambre']=min(100,p['hambre']+ham)
        p['log']=f"{item}: +{hpc}HP."
    else:
        p['log']=f"{item}: no consumible directamente."
    p['inventario'].remove(item); session.modified=True; return redirect(url_for('juego'))

@app.route('/equipar_item/<item>')
def equipar_item(item):
    p=session.get('p')
    if not p or item not in p.get('inventario',[]): return redirect(url_for('juego'))
    p.setdefault('equipo',{'cabeza':None,'torso':None,'mano_der':None,'espalda':None,'pies':None})
    obj=OBJETOS.get(item,{}); slot=obj.get('slot','mano_der') if obj else 'mano_der'
    ant=p['equipo'].get(slot)
    if ant: p['inventario'].append(ant)
    p['equipo'][slot]=item; p['inventario'].remove(item); recalcular_stats(p)
    p['log']=f"{item} equipado [{slot}]."; session.modified=True; return redirect(url_for('juego'))

@app.route('/desequipar/<slot>')
def desequipar(slot):
    p=session.get('p')
    if not p: return redirect(url_for('juego'))
    p.setdefault('equipo',{'cabeza':None,'torso':None,'mano_der':None,'espalda':None,'pies':None})
    item=p['equipo'].get(slot)
    if item and len(p.get('inventario',[]))<p.get('max_inventario',5):
        p['inventario'].append(item); p['equipo'][slot]=None; recalcular_stats(p); p['log']=f"{item} desequipado."
    elif item: p['log']="Inventario lleno."
    session.modified=True; return redirect(url_for('juego'))

# --- EDIFICIOS ---
@app.route('/entrar_edificio')
def entrar_edificio():
    p=session.get('p')
    if not p or not p.get('interaccion'): return redirect(url_for('juego'))
    inter=p['interaccion']
    if inter.get('zombis'):
        p['enemigo']=spawn_zombi(p); p['log']=f"{p['enemigo']['nombre']} en el edificio!"
    else:
        found=[]; extra=random.randint(0,15); p['dinero']+=extra
        for _ in range(random.randint(1,3)):
            it=random.choice(LOOT_EDIFICIO)
            if add_item(p,it): found.append(it)
        p['log']=f"Saqueado: {', '.join(found) if found else 'nada util'}. +{extra}CC"
    for ed in p['edificios_mapa']:
        if ed.get('x')==inter.get('ed_x') and ed.get('y')==inter.get('ed_y'): ed['saqueado']=True
    p['interaccion']=None; session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_edificio')
def ignorar_edificio():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="Edificio ignorado."
    session.modified=True; return redirect(url_for('juego'))

# --- MINIJUEGO GANZÚA (COCHE) ---
@app.route('/ganzua_input/<tecla>')
def ganzua_input(tecla):
    """Recibe una tecla del minijuego de ganzúa y actualiza el estado."""
    p=session.get('p')
    if not p or not p.get('interaccion') or p['interaccion'].get('tipo')!='coche':
        return redirect(url_for('juego'))
    inter=p['interaccion']
    combo=inter['combo']; prog=inter.get('progreso',[])
    idx=len(prog)

    if idx>=len(combo):
        # Ya terminado, redirigir
        session.modified=True; return redirect(url_for('juego'))

    if tecla==combo[idx]:
        prog.append(tecla); inter['progreso']=prog
        if len(prog)==len(combo):
            # EXITO — abrir coche
            found=[]; extra=random.randint(5,20); p['dinero']+=extra
            for _ in range(random.randint(2,4)):
                it=random.choice(LOOT_COCHE)
                if add_item(p,it): found.append(it)
            p['log']=f"Coche abierto! {', '.join(found) if found else 'vacio'}. +{extra}CC"
            for c in p['coches_mapa']:
                if c.get('x')==inter.get('c_x') and c.get('y')==inter.get('c_y'): c['forzado']=True
            p['interaccion']=None
    else:
        # Fallo
        inter['intentos']=inter.get('intentos',0)+1
        inter['progreso']=[]  # reset progreso
        if inter['intentos']>=inter.get('max_intentos',3):
            # Se acaban los intentos — ganzua rota
            p['log']="Ganzua rota. El coche no pudo abrirse."
            for c in p['coches_mapa']:
                if c.get('x')==inter.get('c_x') and c.get('y')==inter.get('c_y'): c['forzado']=True
            p['interaccion']=None
        else:
            restantes=inter['max_intentos']-inter['intentos']
            p['log']=f"Fallo! Reiniciando. {restantes} intentos restantes."

    session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_coche')
def ignorar_coche():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="Coche ignorado."
    session.modified=True; return redirect(url_for('juego'))

# --- SUPERVIVIENTES ---
@app.route('/rescatar_superviviente')
def rescatar_superviviente():
    p=session.get('p')
    if not p or not p.get('interaccion'): return redirect(url_for('juego'))
    inter=p['interaccion']
    if inter.get('en_peligro'):
        p['enemigo']=spawn_zombi(p)
        p['log']=f"Zombis atacan mientras rescatas a {inter['nombre']}!"
        p['superviviente_pendiente']=inter; p['interaccion']=None
    else:
        _dar_recompensa_superv(p,inter); p['interaccion']=None
    session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_superviviente')
def ignorar_superviviente():
    p=session.get('p')
    if p:
        n=p.get('interaccion',{}).get('nombre','Superviviente')
        p['interaccion']=None; p['log']=f"Ignoras a {n}."
    session.modified=True; return redirect(url_for('juego'))

@app.route('/registrar_cadaver')
def registrar_cadaver():
    p=session.get('p')
    if not p or not p.get('interaccion'): return redirect(url_for('juego'))
    inter=p['interaccion']; dados=[]
    for it in inter.get('loot',[]):
        if add_item(p,it): dados.append(it)
    p['log']=f"Cadaver: {', '.join(dados) if dados else 'nada util'}."; p['interaccion']=None
    session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_cadaver')
def ignorar_cadaver():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="Rodeas el cadaver."
    session.modified=True; return redirect(url_for('juego'))

@app.route('/evitar_trampa')
def evitar_trampa():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="Rodeas la trampa."
    session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_interaccion')
def ignorar_interaccion():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="Sigues adelante."
    session.modified=True; return redirect(url_for('juego'))

# --- MERCADER ---
@app.route('/comprar_mercader/<item>')
def comprar_mercader(item):
    p=session.get('p')
    if not p or not p.get('mercader'): return redirect(url_for('juego'))
    precio=p['mercader']['precios'].get(item,30)
    if p['dinero']>=precio and item in p['mercader']['items']:
        if add_item(p,item):
            p['dinero']-=precio; p['mercader']['items'].remove(item)
            p['log']=f"Comprado: {item} por {precio}CC"
        else: p['log']="Inventario lleno."
    else: p['log']="Creditos insuficientes."
    session.modified=True; return redirect(url_for('juego'))

@app.route('/cerrar_mercader')
def cerrar_mercader():
    p=session.get('p')
    if p: p['mercader']=None
    session.modified=True; return redirect(url_for('juego'))

# --- MAPA ---
@app.route('/mapa')
def mapa():
    p=session.get('p')
    if not p: return redirect(url_for('index'))
    lang=session.get('lang','es'); t_idioma=TEXTOS.get(lang,TEXTOS['es'])
    rx,ry=get_refugio(p['x'],p['y']); dist_ref=int(math.sqrt((p['x']-rx)**2+(p['y']-ry)**2))
    d=obtener_distrito(p['x'],p['y']); p['muertes_mapa']=cargar_muertes()
    return render_template('mapa.html',p=p,t=t_idioma,distrito=d,info_distrito=DISTRITOS.get(d,{}),
        es_noche=(p['ciclo_pasos']>=100),rx=rx,ry=ry,dist_refugio=dist_ref,
        distritos=DISTRITOS,zonas_seguras=ZONAS_SEGURAS)

# --- MUERTE ---
@app.route('/morir')
def morir():
    p=session.get('p')
    if p: guardar_puntuacion(p['nombre'],p['dias'],p.get('lvl',1)); guardar_muerte(p['nombre'],p['x'],p['y'],p['dias'],p.get('lvl',1))
    session.pop('p',None)
    return render_template('muerte.html',t=TEXTOS[session.get('lang','es')])

if __name__ == '__main__':
    app.run(debug=True)