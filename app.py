# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from traducciones import TEXTOS
from app_data import (CLASES, OBJETOS, ITEMS_CURATIVOS, RECETAS_BASE, RECETAS_BIBLIOTECA,
                      TIPOS_MUNICION, CARGADOR, DROPS_JEFE, DROPS_BANDIDO,
                      PIEZAS_BARCO, COMBUSTIBLE_COCHE, RECETAS_DESC)
import random, math, json, os, sqlite3, re, html, time

app = Flask(__name__)
app.secret_key = 'super_zombie_rpg_2026'

DB_FILE      = 'juego.db'
RANKING_FILE = 'leaderboard.json'
DEATHS_FILE  = 'deaths.json'

# ==============================================================
# BASE DE DATOS
# ==============================================================
def init_db():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS personajes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT, genero TEXT, edad INTEGER,
        clase TEXT, lore TEXT, fecha TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ranking(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT, genero TEXT, edad INTEGER,
        dias INTEGER, lvl INTEGER,
        tiempo_seg INTEGER, forma_escape TEXT, fecha TEXT
    )""")
    con.commit(); con.close()

def sanitize(s, max_len=80):
    """Previene XSS e inyección SQL (usamos ? en queries, esto solo limpia texto)."""
    if not isinstance(s, str): return ''
    s = html.escape(s.strip())
    s = re.sub(r'[<>"\';\\]', '', s)
    return s[:max_len]

def guardar_personaje_db(nombre, genero, edad, clase, lore):
    try:
        con = sqlite3.connect(DB_FILE)
        con.execute("INSERT INTO personajes(nombre,genero,edad,clase,lore,fecha) VALUES(?,?,?,?,?,datetime('now'))",
                    (sanitize(nombre), sanitize(genero), edad, sanitize(clase), sanitize(lore, 300)))
        con.commit(); con.close()
    except: pass

def guardar_ranking_db(nombre, genero, edad, dias, lvl, tiempo_seg, forma_escape):
    try:
        con = sqlite3.connect(DB_FILE)
        con.execute("INSERT INTO ranking(nombre,genero,edad,dias,lvl,tiempo_seg,forma_escape,fecha) VALUES(?,?,?,?,?,?,?,datetime('now'))",
                    (sanitize(nombre), sanitize(genero), edad, dias, lvl, tiempo_seg, sanitize(forma_escape)))
        con.commit(); con.close()
    except: pass

def cargar_ranking_db(limit=10):
    try:
        con = sqlite3.connect(DB_FILE)
        rows = con.execute("SELECT nombre,genero,edad,dias,lvl,tiempo_seg,forma_escape FROM ranking ORDER BY dias DESC LIMIT ?", (limit,)).fetchall()
        con.close()
        return [{'nombre':r[0],'genero':r[1],'edad':r[2],'dias':r[3],'lvl':r[4],'tiempo_seg':r[5],'forma_escape':r[6]} for r in rows]
    except: return []

# ==============================================================
# DATOS MAPA
# ==============================================================
DISTRITOS = {
    'Parque Central':      {'color':'#2ecc71','peligro':0,'desc':'Zona segura. Sin zombis.'},
    'Centro Urbano':       {'color':'#e74c3c','peligro':3,'desc':'Epicentro. Loot alto.'},
    'Distrito Financiero': {'color':'#f39c12','peligro':2,'desc':'Torres. Mercaderes.'},
    'Zona Militar':        {'color':'#c0392b','peligro':4,'desc':'Armamento. Muy peligroso.'},
    'Puerto Fluvial':      {'color':'#16a085','peligro':2,'desc':'Barco de escape.'},
    'Hospital':            {'color':'#1abc9c','peligro':3,'desc':'Medicamentos. Infestado.'},
    'Zona Industrial':     {'color':'#8e44ad','peligro':3,'desc':'Fabricas. Materiales.'},
    'Cementerio':          {'color':'#7f8c8d','peligro':2,'desc':'Zombis fuertes. Pitonisa.'},
    'Barrio Residencial':  {'color':'#27ae60','peligro':1,'desc':'Tiendas. Mas tranquilo.'},
    'Periferia':           {'color':'#2980b9','peligro':1,'desc':'Campos. Campamento ok.'},
}

ZONAS_SEGURAS = [(0,0),(0,50),(-50,0),(50,0),(0,-50),(50,50),(-50,50),(50,-50),(-50,-50)]

# Ubicaciones especiales FIJAS en el mapa
LOCS_ESPECIALES = {
    'museo':         {'x':15,'y':10,'nombre':'Museo de Arte',       'desc':'Armaduras y armas legendarias.'},
    'biblioteca':    {'x':-10,'y':15,'nombre':'Biblioteca Central', 'desc':'Planos de crafteo.'},
    'pitonisa':      {'x':-30,'y':-25,'nombre':'Tienda de la Pitonisa','desc':'Armas y misterios.'},
    'comic_store':   {'x':20,'y':-15,'nombre':'Tienda de Comics',   'desc':'La espada de Blade.'},
    'oficina':       {'x':45,'y':10,'nombre':'Oficina Abandonada',  'desc':'Pistolas akimbo.'},
    'mansion':       {'x':-45,'y':30,'nombre':'Mansion',            'desc':'Armaduras de lujo.'},
    'ropa_store':    {'x':12,'y':-20,'nombre':'Tienda de Ropa',     'desc':'Chaquetas de motorista.'},
    'restaurante':   {'x':-8,'y':-12,'nombre':'Restaurante',        'desc':'Cuchillos y comida.'},
    'furgon_policia':{'x':35,'y':25,'nombre':'Furgon Policial',     'desc':'Chalecos antibalas.'},
    'torre_radio':   {'x':0,'y':-60,'nombre':'Torre de Radio',      'desc':'Llama al helicoptero.'},
    'coche_escape':  {'x':70,'y':70,'nombre':'Coche Abandonado',    'desc':'Necesitas 5 gasolinas.'},
    'barco':         {'x':-50,'y':55,'nombre':'Barco en el Puerto', 'desc':'Necesitas piezas.'},
    'central_1':     {'x':30,'y':40,'nombre':'Central Electrica 1', 'desc':'Generador para la torre.'},
    'central_2':     {'x':-40,'y':-30,'nombre':'Central Electrica 2','desc':'Generador para la torre.'},
    'central_3':     {'x':50,'y':-20,'nombre':'Central Electrica 3', 'desc':'Generador para la torre.'},
    'central_4':     {'x':-20,'y':50,'nombre':'Central Electrica 4', 'desc':'Generador para la torre.'},
    'central_5':     {'x':10,'y':-50,'nombre':'Central Electrica 5', 'desc':'Generador para la torre.'},
}

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
    'inmunidad':     {'nombre':'Inmune',       'desc':'Infeccion 50% mas lenta.',  'coste':2,'cat':'supervivencia','req':'resistencia'},
    'carronero':     {'nombre':'Carronero',    'desc':'Mas creditos al matar.',    'coste':1,'cat':'recursos',     'req':None},
    'mochila_ext':   {'nombre':'Mochilero',    'desc':'+2 slots inventario.',      'coste':1,'cat':'recursos',     'req':None},
    'mochila_ext2':  {'nombre':'Cargador',     'desc':'+3 slots adicionales.',     'coste':2,'cat':'recursos',     'req':'mochila_ext'},
    'mochila_ext3':  {'nombre':'Camionero',    'desc':'+5 slots adicionales.',     'coste':3,'cat':'recursos',     'req':'mochila_ext2'},
    'ganzua':        {'nombre':'Cerrajero',    'desc':'+1 intento ganzua.',        'coste':2,'cat':'recursos',     'req':None},
    'recolector':    {'nombre':'Recolector',   'desc':'Mas loot en edificios.',    'coste':1,'cat':'recursos',     'req':None},
    'agricultura':   {'nombre':'Botanico',     'desc':'Plantas medicinales.',      'coste':1,'cat':'exploracion',  'req':None},
    'navegacion':    {'nombre':'Orientacion',  'desc':'Radio deteccion mayor.',    'coste':1,'cat':'exploracion',  'req':None},
    'velocidad':     {'nombre':'Corredor',     'desc':'Huida garantizada.',        'coste':2,'cat':'exploracion',  'req':None},
    'carisma':       {'nombre':'Carisma',      'desc':'Superv. dan item extra.',   'coste':2,'cat':'exploracion',  'req':None},
    'campista':      {'nombre':'Campista',     'desc':'Construye campamento base.','coste':3,'cat':'exploracion',  'req':'agricultura'},
}

TIPOS_ZOMBI = {
    'normal':   {'nombre':'Zombi',          'hp':35,'atk':12,'xp':35, 'inf':0.013,'color':'#ff3131','ef':None},
    'corredor': {'nombre':'Zombi Corredor', 'hp':22,'atk':18,'xp':45, 'inf':0.020,'color':'#ff8800','ef':None},
    'gordo':    {'nombre':'Zombi Bloated',  'hp':80,'atk':8, 'xp':60, 'inf':0.000,'color':'#8e44ad','ef':'explota'},
    'nuclear':  {'nombre':'Zombi Nuclear',  'hp':50,'atk':15,'xp':70, 'inf':0.010,'color':'#f1c40f','ef':'irradiado'},
    'soldado':  {'nombre':'Zombi Soldado',  'hp':65,'atk':22,'xp':80, 'inf':0.015,'color':'#c0392b','ef':None},
    'nino':     {'nombre':'Zombi Pequeno',  'hp':18,'atk':10,'xp':25, 'inf':0.018,'color':'#e74c3c','ef':'evasion'},
    'mutante':  {'nombre':'Zombi Mutante',  'hp':90,'atk':25,'xp':100,'inf':0.020,'color':'#2ecc71','ef':None},
    'toxico':   {'nombre':'Zombi Toxico',   'hp':40,'atk':14,'xp':55, 'inf':0.000,'color':'#27ae60','ef':'infectado'},
    'jefe':     {'nombre':'JEFE ZOMBI',     'hp':400,'atk':999,'xp':500,'inf':0.50,'color':'#ff0000','ef':'jefe'},
}

ZOMBI_POOL = {
    0:[('normal',100)],
    1:[('normal',70),('corredor',20),('gordo',10)],
    2:[('normal',50),('corredor',25),('gordo',10),('nuclear',8),('toxico',7)],
    3:[('normal',35),('corredor',20),('soldado',15),('nuclear',12),('toxico',10),('gordo',5),('nino',3)],
    4:[('normal',20),('soldado',20),('mutante',15),('nuclear',15),('toxico',12),('corredor',8),('gordo',5),('nino',5)],
}

ENFERMEDADES = {
    'gripe':       {'nombre':'Gripe',        'dano':1,'cada':20,'dura':60,'cura':'Antibioticos'},
    'intoxicacion':{'nombre':'Intoxicacion', 'dano':2,'cada':15,'dura':40,'cura':'Carbon Activado'},
    'neumonia':    {'nombre':'Neumonia',      'dano':2,'cada':12,'dura':80,'cura':'Antibioticos'},
    'parasitos':   {'nombre':'Parasitos',     'dano':1,'cada':18,'dura':70,'cura':'Antibioticos'},
}

LOOT_EDIFICIO = ['Trapo','Trapo','Botella vacia','Alcohol','Alcohol','Palo','Cuerda',
    'Chatarra metalica','Lata vacia','Lata de comida','Lata de comida','Venda','Venda',
    'Agua sucia','Gasolina','Cable','Azucar','Pastilla potabilizadora','Botiquin',
    'Antibioticos','Morfina','Cuchillo','Vial de Retencion','Pila','Cinta americana','Polvora',]
LOOT_CADAVER = ['Venda','Lata de comida','Trapo','Alcohol','Cuerda','Botiquin','Antibioticos',
    'Cuchillo','Gasolina','Chatarra metalica','Pila','Balas 9mm',]
LOOT_COCHE   = ['Gasolina','Gasolina','Chatarra metalica','Cuerda','Trapo','Lata de comida',
    'Venda','Botiquin','Cuchillo','Cable','Antibioticos','Alcohol','Vial de Retencion','Morfina','Balas 9mm',]

RECOMPENSAS_SUPERV = [
    ['Botiquin','Venda'],['Lata de comida','Agua Purificada'],['Cuchillo','Trapo'],
    ['Antibioticos','Venda'],['Gasolina','Botella vacia'],['Cuerda','Palo','Lata de comida'],
    ['Vial de Retencion'],['Racion Energetica','Agua Purificada'],
    ['Chatarra metalica','Cable'],['Balas 9mm','Balas 9mm'],
]
NOMBRES_SUPERV = ['Ana','Marcos','Lucia','Ivan','Sara','Dani','Carlos','Miren',
                   'Txema','Iker','Amaia','Gorka','Elena','Pablo','Nerea','Jon']

# MERCADERES ESPECÍFICOS
MERCADER_TIPOS = {
    'exmilitar':{'nombre':'[ARMAS]',     'color':'#cc4444','desc':'Ex-militar. Vende armas y municion.',
                'stock':['Pistola 9mm','Balas 9mm','Balas 9mm','Balas Rifle','Cuchillo','Hacha','Escopeta','Cartuchos'],
                'precios':{'Pistola 9mm':80,'Balas 9mm':15,'Balas Rifle':20,'Cuchillo':25,'Hacha':40,'Escopeta':120,'Cartuchos':25,'Flechas':12}},
    'buhonero':{'nombre':'[MATERIALES]','color':'#8888ff','desc':'Vende materiales de crafteo.',
                'stock':['Chatarra metalica','Cable','Pila','Cuerda','Trapo','Polvora','Cinta americana','Palo'],
                'precios':{'Chatarra metalica':8,'Cable':10,'Pila':15,'Cuerda':8,'Trapo':5,'Polvora':18,'Cinta americana':12,'Palo':3}},
    'senora':  {'nombre':'[COMIDA]',    'color':'#88ff88','desc':'Vende comida y medicinas.',
                'stock':['Lata de comida','Lata de comida','Agua Purificada','Racion Energetica','Botiquin','Venda','Antibioticos'],
                'precios':{'Lata de comida':12,'Agua Purificada':15,'Racion Energetica':20,'Botiquin':35,'Venda':8,'Antibioticos':40,'Morfina':60}},
    'chino':   {'nombre':'[BAZAR]',     'color':'#ffcc44','desc':'Vende de todo pero poco.',
                'stock':['Lata de comida','Balas 9mm','Venda','Trapo','Chatarra metalica','Botiquin'],
                'precios':{'Lata de comida':15,'Balas 9mm':20,'Venda':12,'Trapo':8,'Chatarra metalica':10,'Botiquin':45,'Gasolina':18}},
}

# NPCS con árboles de diálogo
# Cada NPC tiene: nombre, descripcion, zona_base (zona segura donde aparece), dialogos
# Cada dialogo: texto, opciones [ {texto, respuesta, accion} ]
NPCS = [
    {
        'id': 'mou5labs',
        'nombre': 'Mou5labs',
        'desc': 'Una voz en la radio estatica.',
        'zona_base': (0, 0),  # Parque Central
        'dialogos': {
            'inicio': {
                'texto': "Aqui Mou5labs. Hace 72 horas la realidad se fragmento. La detonacion en el reactor G-42 inicio el colapso global. Los ZOMBIES NUCLEARES son focos de infeccion viva. Tu terminal sigue activa. El protocolo C.R.T. es tu unica guia.",
                'opciones': [
                    {'texto': "Que es el reactor G-42?", 'siguiente': 'reactor'},
                    {'texto': "Como sobrevivo la infeccion?", 'siguiente': 'infeccion'},
                    {'texto': "Hay alguna forma de escapar?", 'siguiente': 'escape'},
                    {'texto': "Adios.", 'siguiente': None},
                ]
            },
            'reactor': {
                'texto': "El G-42 era un prototipo de fusion nuclear limpia. Fue saboteado. La radiacion que emite no es natural — reescribe el ADN en tiempo real. Los que no se sellaron a tiempo... ya no son personas.",
                'opciones': [
                    {'texto': "Quien lo saboteo?", 'siguiente': 'sabotaje'},
                    {'texto': "Volver.", 'siguiente': 'inicio'},
                ]
            },
            'sabotaje': {
                'texto': "No lo se con certeza. Pero la frecuencia de la explosion... era artificial. Coordinada. Alguien queria que esto pasara. Desconfia de cualquier rescate que no sea en frecuencia 147.3.",
                'opciones': [
                    {'texto': "Entendido.", 'siguiente': 'inicio'},
                ]
            },
            'infeccion': {
                'texto': "Los Viales de Retencion frenan la mutacion celular. No la curan — la detienen temporalmente. Si tu infeccion llega al 100%, el protocolo se aborta. No hay vuelta atras.",
                'opciones': [
                    {'texto': "Donde encuentro Viales?", 'siguiente': 'viales'},
                    {'texto': "Volver.", 'siguiente': 'inicio'},
                ]
            },
            'viales': {
                'texto': "Los sintetizaban en el Hospital y en los laboratorios de la Zona Industrial. Tambien los mercaderes los tienen... a precio de apocalipsis.",
                'opciones': [
                    {'texto': "Gracias.", 'siguiente': 'inicio'},
                ]
            },
            'escape': {
                'texto': "Tres rutas: el helicoptero de rescate requiere activar la torre de radio — pero primero necesitas 5 generadores activos y una radio artesanal. El barco en el Puerto necesita piezas de motor. Y hay un coche al este... si consigues gasolina.",
                'opciones': [
                    {'texto': "Como activo la torre de radio?", 'siguiente': 'torre'},
                    {'texto': "Volver.", 'siguiente': 'inicio'},
                ]
            },
            'torre': {
                'texto': "Activa 5 centrales electricas distribuidas por la ciudad. Luego construye una radio con chatarra y cable. Escala la torre y transmite. El helicoptero llegara en minutos. No en horas. MINUTOS.",
                'opciones': [
                    {'texto': "Entendido. Lo hare.", 'siguiente': None, 'accion': 'sp+1'},
                    {'texto': "Volver.", 'siguiente': 'inicio'},
                ]
            },
        }
    },
    {
        'id': 'dr_vega',
        'nombre': 'Dr. Vega',
        'desc': 'Cientifico nervioso con gafas rotas.',
        'zona_base': (0, 50),
        'dialogos': {
            'inicio': {
                'texto': "El virus no es biologico. Es una senal. Una frecuencia de radiacion que reescribe el ADN activo. He pasado tres dias estudiando muestras y... esto no es natural. Alguien lo disenyo.",
                'opciones': [
                    {'texto': "Quien lo disenyo?", 'siguiente': 'origen'},
                    {'texto': "Hay cura?", 'siguiente': 'cura'},
                    {'texto': "Necesitas algo?", 'siguiente': 'peticion'},
                    {'texto': "Adios.", 'siguiente': None},
                ]
            },
            'origen': {
                'texto': "No lo se. Pero la firma espectral de la radiacion... coincide con tecnologia de defensa clasifacada. Alguien con muchos recursos. Y sin escrúpulos.",
                'opciones': [
                    {'texto': "Impresionante.", 'siguiente': 'inicio'},
                ]
            },
            'cura': {
                'texto': "Tecnicamente si. Necesito muestras del nucleo del reactor G-42. Pero eso esta en la Zona Militar. Nivel de peligro: suicida. Los Viales que circulan solo retrasan lo inevitable.",
                'opciones': [
                    {'texto': "Lo intentare.", 'siguiente': 'inicio'},
                    {'texto': "Demasiado peligroso.", 'siguiente': 'inicio'},
                ]
            },
            'peticion': {
                'texto': "Antibioticos. Y si encuentras muestras de zombi irradiado — tejido, no el zombi entero por favor — traemelas. Te dare algo a cambio.",
                'opciones': [
                    {'texto': "De acuerdo.", 'siguiente': None, 'accion': 'info_hospital'},
                    {'texto': "Quiza mas tarde.", 'siguiente': None},
                ]
            },
        }
    },
    {
        'id': 'coronel_rax',
        'nombre': 'Coronel Rax',
        'desc': 'Militar de carrera. Mirada dura.',
        'zona_base': (50, 0),
        'dialogos': {
            'inicio': {
                'texto': "Soldado. El G-42 fue saboteado. Esto no fue un accidente. He visto los protocolos de evacuacion — estaban preparados. Alguien sabia lo que iba a pasar.",
                'opciones': [
                    {'texto': "Quien sabia?", 'siguiente': 'quien'},
                    {'texto': "Que hay en la Zona Militar?", 'siguiente': 'zona_militar'},
                    {'texto': "Cual es el plan?", 'siguiente': 'plan'},
                    {'texto': "Adios.", 'siguiente': None},
                ]
            },
            'quien': {
                'texto': "Los archivos clasificados estan en el bunker B-7 de la Zona Militar. Pero esta infestado. Nivel de acceso: mortal. Si llegas alli... trae los discos duros. La verdad tiene que salir.",
                'opciones': [
                    {'texto': "Lo intentare.", 'siguiente': None, 'accion': 'sp+1'},
                    {'texto': "Volver.", 'siguiente': 'inicio'},
                ]
            },
            'zona_militar': {
                'texto': "Armamento de alto nivel. Equipo de proteccion radiactiva. Y zombis soldado — los peores. Entrenados incluso en muerte. No entres sin blindaje completo.",
                'opciones': [
                    {'texto': "Gracias por el aviso.", 'siguiente': 'inicio'},
                ]
            },
            'plan': {
                'texto': "Supervivir. Documentar. Y si es posible: activar la torre de radio. El comando exterior aun no sabe la magnitud de esto. Necesitan saberlo.",
                'opciones': [
                    {'texto': "Estoy en ello.", 'siguiente': 'inicio'},
                ]
            },
        }
    },
    {
        'id': 'nina',
        'nombre': 'Nina',
        'desc': 'Nina de unos 12 annos. Asustada.',
        'zona_base': (-50, 0),
        'dialogos': {
            'inicio': {
                'texto': "Hola... no muerdas, verdad? Mi padre me dijo que esperara aqui. Eso fue hace dos dias. No ha vuelto.",
                'opciones': [
                    {'texto': "Donde fue tu padre?", 'siguiente': 'padre'},
                    {'texto': "Estas bien?", 'siguiente': 'estado'},
                    {'texto': "Tengo comida.", 'siguiente': 'comida', 'requiere': 'Lata de comida'},
                    {'texto': "Cuídate.", 'siguiente': None},
                ]
            },
            'padre': {
                'texto': "Al hospital. Dijo que habia suministros medicos ahi. Y que volveria antes de que oscureciera. Pero no volvio. Y ya han pasado dos noches.",
                'opciones': [
                    {'texto': "Ire a buscarlo.", 'siguiente': 'promesa'},
                    {'texto': "Lo siento.", 'siguiente': 'inicio'},
                ]
            },
            'promesa': {
                'texto': "De verdad? Gracias... se llama Ernesto. Llevaba una mochila azul. Y... ten cuidado. El hospital es... ya oigo cosas desde aqui.",
                'opciones': [
                    {'texto': "Lo encontrare.", 'siguiente': None, 'accion': 'sp+1'},
                ]
            },
            'estado': {
                'texto': "Tengo hambre. Y frio. Pero estoy bien. Encontre una botella de agua esta mannana. Y no vi a ninguno de esos... bichos. Creo que esta zona es segura.",
                'opciones': [
                    {'texto': "Aqui tienes algo.", 'siguiente': 'regalo', 'requiere': 'Lata de comida'},
                    {'texto': "Me alegra que estes bien.", 'siguiente': 'inicio'},
                ]
            },
            'comida': {
                'texto': "Oh! Gracias... muchisimas gracias. Llevaba tanta hambre. Toma esto — lo encontre pero no se para que sirve.",
                'opciones': [
                    {'texto': "De nada.", 'siguiente': None, 'accion': 'dar_item:Lata de comida:Vial de Retencion'},
                ]
            },
            'regalo': {
                'texto': "Oh! Gracias... muchisimas gracias. Llevaba tanta hambre. Toma esto — lo encontre pero no se para que sirve.",
                'opciones': [
                    {'texto': "De nada.", 'siguiente': None, 'accion': 'dar_item:Lata de comida:Vial de Retencion'},
                ]
            },
        }
    },
    {
        'id': 'marcus',
        'nombre': 'Marcus',
        'desc': 'Superviviente corpulento. Cicatrices recientes.',
        'zona_base': (0, -50),
        'dialogos': {
            'inicio': {
                'texto': "Otro vivo. Bien. Los numeros importan. He estado seis dias solo y puedo decirte: los primeros tres son los mas peligrosos. Despues aprendes los patrones.",
                'opciones': [
                    {'texto': "Que patrones?", 'siguiente': 'patrones'},
                    {'texto': "Donde hay loot bueno?", 'siguiente': 'loot'},
                    {'texto': "Como te llamas?", 'siguiente': 'presentacion'},
                    {'texto': "Adios.", 'siguiente': None},
                ]
            },
            'patrones': {
                'texto': "Los corredores atacan en manada de noche. Los soldados patrullan zonas fijas — si los ves, rodea. El jefe... ese no tiene patron. Cuando aparece, corres o tienes armadura completa.",
                'opciones': [
                    {'texto': "Util. Gracias.", 'siguiente': 'inicio'},
                ]
            },
            'loot': {
                'texto': "Los coches tienen gasolina y material. Los furgones policiales tienen chalecos si consigues abrirlos. Y el museo... ahi encontre algo que parece una espada antigua. No me cabe en la mochila.",
                'opciones': [
                    {'texto': "Ire al museo.", 'siguiente': None, 'accion': 'sp+1'},
                    {'texto': "Gracias.", 'siguiente': 'inicio'},
                ]
            },
            'presentacion': {
                'texto': "Marcus. Ex-bombero. Bueno, ex-todo ahora. Llevo seis dias buscando a mi equipo. Separados en la primera noche. Si los ves — tres tios con ropa naranja — diles que estoy en el parque.",
                'opciones': [
                    {'texto': "Lo hare.", 'siguiente': 'inicio'},
                ]
            },
        }
    },
]

# Para movimiento entre zonas seguras
def get_npc_posicion(npc, dia_actual):
    """Los NPCs rotan entre zonas seguras segun el dia. NO importa nada externo."""
    _zonas = [(0,0),(0,50),(-50,0),(50,0),(0,-50),(50,50),(-50,50),(50,-50),(-50,-50)]
    try:
        idx = NPCS.index(npc)
    except ValueError:
        idx = 0
    zona_idx = (idx + dia_actual) % len(_zonas)
    return _zonas[zona_idx]

def get_npcs_en_zona(p):
    """Devuelve NPCs presentes en la zona segura actual."""
    resultado = []
    for npc in NPCS:
        try:
            zx, zy = get_npc_posicion(npc, p.get('dias', 0))
            if abs(p['x'] - zx) <= 4 and abs(p['y'] - zy) <= 4:
                resultado.append(npc)
        except Exception:
            pass
    return resultado

# ==============================================================
# FUNCIONES
# ==============================================================
def get_refugio(x,y): return round(x/100)*100, round(y/100)*100
def obtener_distrito(x,y):
    dist=math.sqrt(x**2+y**2); ang=math.degrees(math.atan2(y,x))%360
    if dist<15: return 'Parque Central'
    if dist<38: return 'Centro Urbano'
    if 0<=ang<45 or 315<=ang<360: return 'Distrito Financiero'
    if 45<=ang<90:   return 'Zona Militar'
    if 90<=ang<135:  return 'Puerto Fluvial'
    if 135<=ang<180: return 'Hospital'
    if 180<=ang<225: return 'Zona Industrial'
    if 225<=ang<270: return 'Cementerio'
    if 270<=ang<315: return 'Barrio Residencial'
    return 'Periferia'

def es_zona_segura(x,y):
    return any(abs(x-zx)<=3 and abs(y-zy)<=3 for zx,zy in ZONAS_SEGURAS)

def recalcular_stats(p):
    p.setdefault('equipo',{'cabeza':None,'torso':None,'mano_der':None,'espalda':None,'pies':None})
    p['defensa']=0; p['evasion']=0.0; p['mordida_prot']=0.0
    for slot,item in p['equipo'].items():
        if item and item in OBJETOS:
            obj=OBJETOS[item]
            p['defensa']   += obj.get('defensa',0)
            p['evasion']   += obj.get('evasion',0.0)
            p['mordida_prot'] += obj.get('mordida_prot',0.0)
    b=0; sk=p.get('skills',[])
    if 'mochila_ext' in sk:  b+=2
    if 'mochila_ext2' in sk: b+=3
    if 'mochila_ext3' in sk: b+=5
    p['max_inventario']=5+b

def add_item(p,item):
    if len(p.get('inventario',[]))<p.get('max_inventario',5):
        p['inventario'].append(item); return True
    return False

def get_ammo_in_cargador(p):
    """Returns (ammo_in_mag, ammo_type) for equipped weapon."""
    arma = p.get('equipo',{}).get('mano_der','')
    if not arma or arma not in CARGADOR: return None, None
    ammo_type = OBJETOS.get(arma,{}).get('ammo_type')
    if not ammo_type: return None, None
    mag_size = CARGADOR[arma]
    cargador = p.get('cargador_actual', mag_size)
    return cargador, ammo_type

def consume_ammo(p):
    """Gasta 1 bala del cargador actual."""
    arma = p.get('equipo',{}).get('mano_der','')
    if arma not in CARGADOR: return True
    p['cargador_actual'] = p.get('cargador_actual', CARGADOR.get(arma, 1))
    if p['cargador_actual'] <= 0:
        return False  # necesita recargar
    p['cargador_actual'] -= 1
    return True

def can_attack_with_weapon(p):
    arma = p.get('equipo',{}).get('mano_der','')
    if not arma: return True  # puños
    if arma not in CARGADOR: return True  # cuerpo a cuerpo
    return p.get('cargador_actual', 1) > 0

def desgastar_arma(p, logs):
    """Reduce durabilidad del arma equipada."""
    arma = p.get('equipo',{}).get('mano_der')
    if not arma: return
    obj = OBJETOS.get(arma,{})
    max_dur = obj.get('dur')
    if max_dur is None: return  # indestructible
    dur_key = f'dur_{arma}'
    p[dur_key] = p.get(dur_key, max_dur) - 1
    if p[dur_key] <= 0:
        p['equipo']['mano_der'] = None
        recalcular_stats(p)
        logs.append(f"[!] {arma} se ha roto!")
    elif p[dur_key] <= 5:
        logs.append(f"[!] {arma} a punto de romperse ({p[dur_key]} usos).")

def spawn_zombi(p, tipo_forzado=None):
    dist=obtener_distrito(p['x'],p['y'])
    peligro=DISTRITOS.get(dist,{}).get('peligro',1)
    pool=ZOMBI_POOL.get(peligro, ZOMBI_POOL[1])
    tipo_k = tipo_forzado or random.choices([x[0] for x in pool],weights=[x[1] for x in pool])[0]
    tz=TIPOS_ZOMBI[tipo_k]; lvl=p.get('lvl',1)
    hp_f=tz['hp']+lvl*4
    return {'nombre':tz['nombre'],'tipo':tipo_k,'hp':hp_f,'hp_max':hp_f,
            'atk':tz['atk']+lvl,'xp':tz['xp'],'inf':tz['inf'],'color':tz['color'],'ef':tz['ef']}

def spawn_bandido(p):
    nombres=['Raul el Brutal','La Serpiente','Sombra','El Cojo','Mateo el Rojo','La Bruja','Santos']
    lvl=p.get('lvl',1)
    hp=40+lvl*6; atk=15+lvl*2
    return {'nombre':random.choice(nombres),'tipo':'bandido','hp':hp,'hp_max':hp,
            'atk':atk,'xp':60+lvl*5,'color':'#ff6600','ef':None,'inf':0.0}

def _juego_vars(p, lang='es'):
    d=obtener_distrito(p['x'],p['y']); rx,ry=get_refugio(p['x'],p['y'])
    recetas_disponibles = dict(RECETAS_BASE)
    for rid, rec in RECETAS_BIBLIOTECA.items():
        if rec['plano'] in p.get('inventario',[]) or rec['plano'] in p.get('planos_encontrados',[]):
            recetas_disponibles[rid] = rec
    return dict(
        distrito=d, info_distrito=DISTRITOS.get(d,{}),
        es_noche=(p['ciclo_pasos']>=100),
        en_refugio=(p['x']==rx and p['y']==ry),
        zona_segura=es_zona_segura(p['x'],p['y']),
        habs=HABILIDADES, distritos=DISTRITOS,
        zonas_seguras=ZONAS_SEGURAS, recetas=recetas_disponibles,
        enfermedades=ENFERMEDADES, locs=LOCS_ESPECIALES,
        npcs=get_npcs_en_zona(p),
        recetas_desc=RECETAS_DESC.get(lang, RECETAS_DESC['es']),
    )

def tick_infeccion(p, pasos=1):
    logs=[]
    if p.get('infeccion',0)>0:
        vel=0.5 if 'inmunidad' in p.get('skills',[]) else 1
        if p.get('vial_activo',0)>0:
            p['vial_activo']-=pasos
            if p['vial_activo']<=0: p['vial_activo']=0; logs.append("Vial expirado.")
        else:
            p['infeccion']=min(100,p['infeccion']+vel*pasos)
            if p['infeccion']>=100:
                p['hp']=0; p['log']="La infeccion te ha consumido."; return logs,True
        if p['infeccion']>=50 and p['pasos']%15==0:
            dmg=int((p['infeccion']-40)/10); p['hp']-=dmg; logs.append(f"Infeccion: -{dmg}HP")
    enfs=p.get('enfermedades_activas',{})
    for eid,edata in list(enfs.items()):
        edata['restante']-=pasos
        if edata['restante']<=0: del enfs[eid]; logs.append(f"{ENFERMEDADES[eid]['nombre']} curada."); continue
        if p['pasos']%ENFERMEDADES[eid]['cada']==0:
            p['hp']-=ENFERMEDADES[eid]['dano']; logs.append(f"{ENFERMEDADES[eid]['nombre']}: -{ENFERMEDADES[eid]['dano']}HP")
    return logs,False

def aplicar_mordisco(p, zombi):
    prot=p.get('mordida_prot',0.0)
    chance=max(0, zombi.get('inf',0.013)-prot)
    if random.random()<chance:
        p['infeccion']=min(100,p.get('infeccion',0)+(5 if p['infeccion']>0 else 1))
        return "MORDISCO INFECTADO." if p['infeccion']==1 else f"Mordisco +5% ({int(p['infeccion'])}%)"
    return None

def generar_evento(p, lang='es'):
    from traducciones import TEXTOS
    _t = TEXTOS.get(lang, TEXTOS['es'])
    dist=obtener_distrito(p['x'],p['y']); peligro=DISTRITOS.get(dist,{}).get('peligro',1)
    pool=[('superviviente',max(1,6-peligro)),('cadaver',2+peligro),('radio',2),('lluvia',2),('explosion',2)]
    if peligro>=2: pool+=[('trampa',3),('manada',peligro),('bandido',peligro)]
    if 'agricultura' in p.get('skills',[]): pool.append(('planta',4))
    tipo=random.choices([x[0] for x in pool],weights=[x[1] for x in pool])[0]
    if tipo=='superviviente':
        n=random.choice(NOMBRES_SUPERV); r=random.choice(RECOMPENSAS_SUPERV); ep=random.random()<0.5
        return {'tipo':'superviviente','nombre':n,'recompensa':r,'en_peligro':ep,'msj':_t.get('superviviente_acorralado','{nombre} esta acorralado.').replace('{nombre}',n) if ep else _t.get('superviviente_observa','{nombre} te observa.').replace('{nombre}',n)}
    elif tipo=='cadaver':
        loot=random.sample(LOOT_CADAVER,k=random.randint(1,2))
        return {'tipo':'cadaver','loot':loot,'msj':_t.get('cadaver_msj','Un cadaver reciente bloquea el camino.')}
    elif tipo=='trampa':
        d=random.randint(8,20); return {'tipo':'trampa','dano':d,'msj':_t.get('trampa_msj','Trampa de cables.') + f' -{d}HP.'}
    elif tipo=='radio':
        msgs=["'...sector 7... supervivientes...'","'PROTOCOLO OMEGA. EVACUACION CANCELADA.'","'...vacuna... laboratorio...'","'...papa no vuelve...'"]
        return {'tipo':'radio','msj':random.choice(msgs)}
    elif tipo=='lluvia':
        d=random.randint(3,10); return {'tipo':'lluvia','dano':d,'msj':_t.get('lluvia_msj','Lluvia acida.') + f' -{d}HP.'}
    elif tipo=='manada':
        n=random.randint(2,4); return {'tipo':'manada','n_zombis':n,'msj':_t.get('manada_msj','Manada de {n} zombis.').replace('{n}',str(n))}
    elif tipo=='explosion':
        return {'tipo':'explosion','msj':_t.get('explosion_msj','Explosion lejana. El suelo tiembla.')}
    elif tipo=='planta':
        it=random.choice(['Venda','Agua Purificada','Antibioticos'])
        return {'tipo':'planta','item':it,'msj':_t.get('planta_msj','Planta medicinal: {item}.').replace('{item}',it)}
    elif tipo=='bandido':
        b=spawn_bandido(p); b['_es_bandido']=True
        return {'tipo':'bandido','bandido':b,'msj':f"{b['nombre']} aparece con un arma."}
    return None

def _dar_recompensa_superv(p,inter):
    r=inter.get('recompensa',['Venda']); dados=[]
    for it in r:
        if add_item(p,it): dados.append(it)
    if 'carisma' in p.get('skills',[]):
        b=random.choice(['Lata de comida','Trapo','Alcohol','Vial de Retencion'])
        if add_item(p,b): dados.append(b)
    p['log']=f"{inter.get('nombre','Superv.')} recompensa: {', '.join(dados) if dados else '__mochila_llena__'}."
    p['exp']=p.get('exp',0)+20
    if p['exp']>=100:
        p['lvl']+=1; p['exp']%=100; p['sp']+=1; p['max_hp']+=10; p['hp']=p['max_hp']

# ==============================================================
# PARTES COMBATE
# ==============================================================
PARTES_BONUS={
    'cabeza':    {'mult':2.5,'ef':'aturdir'},  'torso':    {'mult':1.0,'ef':None},
    'brazo_izq': {'mult':0.7,'ef':'desarmar'}, 'brazo_der':{'mult':0.7,'ef':'desarmar'},
    'pierna_izq':{'mult':0.8,'ef':'ralentizar'},'pierna_der':{'mult':0.8,'ef':'ralentizar'},
}

# ==============================================================
# RUTAS
# ==============================================================
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in TEXTOS: session['lang']=lang
    return redirect(request.referrer or url_for('index'))

@app.route('/leaderboard')
def leaderboard():
    lang=session.get('lang','es')
    scores=cargar_ranking_db()
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
    cid=sanitize(request.form.get('clase',''))
    if cid not in CLASES: return redirect(url_for('index'))
    cd=CLASES[cid]; hp=cd['hp']; item=cd.get('item','')
    nombre=sanitize(request.form.get('nombre','Superviviente'))
    genero=sanitize(request.form.get('genero',''))
    lore=sanitize(request.form.get('lore',''),300)
    try: edad=max(1,min(120,int(request.form.get('edad',25))))
    except: edad=25
    guardar_personaje_db(nombre,genero,edad,cid,lore)
    # municion inicial por clase
    inv_inicial=[item] if item else []
    if cid in ('Policia','Policía','Militar'): inv_inicial.append('Balas 9mm')
    cargador_inicial = CARGADOR.get(item,0)
    session['p']={
        'nombre':nombre,'genero':genero,'edad':edad,'lore':lore,'clase':cid,
        'hp':hp,'max_hp':hp,'hambre':100,'dinero':50,
        'x':0,'y':0,'pasos':0,'ciclo_pasos':0,'dias':0,
        'lvl':1,'exp':0,'sp':0,'skills':[],
        'inventario':inv_inicial,'max_inventario':5,
        'estados':[],'dmg_base':10,'defensa':0,'evasion':0.0,'mordida_prot':0.0,
        'equipo':{'cabeza':None,'torso':None,'mano_der':None,'espalda':None,'pies':None},
        'cargador_actual': cargador_inicial,
        'enemigo':None,'mercader':None,'interaccion':None,
        'pasos_hambre_cero':0,'log_combate':[],
        'infeccion':0,'vial_activo':0,'enfermedades_activas':{},
        'generadores_activos':[],'radio_activa':False,
        'piezas_barco_recogidas':0,'gasolina_coche':0,'forma_escape':'',
        'campamento':None,'planos_encontrados':[],
        'muertes_mapa':_cargar_muertes(),
        'edificios_mapa':[{'x':random.randint(-60,60),'y':random.randint(-60,60),'saqueado':False} for _ in range(14)],
        'coches_mapa':[{'x':random.randint(-70,70),'y':random.randint(-70,70),'forzado':False} for _ in range(8)],
        'enemigos_mapa':[{'x':random.randint(-15,15),'y':random.randint(-15,15)} for _ in range(5)],
        'jefe_spawn':False,
        'tiempo_inicio': int(time.time()),
        'log':'__startup__',
    }
    # Equipar arma inicial si corresponde
    if item in OBJETOS:
        p2=session['p']; p2['equipo']['mano_der']=item; p2['inventario'].remove(item)
    return redirect(url_for('juego'))

@app.route('/juego')
def juego():
    p=session.get('p')
    if not p: return redirect(url_for('index'))
    lang=session.get('lang','es'); t_idioma=TEXTOS.get(lang,TEXTOS['es'])
    p['muertes_mapa']=_cargar_muertes()
    _backfill(p); session.modified=True
    return render_template('juego.html',p=p,t=t_idioma,**_juego_vars(p,lang))

def _backfill(p):
    p.setdefault('equipo',{'cabeza':None,'torso':None,'mano_der':None,'espalda':None,'pies':None})
    p.setdefault('defensa',0); p.setdefault('evasion',0.0); p.setdefault('mordida_prot',0.0)
    p.setdefault('log_combate',[]); p.setdefault('muertes_mapa',[])
    p.setdefault('infeccion',0); p.setdefault('vial_activo',0)
    p.setdefault('enfermedades_activas',{}); p.setdefault('coches_mapa',[])
    p.setdefault('cargador_actual',0); p.setdefault('generadores_activos',[])
    p.setdefault('radio_activa',False); p.setdefault('piezas_barco_recogidas',0)
    p.setdefault('gasolina_coche',0); p.setdefault('forma_escape','')
    p.setdefault('campamento',None); p.setdefault('planos_encontrados',[])
    p.setdefault('jefe_spawn',False); p.setdefault('tiempo_inicio',int(time.time()))
    p.setdefault('skills',[]); p.setdefault('estados',[]); p.setdefault('sp',0)
    p.setdefault('dmg_base',10); p.setdefault('mordida_prot',0.0)
    p.setdefault('pasos',0); p.setdefault('ciclo_pasos',0); p.setdefault('dias',0)
    p.setdefault('max_inventario',5); p.setdefault('inventario',[])
    p.setdefault('mercader',None); p.setdefault('enemigo',None); p.setdefault('interaccion',None)
    for ed in p.get('edificios_mapa',[]): ed.setdefault('saqueado',False)
    for c in p.get('coches_mapa',[]): c.setdefault('forzado',False)

def _cargar_muertes():
    if os.path.exists(DEATHS_FILE):
        try:
            with open(DEATHS_FILE,'r',encoding='utf-8') as f: return json.load(f)
        except: pass
    return []

def _guardar_muerte(nombre,x,y,dias,nivel):
    deaths=_cargar_muertes()
    deaths.append({'nombre':nombre,'x':x,'y':y,'dias':dias,'lvl':nivel})
    deaths=deaths[-20:]
    with open(DEATHS_FILE,'w',encoding='utf-8') as f: json.dump(deaths,f,indent=2)

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

    if p.get('superviviente_pendiente') and not p.get('enemigo'):
        sv=p.pop('superviviente_pendiente'); _dar_recompensa_superv(p,sv)

    if p['hambre']<=0:
        p['pasos_hambre_cero']=p.get('pasos_hambre_cero',0)+1
        if p['pasos_hambre_cero']>=740:
            p['hp']=0; p['log']="Muerte por inanicion."; return redirect(url_for('morir'))
    else: p['pasos_hambre_cero']=0
    tasa=10 if 'supervivencia2' in p.get('skills',[]) else (8 if 'supervivencia' in p.get('skills',[]) else 6)
    if p['pasos']%tasa==0:
        p['hambre']=max(0,p['hambre']-1)
        if p['hambre']<=0: p['hp']-=3

    if es_zona_segura(p['x'],p['y']):
        if p['hp']<p['max_hp']: p['hp']=min(p['max_hp'],p['hp']+2)

    inf_logs,muerte=tick_infeccion(p)
    if muerte: return redirect(url_for('morir'))
    if inf_logs: p['log']=inf_logs[-1]

    if random.random()<0.004:
        eid=random.choice(list(ENFERMEDADES.keys()))
        if eid not in p.get('enfermedades_activas',{}):
            p.setdefault('enfermedades_activas',{})[eid]={'restante':ENFERMEDADES[eid]['dura']}
            p['log']=f"Has contraido {ENFERMEDADES[eid]['nombre']}."

    # Jefe spawn ocasional en zonas peligrosas
    if not p.get('jefe_spawn') and p['pasos']>50 and random.random()<0.002:
        dist=obtener_distrito(p['x'],p['y'])
        if DISTRITOS.get(dist,{}).get('peligro',0)>=3:
            ox=random.choice([-8,-5,5,8]); oy=random.choice([-8,-5,5,8])
            p['enemigos_mapa'].append({'x':p['x']+ox,'y':p['y']+oy,'es_jefe':True})
            p['log']="__alerta_jefe__"; p['jefe_spawn']=True

    ddet=3 if 'sigilo' in p.get('skills',[]) else 6
    for z in list(p['enemigos_mapa']):
        if math.sqrt((p['x']-z['x'])**2+(p['y']-z['y'])**2)<ddet:
            if z['x']<p['x']: z['x']+=1
            elif z['x']>p['x']: z['x']-=1
            if z['y']<p['y']: z['y']+=1
            elif z['y']>p['y']: z['y']-=1
        if z['x']==p['x'] and z['y']==p['y']:
            tipo='jefe' if z.get('es_jefe') else None
            p['enemigo']=spawn_zombi(p, tipo)
            if tipo=='jefe': p['jefe_spawn']=False
            p['enemigos_mapa'].remove(z)
            p['log']=f"{p['enemigo']['nombre']} te intercepta!"
            session.modified=True; return redirect(url_for('juego'))
    while len(p['enemigos_mapa'])<5:
        ox=random.choice([-10,-8,8,10]); oy=random.choice([-10,-8,8,10])
        p['enemigos_mapa'].append({'x':p['x']+ox,'y':p['y']+oy})

    # Edificios normales
    for ed in p['edificios_mapa']:
        if ed['x']==p['x'] and ed['y']==p['y'] and not ed.get('saqueado'):
            p['interaccion']={'tipo':'edificio','msj':'Edificio detectado.','zombis':random.random()<0.3,'ed_x':ed['x'],'ed_y':ed['y']}
            session.modified=True; return redirect(url_for('juego'))

    # Coches
    for c in p['coches_mapa']:
        if c['x']==p['x'] and c['y']==p['y'] and not c.get('forzado'):
            combo=[random.choice(['w','a','s','d']) for _ in range(random.randint(4,6))]
            p['interaccion']={'tipo':'coche','msj':'Coche abandonado. Usar ganzua?','combo':combo,'intentos':0,
                              'max_intentos':3+('ganzua' in p.get('skills',[])), 'progreso':[],'c_x':c['x'],'c_y':c['y']}
            session.modified=True; return redirect(url_for('juego'))

    # Localizaciones especiales
    for loc_id, loc in LOCS_ESPECIALES.items():
        if abs(p['x']-loc['x'])<=2 and abs(p['y']-loc['y'])<=2:
            p['interaccion']={'tipo':'loc_especial','loc_id':loc_id,'nombre':loc['nombre'],'desc':loc['desc'],'msj':f"Encontraste: {loc['nombre']}. {loc['desc']}"}
            session.modified=True; return redirect(url_for('juego'))

    # Mercaderes tipo
    if p['pasos']%8==0 and not es_zona_segura(p['x'],p['y']):
        ev=generar_evento(p, session.get('lang','es'))
        if ev:
            if ev['tipo']=='lluvia': p['hp']=max(1,p['hp']-ev['dano']); p['log']=ev['msj']
            elif ev['tipo'] in ('explosion','radio'): p['log']=ev['msj']
            elif ev['tipo']=='planta':
                if add_item(p,ev['item']): p['log']=ev['msj']
                else: p['log']=ev['msj']+" (mochila llena)"
            elif ev['tipo']=='manada':
                for _ in range(ev['n_zombis']):
                    ox=random.choice([-6,-4,4,6]); oy=random.choice([-6,-4,4,6])
                    p['enemigos_mapa'].append({'x':p['x']+ox,'y':p['y']+oy})
                p['log']=ev['msj']
            elif ev['tipo']=='bandido':
                p['enemigo']=ev['bandido']; p['log']=ev['msj']
                session.modified=True; return redirect(url_for('juego'))
            else:
                p['interaccion']=ev

    if p['hp']<=0: return redirect(url_for('morir'))
    if p['ciclo_pasos']>=180:
        p['ciclo_pasos']=0; p['dias']+=1
        if random.random()<0.3:
            tipo_m=random.choice(list(MERCADER_TIPOS.keys()))
            info=MERCADER_TIPOS[tipo_m]
            stock=random.sample(info['stock'], min(4,len(info['stock'])))
            p['mercader']={'tipo':tipo_m,'nombre':info['nombre'],'color':info['color'],
                           'items':stock,'precios':info['precios'],'desc':info['desc']}
            p['log']=f"Mercader {info['nombre']} aparece al amanecer."
    session.modified=True; return redirect(url_for('juego'))

# --- DORMIR ---
@app.route('/dormir')
def dormir():
    p=session.get('p')
    if not p: return redirect(url_for('juego'))
    if p.get('enemigo') or p.get('interaccion') or p.get('mercader'):
        p['log']="__no_dormir_amenazas__"; session.modified=True; return redirect(url_for('juego'))
    es_noche=p['ciclo_pasos']>=100
    if not es_noche and not es_zona_segura(p['x'],p['y']):
        p['log']="__no_dormir_dia__"; session.modified=True; return redirect(url_for('juego'))
    pasos_salto=max(10,min(180-p['ciclo_pasos'],180))
    p['ciclo_pasos']=0; p['dias']+=1; p['pasos']+=pasos_salto
    regen=int(p['max_hp']*0.25); p['hp']=min(p['max_hp'],p['hp']+regen)
    p['hambre']=max(0,p['hambre']-15)
    inf_logs,muerte=tick_infeccion(p,pasos=pasos_salto)
    if muerte: return redirect(url_for('morir'))
    p['log']=f"Duermes hasta el amanecer. +{regen}HP."
    session.modified=True; return redirect(url_for('juego'))

# --- RECARGAR ---
@app.route('/recargar')
def recargar():
    """Recarga el arma si hay municion en inventario."""
    p=session.get('p')
    if not p: return redirect(url_for('juego'))
    arma=p.get('equipo',{}).get('mano_der','')
    if arma not in CARGADOR:
        p['log']="__arma_no_recarga__"; session.modified=True; return redirect(url_for('juego'))
    ammo_type=OBJETOS[arma].get('ammo_type')
    if ammo_type in p.get('inventario',[]):
        p['inventario'].remove(ammo_type)
        p['cargador_actual']=CARGADOR[arma]
        p['log']=f"Recargado. {CARGADOR[arma]} balas en {arma}."
    else:
        p['log']=f"Sin {ammo_type} en inventario."
    session.modified=True; return redirect(url_for('juego'))

# --- COMBATE ---
@app.route('/atacar')
@app.route('/atacar/<parte>')
def atacar(parte='torso'):
    p=session.get('p')
    if not p or not p.get('enemigo'): return redirect(url_for('juego'))
    enemigo=p['enemigo']; logs=p.get('log_combate',[]); bonus=PARTES_BONUS.get(parte,PARTES_BONUS['torso'])

    # Verificar municion
    if not can_attack_with_weapon(p):
        p['log']="SIN MUNICION. Recarga el arma."; session.modified=True; return redirect(url_for('juego'))

    dmg=p.get('dmg_base',10)+p.get('lvl',1)
    arma=p.get('equipo',{}).get('mano_der')
    if arma and arma in OBJETOS: dmg+=OBJETOS[arma].get('dmg',0)
    consume_ammo(p)
    dmg=int(dmg*bonus['mult'])
    # Especiales
    if arma:
        sp=OBJETOS.get(arma,{}).get('special')
        if sp=='doble_disparo': dmg=int(dmg*1.5); logs.append("DOBLE DISPARO!")
        elif sp=='quemado': logs.append("QUEMADO aplicado al zombi!")
        elif sp=='aturdir': logs.append("ATURDIDO!")
    if 'golpe_critico' in p.get('skills',[]) and random.random()<0.20:
        dmg*=2; logs.append(f"CRITICO! {parte.upper()} -{dmg}HP")
    else: logs.append(f"{parte.upper()} -{dmg}HP")
    desgastar_arma(p, logs)
    enemigo['hp']-=dmg

    if enemigo['hp']<=0:
        mult=1.5 if 'carronero' in p.get('skills',[]) else 1.0
        loot=int(random.randint(5,20)*mult); p['dinero']+=loot
        p['exp']=p.get('exp',0)+enemigo.get('xp',35)
        logs.append(f"Eliminado. +{enemigo.get('xp',35)}XP +{loot}CC")
        # DROPS
        drops=DROPS_JEFE if enemigo.get('tipo')=='jefe' else (DROPS_BANDIDO if enemigo.get('tipo')=='bandido' else LOOT_CADAVER)
        if random.random()<0.45:
            it=random.choice(drops)
            if add_item(p,it): logs.append(f"Drop: {it}")
        # Vampirismo
        if arma and OBJETOS.get(arma,{}).get('special')=='vampirismo':
            heal=int(p['max_hp']*0.10); p['hp']=min(p['max_hp'],p['hp']+heal); logs.append(f"VAMPIRISMO +{heal}HP")
        p['enemigo']=None
        if p.get('superviviente_pendiente'):
            sv=p.pop('superviviente_pendiente'); _dar_recompensa_superv(p,sv)
        if p['exp']>=100:
            p['lvl']+=1; p['exp']%=100; p['sp']+=1; p['max_hp']+=10; p['hp']=p['max_hp']; logs.append(f"NIVEL {p['lvl']}! +1SP")
    else:
        ev=p.get('evasion',0.0)
        if 'esquivar' in p.get('skills',[]): ev=max(ev,0.15)
        if enemigo.get('ef')=='evasion': ev=max(ev,0.25)
        if random.random()<ev: logs.append("__esquivaste__")
        else:
            dr=max(1,enemigo['atk']-p.get('defensa',0)); p['hp']-=dr; logs.append(f"{enemigo['nombre']}: -{dr}HP")
            inf_msg=aplicar_mordisco(p,enemigo)
            if inf_msg: logs.append(inf_msg)
            ef=enemigo.get('ef')
            if ef=='irradiado' and 'irradiado' not in p.get('estados',[]): p.setdefault('estados',[]).append('irradiado')
            if ef=='infectado': p['infeccion']=min(100,p.get('infeccion',0)+10); logs.append(f"Veneno: infeccion +10%")
            if ef=='explota' and enemigo['hp']<=0: p['hp']-=random.randint(10,20); logs.append("EXPLOSION!")
            if ef=='jefe' and p.get('defensa',0)<5:
                p['hp']=0; logs.append("EL JEFE TE HA MATADO DE UN GOLPE."); p['log_combate']=logs
                return redirect(url_for('morir'))
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
    mult=1.3 if 'medicina' in p.get('skills',[]) else 1.0
    if item=='Vial de Retencion':
        p['vial_activo']=p.get('vial_activo',0)+120; p['log']="Vial usado. Infeccion frenada 120 pasos."
        p['inventario'].remove(item); session.modified=True; return redirect(url_for('juego'))
    if item=='Antibioticos':
        cured=[]; enfs=p.get('enfermedades_activas',{})
        for eid in list(enfs.keys()):
            if ENFERMEDADES[eid]['cura']=='Antibioticos': del enfs[eid]; cured.append(eid)
        p['log']=f"Antibioticos: {', '.join(cured) if cured else 'sin efecto'}."
        p['inventario'].remove(item); session.modified=True; return redirect(url_for('juego'))
    if item=='Carbon Activado':
        enfs=p.get('enfermedades_activas',{})
        if 'intoxicacion' in enfs: del enfs['intoxicacion']
        p['log']="Carbon activado: intoxicacion curada."
        p['inventario'].remove(item); session.modified=True; return redirect(url_for('juego'))
    data=ITEMS_CURATIVOS.get(item,{})
    if data:
        # Riesgo carne de cadaver
        if data.get('riesgo',0)>0 and random.random()<data['riesgo']:
            eid=random.choice(['intoxicacion','parasitos'])
            p.setdefault('enfermedades_activas',{})[eid]={'restante':ENFERMEDADES[eid]['dura']}
            p['log']=f"{item} consumido pero... te has puesto malo. {ENFERMEDADES[eid]['nombre']}!"
            p['inventario'].remove(item); session.modified=True; return redirect(url_for('juego'))
        hpc=int((data.get('hp',0))*mult)
        p['hp']=min(p['max_hp'],p['hp']+hpc); p['hambre']=min(100,p['hambre']+data.get('hambre',0))
        p['log']=f"{item}: +{hpc}HP."
    else: p['log']=f"{item}: no consumible."
    p['inventario'].remove(item); session.modified=True; return redirect(url_for('juego'))

@app.route('/equipar_item/<item>')
def equipar_item(item):
    p=session.get('p')
    if not p or item not in p.get('inventario',[]): return redirect(url_for('juego'))
    p.setdefault('equipo',{'cabeza':None,'torso':None,'mano_der':None,'espalda':None,'pies':None})
    obj=OBJETOS.get(item,{}); slot=obj.get('slot','mano_der') if obj else 'mano_der'
    ant=p['equipo'].get(slot)
    if ant: p['inventario'].append(ant)
    p['equipo'][slot]=item; p['inventario'].remove(item)
    # cargador al equipar arma de fuego
    if item in CARGADOR: p['cargador_actual']=CARGADOR[item]
    recalcular_stats(p); p['log']=f"{item} equipado [{slot}]."
    session.modified=True; return redirect(url_for('juego'))

@app.route('/desequipar/<slot>')
def desequipar(slot):
    p=session.get('p')
    if not p: return redirect(url_for('juego'))
    p.setdefault('equipo',{'cabeza':None,'torso':None,'mano_der':None,'espalda':None,'pies':None})
    item=p['equipo'].get(slot)
    if item and len(p.get('inventario',[]))<p.get('max_inventario',5):
        p['inventario'].append(item); p['equipo'][slot]=None; recalcular_stats(p); p['log']=f"{item} desequipado."
    elif item: p['log']="__inv_lleno__"
    session.modified=True; return redirect(url_for('juego'))

# --- CRAFTEO ---
@app.route('/craftear/<receta_id>')
def craftear(receta_id):
    p=session.get('p')
    if not p: return redirect(url_for('juego'))
    from app_data import RECETAS_BASE, RECETAS_BIBLIOTECA
    todas={**RECETAS_BASE, **RECETAS_BIBLIOTECA}
    rec=todas.get(receta_id)
    if not rec: p['log']="__receta_desconocida__"; session.modified=True; return redirect(url_for('juego'))
    if rec.get('requiere_campamento') and not p.get('campamento'):
        p['log']="Necesitas un campamento para esto."; session.modified=True; return redirect(url_for('juego'))
    inv=list(p['inventario'])
    for mat,cant in rec['ingredientes']:
        if inv.count(mat)<cant:
            p['log']=f"Faltan: {cant}x {mat}"; session.modified=True; return redirect(url_for('juego'))
    for mat,cant in rec['ingredientes']:
        for _ in range(cant): inv.remove(mat)
    p['inventario']=inv
    if add_item(p,receta_id):
        p['log']=f"Crafteado: {receta_id}! +{rec.get('xp',10)}XP"
        p['exp']=p.get('exp',0)+rec.get('xp',10)
    else: p['log']="__inv_lleno__"
    session.modified=True; return redirect(url_for('juego'))

# --- EDIFICIOS ---
@app.route('/entrar_edificio')
def entrar_edificio():
    p=session.get('p')
    if not p or not p.get('interaccion'): return redirect(url_for('juego'))
    inter=p['interaccion']
    if inter.get('zombis'):
        p['enemigo']=spawn_zombi(p); p['log']=f"{p['enemigo']['nombre']} en el edificio!"
        p['interaccion']=None
    else:
        # Exploración interior con habitaciones
        n_hab=random.randint(2,3)
        habitaciones=random.sample(HABITACIONES, n_hab)
        inter['tipo']='interior'
        inter['habitaciones']=habitaciones
        inter['msj']=f"Entras al edificio. {n_hab} zonas a explorar."
    session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_edificio')
def ignorar_edificio():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="__edificio_ignorado__"
    session.modified=True; return redirect(url_for('juego'))

# --- LOCALIZACIONES ESPECIALES ---
@app.route('/entrar_loc_especial')
def entrar_loc_especial():
    p=session.get('p')
    if not p or not p.get('interaccion'): return redirect(url_for('juego'))
    inter=p['interaccion']; lid=inter.get('loc_id','')
    found=[]; msg=inter.get('nombre','Lugar desconocido')

    LOOT_LOC = {
        'museo':         [('Excalibur',0.3),('Winchester 1866',0.3),('Katana de Musashi',0.3),('Armadura de Estatua',0.5),('Plano: Ballesta',0.6)],
        'biblioteca':    [('Plano: Ballesta',0.7),('Plano: Machete',0.7),('Plano: Rifle Modificado',0.5),('Plano: Botiquin Mejorado',0.6),('Plano: Comida Cocinada',0.8)],
        'pitonisa':      [('Espada del Brujo',0.5),('Vial de Retencion',0.7),('Morfina',0.8)],
        'comic_store':   [('Espada de Blade',0.5),('Lata de comida',0.9),('Trapo',0.9)],
        'oficina':       [('Ebony & Ivory',0.4),('Balas 9mm',0.8),('Chatarra metalica',0.9)],
        'mansion':       [('Armadura de Mansion',0.6),('Casco Militar',0.7),('Botiquin',0.8)],
        'ropa_store':    [('Chaqueta de Motorista',0.7),('Trapo',0.9),('Cuerda',0.9)],
        'restaurante':   [('Cuchillo de cocina',0.8),('Cuchillo de cocina',0.6),('Lata de comida',0.9),('Alcohol',0.8)],
        'furgon_policia':[('Chaleco Antibalas',0.5),('Pistola 9mm',0.4),('Balas 9mm',0.7)],
        'torre_radio':   [],
        'coche_escape':  [],
        'barco':         [],
    }
    for cid in ['central_1','central_2','central_3','central_4','central_5']:
        LOOT_LOC[cid]=[]

    if lid in ('torre_radio',):
        if not p.get('radio_activa') and 'Radio' not in p.get('inventario',[]):
            p['log']="Necesitas una Radio artesanal para activar la torre."; p['interaccion']=None
            session.modified=True; return redirect(url_for('juego'))
        generadores=len(p.get('generadores_activos',[]))
        if generadores < 5:
            p['log']=f"Necesitas {5-generadores} generadores mas activos. ({generadores}/5 activos)"
            p['interaccion']=None; session.modified=True; return redirect(url_for('juego'))
        # Activa torre — ESCAPE
        p['radio_activa']=True; p['forma_escape']='Helicoptero'
        if 'Radio' in p['inventario']: p['inventario'].remove('Radio')
        p['log']="TORRE DE RADIO ACTIVADA. Helicoptero en camino. VE A ZONA SEGURA."; p['interaccion']=None
        session.modified=True
        return redirect(url_for('escapar', metodo='helicoptero'))

    elif lid.startswith('central_'):
        if lid not in p.get('generadores_activos',[]):
            p.setdefault('generadores_activos',[]).append(lid)
            n=len(p['generadores_activos'])
            p['log']=f"Generador activado. ({n}/5) {'TODOS LOS GENERADORES ACTIVOS!' if n>=5 else ''}"
        else:
            p['log']="__gen_ya_activo__"
        p['interaccion']=None; session.modified=True; return redirect(url_for('juego'))

    elif lid=='coche_escape':
        gas=p.get('gasolina_coche',0)
        if gas>=5:
            p['forma_escape']='Coche'; session.modified=True
            return redirect(url_for('escapar', metodo='coche'))
        else:
            gasolinas=[it for it in p.get('inventario',[]) if it=='Gasolina']
            if gasolinas:
                p['inventario'].remove('Gasolina'); p['gasolina_coche']=gas+1
                p['log']=f"Gasolina echada al coche. ({p['gasolina_coche']}/5)"
            else:
                p['log']=f"El coche necesita gasolina. ({gas}/5)"
        p['interaccion']=None; session.modified=True; return redirect(url_for('juego'))

    elif lid=='barco':
        piezas=p.get('piezas_barco_recogidas',0)
        # Buscar pieza en inventario
        if 'Pieza de Motor' in p.get('inventario',[]):
            p['inventario'].remove('Pieza de Motor'); piezas+=1; p['piezas_barco_recogidas']=piezas
            p['log']=f"Pieza instalada en el barco. ({piezas}/4)"
            if piezas>=4 and 'Combustible Marino' in p.get('inventario',[]):
                p['forma_escape']='Barco'; session.modified=True
                return redirect(url_for('escapar', metodo='barco'))
            elif piezas>=4:
                p['log']="Faltan piezas pero el barco casi esta listo. Necesitas Combustible Marino."
        else:
            p['log']=f"Barco necesita {4-piezas} Piezas de Motor y Combustible Marino."
        p['interaccion']=None; session.modified=True; return redirect(url_for('juego'))

    # Loot de localizacion
    for item,prob in LOOT_LOC.get(lid,[]):
        if random.random()<prob:
            if item.startswith('Plano:'):
                p.setdefault('planos_encontrados',[])
                if item not in p['planos_encontrados']: p['planos_encontrados'].append(item); found.append(item)
            else:
                if add_item(p,item): found.append(item)

    p['log']=f"{msg}: {', '.join(found) if found else 'nada esta vez'}."
    p['interaccion']=None; session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_loc_especial')
def ignorar_loc_especial():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="__te_alejas__"
    session.modified=True; return redirect(url_for('juego'))

# --- GANZÚA ---
@app.route('/ganzua_input/<tecla>')
def ganzua_input(tecla):
    p=session.get('p')
    if not p or not p.get('interaccion') or p['interaccion'].get('tipo')!='coche':
        return redirect(url_for('juego'))
    inter=p['interaccion']; combo=inter['combo']; prog=inter.get('progreso',[])
    idx=len(prog)
    if idx>=len(combo): session.modified=True; return redirect(url_for('juego'))
    if tecla==combo[idx]:
        prog.append(tecla); inter['progreso']=prog
        if len(prog)==len(combo):
            found=[]; extra=random.randint(5,20); p['dinero']+=extra
            for _ in range(random.randint(2,4)):
                it=random.choice(LOOT_COCHE)
                if add_item(p,it): found.append(it)
            p['log']=f"Coche abierto! {', '.join(found) if found else 'vacio'}. +{extra}CC"
            for c in p['coches_mapa']:
                if c.get('x')==inter.get('c_x') and c.get('y')==inter.get('c_y'): c['forzado']=True
            p['interaccion']=None
    else:
        inter['intentos']=inter.get('intentos',0)+1; inter['progreso']=[]
        if inter['intentos']>=inter.get('max_intentos',3):
            p['log']="__ganzua_rota__"
            for c in p['coches_mapa']:
                if c.get('x')==inter.get('c_x') and c.get('y')==inter.get('c_y'): c['forzado']=True
            p['interaccion']=None
        else:
            p['log']=f"Fallo. {inter['max_intentos']-inter['intentos']} intentos."
    session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_coche')
def ignorar_coche():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="__coche_ignorado__"
    session.modified=True; return redirect(url_for('juego'))

# --- SUPERVIVIENTES ---
@app.route('/rescatar_superviviente')
def rescatar_superviviente():
    p=session.get('p')
    if not p or not p.get('interaccion'): return redirect(url_for('juego'))
    inter=p['interaccion']
    if inter.get('en_peligro'):
        p['enemigo']=spawn_zombi(p); p['log']=f"Zombis mientras rescatas a {inter['nombre']}!"
        p['superviviente_pendiente']=inter; p['interaccion']=None
    else:
        _dar_recompensa_superv(p,inter); p['interaccion']=None
    session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_superviviente')
def ignorar_superviviente():
    p=session.get('p')
    if p: n=p.get('interaccion',{}).get('nombre','?'); p['interaccion']=None; p['log']=f"Ignoras a {n}."
    session.modified=True; return redirect(url_for('juego'))

@app.route('/registrar_cadaver')
def registrar_cadaver():
    p=session.get('p')
    if not p or not p.get('interaccion'): return redirect(url_for('juego'))
    inter=p['interaccion']; dados=[]
    for it in inter.get('loot',[]): 
        if add_item(p,it): dados.append(it)
    p['log']=f"Cadaver: {', '.join(dados) if dados else '__nada_util__'}."; p['interaccion']=None
    session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_cadaver')
def ignorar_cadaver():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="__rodeas_cadaver__"
    session.modified=True; return redirect(url_for('juego'))

@app.route('/evitar_trampa')
def evitar_trampa():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="__rodeas_trampa__"
    session.modified=True; return redirect(url_for('juego'))

@app.route('/ignorar_interaccion')
def ignorar_interaccion():
    p=session.get('p')
    if p: p['interaccion']=None; p['log']="__sigues_adelante__"
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
        else: p['log']="__inv_lleno__"
    else: p['log']="__cred_insuf__"
    session.modified=True; return redirect(url_for('juego'))

@app.route('/cerrar_mercader')
def cerrar_mercader():
    p=session.get('p')
    if p: p['mercader']=None
    session.modified=True; return redirect(url_for('juego'))

# --- CAMPAMENTO ---
@app.route('/construir_campamento')
def construir_campamento():
    p=session.get('p')
    if not p: return redirect(url_for('juego'))
    if 'campista' not in p.get('skills',[]):
        p['log']="__necesitas_campista__"; session.modified=True; return redirect(url_for('juego'))
    materiales=['Palo','Palo','Trapo','Cuerda']
    for m in materiales:
        if m not in p.get('inventario',[]): p['log']=f"Necesitas: {', '.join(materiales)}."; session.modified=True; return redirect(url_for('juego'))
    for m in materiales: p['inventario'].remove(m)
    p['campamento']={'x':p['x'],'y':p['y'],'granja':False}
    p['log']="__campamento_construido__"
    session.modified=True; return redirect(url_for('juego'))

# --- MAPA ---
@app.route('/mapa')
def mapa():
    p=session.get('p')
    if not p: return redirect(url_for('index'))
    lang=session.get('lang','es'); t_idioma=TEXTOS.get(lang,TEXTOS['es'])
    rx,ry=get_refugio(p['x'],p['y']); dist_ref=int(math.sqrt((p['x']-rx)**2+(p['y']-ry)**2))
    d=obtener_distrito(p['x'],p['y']); p['muertes_mapa']=_cargar_muertes()
    lang_mapa=session.get('lang','es')
    recetas_disp = dict(RECETAS_BASE)
    for rid, rec in RECETAS_BIBLIOTECA.items():
        if rec['plano'] in p.get('inventario',[]) or rec['plano'] in p.get('planos_encontrados',[]):
            recetas_disp[rid] = rec
    return render_template('mapa.html',p=p,t=t_idioma,distrito=d,info_distrito=DISTRITOS.get(d,{}),
        es_noche=(p['ciclo_pasos']>=100),rx=rx,ry=ry,dist_refugio=dist_ref,
        distritos=DISTRITOS,zonas_seguras=ZONAS_SEGURAS,locs=LOCS_ESPECIALES,
        recetas=recetas_disp,enfermedades=ENFERMEDADES,npcs=get_npcs_en_zona(p),
        recetas_desc=RECETAS_DESC.get(lang_mapa, RECETAS_DESC['es']))

# --- ESCAPE ---
@app.route('/escapar/<metodo>')
def escapar(metodo):
    p=session.get('p')
    if not p: return redirect(url_for('index'))
    lang=session.get('lang','es'); t=TEXTOS.get(lang,TEXTOS['es'])
    tiempo_jugado=int(time.time())-p.get('tiempo_inicio',int(time.time()))
    guardar_ranking_db(p['nombre'],p.get('genero',''),p.get('edad',0),p['dias'],p.get('lvl',1),tiempo_jugado,metodo)
    _guardar_muerte(p['nombre'],p['x'],p['y'],p['dias'],p.get('lvl',1))
    session.pop('p',None)
    return render_template('victoria.html',t=t,metodo=metodo,tiempo=tiempo_jugado)

# --- SUICIDIO ---
@app.route('/suicidio')
def suicidio():
    p=session.get('p')
    if p: p['hp']=0; return redirect(url_for('morir'))
    return redirect(url_for('index'))

# --- MUERTE ---
@app.route('/morir')
def morir():
    p=session.get('p')
    if p:
        tiempo_jugado=int(time.time())-p.get('tiempo_inicio',int(time.time()))
        guardar_ranking_db(p['nombre'],p.get('genero',''),p.get('edad',0),p['dias'],p.get('lvl',1),tiempo_jugado,'Muerte')
        _guardar_muerte(p['nombre'],p['x'],p['y'],p['dias'],p.get('lvl',1))
    session.pop('p',None)
    return render_template('muerte.html',t=TEXTOS[session.get('lang','es')])

# ============================================================
# MINIJUEGO RECARGA — inicia la interacción de recarga
# ============================================================
@app.route('/iniciar_recarga')
def iniciar_recarga():
    p = session.get('p')
    if not p: return redirect(url_for('juego'))
    arma = p.get('equipo', {}).get('mano_der', '')
    if arma not in CARGADOR:
        p['log'] = "__arma_no_municion__"; session.modified = True; return redirect(url_for('juego'))
    from app_data import TIPOS_MUNICION
    ammo_type = None
    for at, info in TIPOS_MUNICION.items():
        if arma in info['armas']:
            ammo_type = at; break
    if not ammo_type:
        p['log'] = "__sin_tipo_municion__"; session.modified = True; return redirect(url_for('juego'))
    if ammo_type not in p.get('inventario', []):
        p['log'] = f"Sin {ammo_type} en mochila."; session.modified = True; return redirect(url_for('juego'))
    # Generar secuencia de recarga (3-4 teclas)
    seq = [random.choice(['w','a','s','d']) for _ in range(random.randint(3, 4))]
    p['interaccion'] = {
        'tipo': 'recarga',
        'arma': arma,
        'ammo_type': ammo_type,
        'combo': seq,
        'progreso': [],
        'intentos': 0,
        'max_intentos': 2,
        'msj': f"Recargando {arma}. Introduce la secuencia.",
    }
    session.modified = True; return redirect(url_for('juego'))

@app.route('/recarga_input/<tecla>')
def recarga_input(tecla):
    p = session.get('p')
    if not p or not p.get('interaccion') or p['interaccion'].get('tipo') != 'recarga':
        return redirect(url_for('juego'))
    inter = p['interaccion']
    combo = inter['combo']; prog = inter.get('progreso', [])
    idx = len(prog)
    if idx >= len(combo):
        session.modified = True; return redirect(url_for('juego'))

    if tecla == combo[idx]:
        prog.append(tecla); inter['progreso'] = prog
        if len(prog) == len(combo):
            # ÉXITO
            arma = inter['arma']; ammo_type = inter['ammo_type']
            if ammo_type in p.get('inventario', []):
                p['inventario'].remove(ammo_type)
                p['cargador_actual'] = CARGADOR[arma]
                p['log'] = f"Recarga completada. {CARGADOR[arma]} balas en {arma}."
            p['interaccion'] = None
    else:
        inter['intentos'] = inter.get('intentos', 0) + 1; inter['progreso'] = []
        if inter['intentos'] >= inter.get('max_intentos', 2):
            # FALLO TOTAL — atraen zombis
            p['log'] = "Recarga fallida. El ruido atrae zombis."
            for _ in range(2):
                ox = random.choice([-5,-3,3,5]); oy = random.choice([-5,-3,3,5])
                p['enemigos_mapa'].append({'x': p['x']+ox, 'y': p['y']+oy})
            p['interaccion'] = None
        else:
            restantes = inter['max_intentos'] - inter['intentos']
            p['log'] = f"Tecla incorrecta. Reinicia. {restantes} intento(s) restante(s)."

    session.modified = True; return redirect(url_for('juego'))

# ============================================================
# ESCALAR TORRE DE RADIO — minijuego de escalada
# ============================================================
@app.route('/escalar_torre')
def escalar_torre():
    p = session.get('p')
    if not p: return redirect(url_for('juego'))
    # Requiere Cuerda en inventario o habilidad
    if 'Cuerda' not in p.get('inventario', []):
        p['log'] = "__necesitas_cuerda__"; session.modified = True; return redirect(url_for('juego'))
    # Activar minijuego de escalada
    p['interaccion'] = {
        'tipo': 'escalar_torre',
        'altura': 0,
        'max_altura': 10,
        'fuerza': 0,
        'fallos': 0,
        'max_fallos': 3,
        'combo_actual': [random.choice(['w','a','s','d']) for _ in range(3)],
        'progreso': [],
        'msj': "Escalas la torre de radio. Sigue la secuencia para subir.",
    }
    session.modified = True; return redirect(url_for('juego'))

@app.route('/escalar_input/<tecla>')
def escalar_input(tecla):
    p = session.get('p')
    if not p or not p.get('interaccion') or p['interaccion'].get('tipo') != 'escalar_torre':
        return redirect(url_for('juego'))
    inter = p['interaccion']
    combo = inter['combo_actual']; prog = inter.get('progreso', [])
    idx = len(prog)

    if tecla == combo[idx]:
        prog.append(tecla); inter['progreso'] = prog
        if len(prog) == len(combo):
            # Subiste un tramo
            inter['altura'] = inter.get('altura', 0) + 1
            inter['progreso'] = []
            inter['combo_actual'] = [random.choice(['w','a','s','d']) for _ in range(3)]
            if inter['altura'] >= inter['max_altura']:
                # Llegaste arriba
                p['log'] = "¡Llegaste a lo alto de la torre! Activas el transmisor."
                p['interaccion'] = {'tipo': 'loc_especial', 'loc_id': 'torre_radio',
                                    'nombre': 'Torre de Radio', 'desc': 'Activa el transmisor.'}
                if 'Cuerda' in p['inventario']: p['inventario'].remove('Cuerda')
            else:
                inter['msj'] = f"Subiendo... {inter['altura']}/{inter['max_altura']}"
        else:
            inter['msj'] = f"Bien. Siguiente: {''.join(combo[len(prog):]).upper()}"
    else:
        # Fallo → caída
        inter['fallos'] = inter.get('fallos', 0) + 1
        caida_dmg = random.randint(5, 15) * (inter.get('altura', 0) + 1)
        p['hp'] = max(1, p['hp'] - caida_dmg)
        p['log'] = f"Te resbalaas y caes. -{caida_dmg}HP."
        inter['altura'] = max(0, inter.get('altura', 0) - 1)
        inter['progreso'] = []
        inter['combo_actual'] = [random.choice(['w','a','s','d']) for _ in range(3)]
        if inter['fallos'] >= inter['max_fallos']:
            caida_fatal = random.randint(15, 35)
            p['hp'] = max(0, p['hp'] - caida_fatal)
            p['log'] = f"Caida grave desde la torre. -{caida_fatal}HP. Abandonas la escalada."
            p['interaccion'] = None
            if p['hp'] <= 0: return redirect(url_for('morir'))

    session.modified = True; return redirect(url_for('juego'))

# ============================================================
# EXPLORACIÓN INTERIOR DE EDIFICIOS
# ============================================================
HABITACIONES = [
    {'nombre': 'Cocina',       'loot': ['Cuchillo de cocina','Lata de comida','Agua sucia','Cuchillo de cocina'], 'zombi': 0.2},
    {'nombre': 'Oficina',      'loot': ['Chatarra metalica','Cable','Pila','Balas 9mm','Trapo'],                  'zombi': 0.3},
    {'nombre': 'Dormitorio',   'loot': ['Venda','Trapo','Racion Energetica','Cuerda'],                            'zombi': 0.25},
    {'nombre': 'Sótano',       'loot': ['Gasolina','Polvora','Chatarra metalica','Pila','Botiquin'],              'zombi': 0.5},
    {'nombre': 'Baño',         'loot': ['Antibioticos','Alcohol','Venda','Carbon Activado'],                      'zombi': 0.15},
    {'nombre': 'Almacén',      'loot': ['Lata de comida','Lata de comida','Cuerda','Trapo','Palo'],               'zombi': 0.35},
    {'nombre': 'Laboratorio',  'loot': ['Antibioticos','Morfina','Vial de Retencion','Carbon Activado'],          'zombi': 0.6},
    {'nombre': 'Armería',      'loot': ['Balas 9mm','Balas Rifle','Cartuchos','Cuchillo','Hacha'],                'zombi': 0.7},
]

@app.route('/explorar_interior')
def explorar_interior():
    p = session.get('p')
    if not p or not p.get('interaccion'): return redirect(url_for('juego'))
    # Generar 2-3 habitaciones para explorar
    n_hab = random.randint(2, 3)
    habitaciones = random.sample(HABITACIONES, n_hab)
    p['interaccion']['tipo'] = 'interior'
    p['interaccion']['habitaciones'] = habitaciones
    p['interaccion']['hab_idx'] = 0
    p['interaccion']['msj'] = f"Entras al edificio. {n_hab} zonas detectadas."
    session.modified = True; return redirect(url_for('juego'))

@app.route('/entrar_habitacion/<int:idx>')
def entrar_habitacion(idx):
    p = session.get('p')
    if not p or not p.get('interaccion') or p['interaccion'].get('tipo') != 'interior':
        return redirect(url_for('juego'))
    inter = p['interaccion']
    habs = inter.get('habitaciones', [])
    if idx >= len(habs):
        p['interaccion'] = None; session.modified = True; return redirect(url_for('juego'))
    hab = habs[idx]
    if hab.get('visitada'):
        p['log'] = f"{hab['nombre']}: ya explorada."; session.modified = True; return redirect(url_for('juego'))
    hab['visitada'] = True
    if random.random() < hab['zombi']:
        p['enemigo'] = spawn_zombi(p)
        p['log'] = f"{hab['nombre']}: ¡{p['enemigo']['nombre']} agazapado!"
        p['interaccion'] = None
    else:
        found = []; loot_pool = hab['loot']
        for _ in range(random.randint(1, 3)):
            it = random.choice(loot_pool)
            if add_item(p, it): found.append(it)
        p['log'] = f"{hab['nombre']}: {', '.join(found) if found else '__nada_util__'}."
    session.modified = True; return redirect(url_for('juego'))

@app.route('/salir_interior')
def salir_interior():
    p = session.get('p')
    if p:
        inter = p.get('interaccion', {})
        # Marcar edificio como saqueado
        for ed in p.get('edificios_mapa', []):
            if ed.get('x') == inter.get('ed_x') and ed.get('y') == inter.get('ed_y'):
                ed['saqueado'] = True
        p['interaccion'] = None; p['log'] = "__sales_edificio__"
    session.modified = True; return redirect(url_for('juego'))

# ============================================================
# NPC HABLAR
# ============================================================
@app.route('/hablar_npc/<npc_id>')
def hablar_npc(npc_id):
    p = session.get('p')
    if not p: return redirect(url_for('juego'))
    npc = next((n for n in NPCS if n['id'] == npc_id), None)
    if npc:
        dialogo_id = p.get(f'npc_dialogo_{npc_id}', 'inicio')
        dialogo = npc['dialogos'].get(dialogo_id, npc['dialogos']['inicio'])
        p['interaccion'] = {
            'tipo': 'npc', 'npc_id': npc_id,
            'nombre': npc['nombre'], 'desc': npc['desc'],
            'texto': dialogo['texto'],
            'opciones': dialogo.get('opciones', []),
            'dialogo_id': dialogo_id,
        }
    session.modified = True; return redirect(url_for('juego'))

@app.route('/npc_opcion/<npc_id>/<int:opt_idx>')
def npc_opcion(npc_id, opt_idx):
    p = session.get('p')
    if not p: return redirect(url_for('juego'))
    npc = next((n for n in NPCS if n['id'] == npc_id), None)
    if not npc:
        p['interaccion'] = None; session.modified = True; return redirect(url_for('juego'))
    inter = p.get('interaccion', {})
    dialogo_id = inter.get('dialogo_id', 'inicio')
    dialogo = npc['dialogos'].get(dialogo_id, npc['dialogos']['inicio'])
    opciones = dialogo.get('opciones', [])
    if opt_idx >= len(opciones):
        p['interaccion'] = None; session.modified = True; return redirect(url_for('juego'))
    opcion = opciones[opt_idx]

    # Check requisito
    req = opcion.get('requiere')
    if req and req not in p.get('inventario', []):
        p['log'] = f"Necesitas {req} para esta opcion."; session.modified = True; return redirect(url_for('juego'))

    # Procesar accion
    accion = opcion.get('accion')
    if accion:
        if accion == 'sp+1':
            p['sp'] = p.get('sp', 0) + 1
            p['log'] = "El NPC te ha recompensado con 1 SP."
        elif accion.startswith('dar_item:'):
            partes = accion.split(':')
            costo = partes[1] if len(partes) > 1 else None
            recompensa = partes[2] if len(partes) > 2 else None
            if costo and costo in p.get('inventario', []):
                p['inventario'].remove(costo)
            if recompensa:
                if add_item(p, recompensa):
                    p['log'] = f"Recibes: {recompensa}."
                else:
                    p['log'] = f"Inventario lleno, no puedes recibir {recompensa}."
        elif accion == 'info_hospital':
            p['log'] = "Dr. Vega: 'El hospital esta en el Hospital, al sureste. Mucho cuidado.'"

    # Siguiente dialogo
    siguiente = opcion.get('siguiente')
    if siguiente is None:
        p['interaccion'] = None
    else:
        sig_dialogo = npc['dialogos'].get(siguiente, npc['dialogos']['inicio'])
        p[f'npc_dialogo_{npc_id}'] = siguiente
        p['interaccion'] = {
            'tipo': 'npc', 'npc_id': npc_id,
            'nombre': npc['nombre'], 'desc': npc['desc'],
            'texto': sig_dialogo['texto'],
            'opciones': sig_dialogo.get('opciones', []),
            'dialogo_id': siguiente,
        }
    session.modified = True; return redirect(url_for('juego'))

@app.route('/cerrar_npc')
def cerrar_npc():
    p = session.get('p')
    if p: p['interaccion'] = None
    session.modified = True; return redirect(url_for('juego'))

# ============================================================
# CAMPAMENTO — GRANJA
# ============================================================
@app.route('/construir_granja')
def construir_granja():
    p = session.get('p')
    if not p: return redirect(url_for('juego'))
    if not p.get('campamento'):
        p['log'] = "__necesitas_campamento__"; session.modified = True; return redirect(url_for('juego'))
    if 'agricultura' not in p.get('skills', []):
        p['log'] = "__necesitas_botanico__"; session.modified = True; return redirect(url_for('juego'))
    if p['campamento'].get('granja'):
        p['log'] = "__ya_tienes_granja__"; session.modified = True; return redirect(url_for('juego'))
    mats = ['Palo', 'Palo', 'Trapo', 'Agua sucia']
    for m in mats:
        if m not in p.get('inventario', []):
            p['log'] = f"Faltan materiales: {', '.join(mats)}"; session.modified = True; return redirect(url_for('juego'))
    for m in mats: p['inventario'].remove(m)
    p['campamento']['granja'] = True
    p['campamento']['granja_pasos'] = p['pasos']
    p['log'] = "Granja construida. Cosecharas cada 40 pasos."
    session.modified = True; return redirect(url_for('juego'))

@app.route('/cosechar_granja')
def cosechar_granja():
    p = session.get('p')
    if not p: return redirect(url_for('juego'))
    camp = p.get('campamento', {})
    if not camp or not camp.get('granja'):
        p['log'] = "__sin_granja__"; session.modified = True; return redirect(url_for('juego'))
    pasos_desde = p['pasos'] - camp.get('granja_pasos', 0)
    if pasos_desde < 40:
        p['log'] = f"La granja no esta lista. {40-pasos_desde} pasos mas."; session.modified = True; return redirect(url_for('juego'))
    cosecha = random.choice(['Lata de comida', 'Agua sucia', 'Racion Energetica', 'Trapo'])
    n = 2 if 'agricultura' in p.get('skills', []) else 1
    added = []
    for _ in range(n):
        if add_item(p, cosecha): added.append(cosecha)
    camp['granja_pasos'] = p['pasos']
    p['log'] = f"Cosecha: {', '.join(added) if added else '__mochila_llena__'}."
    session.modified = True; return redirect(url_for('juego'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)