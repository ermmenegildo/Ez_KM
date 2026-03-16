# -*- coding: utf-8 -*-

CLASES = {
    'Policía':         {'hp': 110, 'item': 'Pistola 9mm',  'desc': 'Arma de fuego inicial. Alta cadencia.'},
    'Médico':          {'hp': 100, 'item': 'Botiquín',      'desc': 'Curación avanzada. Sana más HP.'},
    'Militar':         {'hp': 130, 'item': 'Cuchillo',      'desc': 'Combate cuerpo a cuerpo experto.'},
    'Leñador':         {'hp': 140, 'item': 'Hacha',         'desc': 'Máxima resistencia física.'},
    'Vagabundo':       {'hp': 90,  'item': 'Lata de comida','desc': 'Conoce los callejones. +Sigilo.'},
    'Artista Marcial': {'hp': 120, 'item': 'Vendas',        'desc': 'Cuerpo como arma. Alta evasión.'},
    'Catedrático':     {'hp': 80,  'item': 'Mapa',          'desc': 'Conocimiento táctico. +XP global.'},
    'Agricultor':      {'hp': 115, 'item': 'Azada',         'desc': 'Supervivencia rural. Cultiva rápido.'}
}

OBJETOS = {
    'Pistola 9mm':    {'tipo': 'arma',   'dmg': 40, 'slot': 'mano_der'},
    'Rifle':          {'tipo': 'arma',   'dmg': 55, 'slot': 'mano_der'},
    'Escopeta':       {'tipo': 'arma',   'dmg': 70, 'slot': 'mano_der'},
    'Hacha':          {'tipo': 'arma',   'dmg': 25, 'slot': 'mano_der'},
    'Cuchillo':       {'tipo': 'arma',   'dmg': 15, 'slot': 'mano_der'},
    'Katana':         {'tipo': 'arma',   'dmg': 35, 'slot': 'mano_der'},
    'Machete':        {'tipo': 'arma',   'dmg': 28, 'slot': 'mano_der'},
    'Bate de béisbol':{'tipo': 'arma',   'dmg': 20, 'slot': 'mano_der'},
    'Lanza artesanal':{'tipo': 'arma',   'dmg': 22, 'slot': 'mano_der'},
    'Exoesqueleto':   {'tipo': 'equipo', 'defensa': 15, 'evasion': 0.25, 'slot': 'torso'},
    'Chaleco':        {'tipo': 'equipo', 'defensa': 10, 'evasion': 0.05, 'slot': 'torso'},
    'Armadura Placas':{'tipo': 'equipo', 'defensa': 20, 'evasion': 0.0,  'slot': 'torso'},
    'Casco Militar':  {'tipo': 'equipo', 'defensa': 8,  'evasion': 0.02, 'slot': 'cabeza'},
    'Gafas Tácticas': {'tipo': 'equipo', 'defensa': 2,  'evasion': 0.10, 'slot': 'cabeza'},
    'Botas Tácticas': {'tipo': 'equipo', 'defensa': 4,  'evasion': 0.08, 'slot': 'pies'},
    'Rodilleras':     {'tipo': 'equipo', 'defensa': 3,  'evasion': 0.05, 'slot': 'pies'},
    'Mochila Grande': {'tipo': 'util',   'efecto': 'inventario+3', 'slot': 'espalda'},
    'Mochila Táctica':{'tipo': 'util',   'efecto': 'inventario+5', 'slot': 'espalda'},
}

ITEMS_CURATIVOS = {
    'Botiquín':         {'hp': 50,  'hambre': 0},
    'Venda':            {'hp': 20,  'hambre': 0},
    'Lata de comida':   {'hp': 5,   'hambre': 20},
    'Ración Energética':{'hp': 10,  'hambre': 35},
    'Agua Purificada':  {'hp': 15,  'hambre': 15},
    'Antibióticos':     {'hp': 30,  'hambre': 0,  'cura_estado': 'infectado'},
    'Yoduro de potasio':{'hp': 0,   'hambre': 0,  'cura_estado': 'irradiado'},
    'Morfina':          {'hp': 60,  'hambre': 0},
    'Azada':            {'hp': 0,   'hambre': 0},
    'Vendas':           {'hp': 15,  'hambre': 0},
    'Mapa':             {'hp': 0,   'hambre': 0},
}

# Recetas de crafteo al estilo Dying Light
# ingredientes: lista de (nombre_item, cantidad)
RECETAS_CRAFTEO = {
    'Cóctel Molotov': {
        'ingredientes': [('Gasolina', 1), ('Trapo', 1), ('Botella vacía', 1)],
        'resultado': {'tipo': 'arma_arrojadiza', 'dmg': 80},
        'desc': 'Bomba incendiaria artesanal. Daño masivo en área.',
        'xp_craft': 15,
    },
    'Venda': {
        'ingredientes': [('Trapo', 2), ('Alcohol', 1)],
        'resultado': {'tipo': 'curativo', 'hp': 20},
        'desc': 'Cura básica de trauma.',
        'xp_craft': 5,
    },
    'Botiquín Mejorado': {
        'ingredientes': [('Botiquín', 1), ('Antibióticos', 1), ('Morfina', 1)],
        'resultado': {'tipo': 'curativo', 'hp': 100},
        'desc': 'Cura completa. Elimina estados negativos.',
        'xp_craft': 25,
    },
    'Lanza artesanal': {
        'ingredientes': [('Palo', 2), ('Cuchillo', 1), ('Cuerda', 1)],
        'resultado': {'tipo': 'arma', 'dmg': 22, 'slot': 'mano_der'},
        'desc': 'Arma cuerpo a cuerpo de largo alcance.',
        'xp_craft': 20,
    },
    'Machete': {
        'ingredientes': [('Chatarra metálica', 2), ('Cuerda', 1)],
        'resultado': {'tipo': 'arma', 'dmg': 28, 'slot': 'mano_der'},
        'desc': 'Hoja improvisada. Corta bien, dura poco.',
        'xp_craft': 18,
    },
    'Trampa Explosiva': {
        'ingredientes': [('Pólvora', 2), ('Cable', 1), ('Lata vacía', 1)],
        'resultado': {'tipo': 'trampa', 'dmg': 120},
        'desc': 'Trampa en el suelo. Daño masivo al primer zombi.',
        'xp_craft': 30,
    },
    'Chaleco': {
        'ingredientes': [('Chatarra metálica', 3), ('Cuerda', 2)],
        'resultado': {'tipo': 'equipo', 'defensa': 10, 'evasion': 0.05, 'slot': 'torso'},
        'desc': 'Protección torácica básica.',
        'xp_craft': 22,
    },
    'Ración Energética': {
        'ingredientes': [('Lata de comida', 1), ('Azúcar', 1)],
        'resultado': {'tipo': 'curativo', 'hp': 10, 'hambre': 35},
        'desc': 'Comida reforzada. Sacia hambre y cura algo.',
        'xp_craft': 8,
    },
    'Agua Purificada': {
        'ingredientes': [('Agua sucia', 2), ('Pastilla potabilizadora', 1)],
        'resultado': {'tipo': 'curativo', 'hp': 15, 'hambre': 15},
        'desc': 'Agua segura para beber.',
        'xp_craft': 6,
    },
    'Rifle Modificado': {
        'ingredientes': [('Rifle', 1), ('Chatarra metálica', 1), ('Cuerda', 1)],
        'resultado': {'tipo': 'arma', 'dmg': 70, 'slot': 'mano_der'},
        'desc': 'Rifle con mejoras de campo. Más preciso.',
        'xp_craft': 35,
    },
}

# Materiales crafteo (no equipables, solo para crafting)
MATERIALES = {
    'Trapo', 'Gasolina', 'Botella vacía', 'Alcohol', 'Palo', 'Cuerda',
    'Chatarra metálica', 'Pólvora', 'Cable', 'Lata vacía', 'Azúcar',
    'Agua sucia', 'Pastilla potabilizadora', 'Lata vacía'
}

# Loot posible al saquear edificios
LOOT_EDIFICIO = [
    ('Trapo', 40), ('Gasolina', 20), ('Botella vacía', 30), ('Alcohol', 25),
    ('Palo', 35), ('Cuerda', 30), ('Chatarra metálica', 25), ('Pólvora', 15),
    ('Cable', 20), ('Lata vacía', 25), ('Azúcar', 20), ('Agua sucia', 30),
    ('Pastilla potabilizadora', 15), ('Lata de comida', 30), ('Venda', 20),
    ('Cuchillo', 10), ('Rifle', 5), ('Antibióticos', 12), ('Morfina', 8),
    ('Yoduro de potasio', 8),
]

# Árbol de habilidades expandido (estilo Project Zomboid)
HABILIDADES = {
    # --- COMBATE ---
    'fuerza':          {'nombre': 'Músculo',          'desc': '+5 Daño base permanente.',          'coste': 1, 'cat': 'combate',      'req': None},
    'fuerza2':         {'nombre': 'Bruto',             'desc': '+8 Daño adicional permanente.',     'coste': 2, 'cat': 'combate',      'req': 'fuerza'},
    'armas_fuego':     {'nombre': 'Tirador',           'desc': '+15 Daño con armas de fuego.',      'coste': 2, 'cat': 'combate',      'req': 'fuerza'},
    'esquivar':        {'nombre': 'Evasor',            'desc': '15% de evadir ataques.',            'coste': 1, 'cat': 'combate',      'req': None},
    'esquivar2':       {'nombre': 'Fantasma',          'desc': '25% de evadir ataques.',            'coste': 2, 'cat': 'combate',      'req': 'esquivar'},
    'golpe_critico':   {'nombre': 'Ojo Clínico',       'desc': '20% de infligir daño doble.',       'coste': 2, 'cat': 'combate',      'req': 'fuerza'},
    'sigilo':          {'nombre': 'Sombra',            'desc': 'Los zombis no te detectan a dist>3.','coste': 2, 'cat': 'combate',     'req': 'esquivar'},

    # --- SUPERVIVENCIA ---
    'supervivencia':   {'nombre': 'Metabolismo',       'desc': 'El hambre baja más despacio.',      'coste': 1, 'cat': 'supervivencia','req': None},
    'supervivencia2':  {'nombre': 'Ayuno Extremo',     'desc': 'El hambre baja aún más despacio.',  'coste': 2, 'cat': 'supervivencia','req': 'supervivencia'},
    'resistencia':     {'nombre': 'Piel Dura',         'desc': '+20 HP máximo permanente.',         'coste': 1, 'cat': 'supervivencia','req': None},
    'resistencia2':    {'nombre': 'Coraza',            'desc': '+30 HP máximo adicional.',          'coste': 2, 'cat': 'supervivencia','req': 'resistencia'},
    'medicina':        {'nombre': 'Paramédico',        'desc': 'Los items curativos curan +30%.',   'coste': 2, 'cat': 'supervivencia','req': 'resistencia'},
    'inmunidad':       {'nombre': 'Sistema Inmune',    'desc': '50% resistencia a infecciones.',    'coste': 2, 'cat': 'supervivencia','req': 'medicina'},

    # --- RECURSOS ---
    'carroñero':       {'nombre': 'Carroñero',         'desc': 'Encuentras más dinero al matar.',   'coste': 1, 'cat': 'recursos',     'req': None},
    'carroñero2':      {'nombre': 'Buitre',            'desc': '+50% loot en edificios.',           'coste': 2, 'cat': 'recursos',     'req': 'carroñero'},
    'mochila_ext':     {'nombre': 'Mochilero',         'desc': '+2 slots de inventario.',           'coste': 1, 'cat': 'recursos',     'req': None},
    'mochila_ext2':    {'nombre': 'Cargador',          'desc': '+3 slots de inventario adicionales.','coste': 2, 'cat': 'recursos',    'req': 'mochila_ext'},
    'mochila_ext3':    {'nombre': 'Camionero',         'desc': '+5 slots de inventario totales.',   'coste': 3, 'cat': 'recursos',     'req': 'mochila_ext2'},
    'crafteo':         {'nombre': 'Manitas',           'desc': 'Desbloquea recetas avanzadas.',     'coste': 2, 'cat': 'recursos',     'req': None},
    'crafteo2':        {'nombre': 'Ingeniero',         'desc': 'Crafteas con 1 ingrediente menos.', 'coste': 3, 'cat': 'recursos',     'req': 'crafteo'},

    # --- EXPLORACIÓN ---
    'agricultura':     {'nombre': 'Botánico',          'desc': 'Permite plantar en el sector.',     'coste': 1, 'cat': 'exploracion',  'req': None},
    'agricultura2':    {'nombre': 'Granjero',          'desc': 'Las cosechas dan el doble.',        'coste': 2, 'cat': 'exploracion',  'req': 'agricultura'},
    'navegacion':      {'nombre': 'Orientación',       'desc': 'Ve los edificios en un radio +5.',  'coste': 1, 'cat': 'exploracion',  'req': None},
    'cartografo':      {'nombre': 'Cartógrafo',        'desc': 'El mapa revela zonas seguras.',     'coste': 2, 'cat': 'exploracion',  'req': 'navegacion'},
    'velocidad':       {'nombre': 'Corredor',          'desc': 'Puedes huir siempre del combate.',  'coste': 2, 'cat': 'exploracion',  'req': None},
}