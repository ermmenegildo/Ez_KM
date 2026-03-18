# -*- coding: utf-8 -*-

CLASES = {
    'Policia':        {'hp':110,'item':'Pistola 9mm',   'bono':'Acceso a furgones policiales.'},
    'Medico':         {'hp':100,'item':'Botiquin',       'bono':'+30% efectividad curativos.'},
    'Militar':        {'hp':130,'item':'Cuchillo',       'bono':'Empieza con municion extra.'},
    'Lenador':        {'hp':140,'item':'Hacha',          'bono':'Armas cuerpo a cuerpo duran +50%.'},
    'Vagabundo':      {'hp': 90,'item':'Lata de comida', 'bono':'Encuentra objetos ocultos.'},
    'Artista Marcial':{'hp':120,'item':'Vendas',         'bono':'Punos infligen 15 de dano.'},
    'Catedratico':    {'hp': 80,'item':'Mapa',           'bono':'+15% XP en todas las acciones.'},
    'Agricultor':     {'hp':115,'item':'Azada',          'bono':'Cosechas rinden el doble.'},
}

CARGADOR = {
    'Pistola 9mm':12,'Ebony & Ivory':24,'Rifle':8,'Winchester 1866':6,
    'Rifle Modificado':10,'Escopeta':6,'Ballesta':1,
}

TIPOS_MUNICION = {
    'Balas 9mm':   {'armas':['Pistola 9mm','Ebony & Ivory'],'paquete':12},
    'Balas Rifle': {'armas':['Rifle','Winchester 1866','Rifle Modificado'],'paquete':8},
    'Cartuchos':   {'armas':['Escopeta'],'paquete':6},
    'Flechas':     {'armas':['Ballesta'],'paquete':10},
}

OBJETOS = {
    'Pistola 9mm':      {'tipo':'arma','dmg':40,'slot':'mano_der','ammo_type':'Balas 9mm',  'dur':None,'special':None},
    'Rifle':            {'tipo':'arma','dmg':55,'slot':'mano_der','ammo_type':'Balas Rifle', 'dur':None,'special':None},
    'Escopeta':         {'tipo':'arma','dmg':70,'slot':'mano_der','ammo_type':'Cartuchos',  'dur':None,'special':None},
    'Ballesta':         {'tipo':'arma','dmg':45,'slot':'mano_der','ammo_type':'Flechas',    'dur':None,'special':None},
    'Hacha':            {'tipo':'arma','dmg':25,'slot':'mano_der','ammo_type':None,'dur':40,'special':None},
    'Cuchillo':         {'tipo':'arma','dmg':15,'slot':'mano_der','ammo_type':None,'dur':30,'special':None},
    'Cuchillo de cocina':{'tipo':'arma','dmg':12,'slot':'mano_der','ammo_type':None,'dur':20,'special':None},
    'Katana':           {'tipo':'arma','dmg':35,'slot':'mano_der','ammo_type':None,'dur':50,'special':'sangrado'},
    'Machete':          {'tipo':'arma','dmg':28,'slot':'mano_der','ammo_type':None,'dur':35,'special':None},
    'Bate de beisbol':  {'tipo':'arma','dmg':20,'slot':'mano_der','ammo_type':None,'dur':25,'special':None},
    'Lanza artesanal':  {'tipo':'arma','dmg':22,'slot':'mano_der','ammo_type':None,'dur':15,'special':None},
    'Tuberia':          {'tipo':'arma','dmg':18,'slot':'mano_der','ammo_type':None,'dur':30,'special':None},
    'Azada':            {'tipo':'arma','dmg':16,'slot':'mano_der','ammo_type':None,'dur':20,'special':None},
    'Achuela':          {'tipo':'arma','dmg':22,'slot':'mano_der','ammo_type':None,'dur':35,'special':None},
    'Rifle Modificado': {'tipo':'arma','dmg':70,'slot':'mano_der','ammo_type':'Balas Rifle','dur':None,'special':None},
    'Ebony & Ivory':    {'tipo':'arma','dmg':65,'slot':'mano_der','ammo_type':'Balas 9mm','dur':None,'special':'doble_disparo','lore':'Pistolas akimbo de Dante. Oficina Distrito Financiero.','raro':True},
    'Espada Crisol':    {'tipo':'arma','dmg':80,'slot':'mano_der','ammo_type':None,'dur':None,'special':'quemado','lore':'Arma del Doom Slayer.','raro':True},
    'Espada de Blade':  {'tipo':'arma','dmg':75,'slot':'mano_der','ammo_type':None,'dur':None,'special':'vampirismo','lore':'Espada del cazavampiros.','raro':True},
    'Espada del Brujo': {'tipo':'arma','dmg':60,'slot':'mano_der','ammo_type':None,'dur':None,'special':'confusion','lore':'Tienda de la pitonisa.','raro':True},
    'Excalibur':        {'tipo':'arma','dmg':70,'slot':'mano_der','ammo_type':None,'dur':None,'special':'aturdir','lore':'Museo del Centro Urbano.','raro':True},
    'Winchester 1866':  {'tipo':'arma','dmg':52,'slot':'mano_der','ammo_type':'Balas Rifle','dur':None,'special':None,'lore':'Museo de historia.','raro':True},
    'Katana de Musashi':{'tipo':'arma','dmg':68,'slot':'mano_der','ammo_type':None,'dur':None,'special':'sangrado','lore':'Museo de arte.','raro':True},
    'Exoesqueleto':          {'tipo':'equipo','defensa':15,'evasion':0.25,'slot':'torso','dur':None},
    'Chaleco Antibalas':     {'tipo':'equipo','defensa':10,'evasion':0.05,'slot':'torso','dur':None},
    'Chaleco':               {'tipo':'equipo','defensa':10,'evasion':0.05,'slot':'torso','dur':None},
    'Armadura Placas':       {'tipo':'equipo','defensa':20,'evasion':0.00,'slot':'torso','dur':None},
    'Armadura de Estatua':   {'tipo':'equipo','defensa':25,'evasion':0.00,'slot':'torso','dur':80},
    'Armadura de Mansion':   {'tipo':'equipo','defensa':22,'evasion':0.05,'slot':'torso','dur':None},
    'Chaqueta de Motorista': {'tipo':'equipo','defensa':8, 'evasion':0.12,'slot':'torso','dur':None,'mordida_prot':0.4},
    'Armadura Improvisada':  {'tipo':'equipo','defensa':6, 'evasion':0.08,'slot':'torso','dur':20,'mordida_prot':0.6},
    'Casco Militar':         {'tipo':'equipo','defensa':8, 'evasion':0.02,'slot':'cabeza','dur':None},
    'Casco Improvisado':     {'tipo':'equipo','defensa':4, 'evasion':0.05,'slot':'cabeza','dur':15},
    'Gafas Tacticas':        {'tipo':'equipo','defensa':2, 'evasion':0.10,'slot':'cabeza','dur':None},
    'Botas Tacticas':        {'tipo':'equipo','defensa':4, 'evasion':0.08,'slot':'pies','dur':None},
    'Rodilleras':            {'tipo':'equipo','defensa':3, 'evasion':0.05,'slot':'pies','dur':None},
    'Mochila Grande':        {'tipo':'util','efecto':'inventario+3','slot':'espalda','dur':None},
    'Mochila Tactica':       {'tipo':'util','efecto':'inventario+5','slot':'espalda','dur':None},
    'Pieza de Motor':        {'tipo':'material'},
    'Combustible Marino':    {'tipo':'material'},
    'Radio':                 {'tipo':'util'},
    'Gasolina':              {'tipo':'material'},
    'Vendas':                {'tipo':'consumible'},
    'Mapa':                  {'tipo':'util'},
}

ITEMS_CURATIVOS = {
    'Botiquin':            {'hp':50, 'hambre':0},
    'Venda':               {'hp':20, 'hambre':0},
    'Vendas':              {'hp':15, 'hambre':0},
    'Lata de comida':      {'hp':5,  'hambre':20},
    'Racion Energetica':   {'hp':10, 'hambre':35},
    'Agua Purificada':     {'hp':15, 'hambre':15},
    'Antibioticos':        {'hp':30, 'hambre':0,  'cura':'bacteriana'},
    'Morfina':             {'hp':60, 'hambre':0},
    'Carbon Activado':     {'hp':10, 'hambre':0,  'cura':'intoxicacion'},
    'Vial de Retencion':   {'hp':0,  'hambre':0,  'especial':'vial'},
    'Comida Cocinada':     {'hp':25, 'hambre':50},
    'Sopa de Campamento':  {'hp':35, 'hambre':60},
    'Carne de Cadaver':    {'hp':20, 'hambre':40, 'riesgo':0.6},
    'Azada':               {'hp':0,  'hambre':0},
    'Mapa':                {'hp':0,  'hambre':0},
}

# Recipe descriptions keyed by language
RECETAS_DESC = {
    'es': {
        'Venda':'Cura basica.',
        'Coctel Molotov':'Bomba incendiaria.',
        'Armadura Improvisada':'Protege de mordidas.',
        'Lanza artesanal':'Arma improvisada.',
        'Radio':'Para la torre de radio.',
        'Casco Improvisado':'Proteccion basica.',
        'Racion Energetica':'Comida reforzada.',
        'Agua Purificada':'Agua potable.',
        'Ballesta':'Silenciosa y letal.',
        'Machete':'Hoja improvisada.',
        'Rifle Modificado':'Rifle mejorado.',
        'Botiquin Mejorado':'Cura completa.',
        'Comida Cocinada':'Comida caliente. Requiere campamento.',
    },
    'en': {
        'Venda':'Basic healing.',
        'Coctel Molotov':'Incendiary bomb.',
        'Armadura Improvisada':'Protects against bites.',
        'Lanza artesanal':'Improvised weapon.',
        'Radio':'For the radio tower.',
        'Casco Improvisado':'Basic protection.',
        'Racion Energetica':'Reinforced food.',
        'Agua Purificada':'Drinkable water.',
        'Ballesta':'Silent and lethal.',
        'Machete':'Improvised blade.',
        'Rifle Modificado':'Improved rifle.',
        'Botiquin Mejorado':'Full recovery.',
        'Comida Cocinada':'Hot food. Requires camp.',
    },
    'eu': {
        'Venda':'Oinarrizko sendaketa.',
        'Coctel Molotov':'Su-bonba.',
        'Armadura Improvisada':'Hozkaduren aurkako babesa.',
        'Lanza artesanal':'Esku-egindako arma.',
        'Radio':'Irrati dorrearako.',
        'Casco Improvisado':'Oinarrizko babesa.',
        'Racion Energetica':'Energia anoa.',
        'Agua Purificada':'Edateko ura.',
        'Ballesta':'Isilik eta hilgarria.',
        'Machete':'Esku-egindako aizto.',
        'Rifle Modificado':'Hobetutako fusila.',
        'Botiquin Mejorado':'Sendaketa osoa.',
        'Comida Cocinada':'Janari beroa. Kanpalekua behar.',
    },
}

RECETAS_BASE = {
    'Venda':             {'ingredientes':[('Trapo',2),('Alcohol',1)],'xp':5,'desc':'Cura basica.'},
    'Coctel Molotov':    {'ingredientes':[('Gasolina',1),('Trapo',1),('Botella vacia',1)],'xp':15,'desc':'Bomba incendiaria.'},
    'Armadura Improvisada':{'ingredientes':[('Trapo',3),('Cuerda',2),('Cinta americana',2)],'xp':20,'desc':'Protege de mordidas.'},
    'Lanza artesanal':   {'ingredientes':[('Palo',2),('Cuchillo',1),('Cuerda',1)],'xp':18,'desc':'Arma improvisada.'},
    'Radio':             {'ingredientes':[('Chatarra metalica',2),('Cable',3),('Pila',1)],'xp':30,'desc':'Para la torre de radio.'},
    'Casco Improvisado': {'ingredientes':[('Chatarra metalica',2),('Cuerda',1)],'xp':15,'desc':'Proteccion basica.'},
    'Racion Energetica': {'ingredientes':[('Lata de comida',1),('Azucar',1)],'xp':8,'desc':'Comida reforzada.'},
    'Agua Purificada':   {'ingredientes':[('Agua sucia',2),('Pastilla potabilizadora',1)],'xp':6,'desc':'Agua potable.'},
}

RECETAS_BIBLIOTECA = {
    'Ballesta':          {'ingredientes':[('Palo',3),('Cuerda',2),('Chatarra metalica',1)],'xp':40,'desc':'Silenciosa y letal.','plano':'Plano: Ballesta'},
    'Machete':           {'ingredientes':[('Chatarra metalica',2),('Cuerda',1)],'xp':22,'desc':'Hoja improvisada.','plano':'Plano: Machete'},
    'Rifle Modificado':  {'ingredientes':[('Rifle',1),('Chatarra metalica',1),('Cuerda',1)],'xp':45,'desc':'Rifle mejorado.','plano':'Plano: Rifle Modificado'},
    'Botiquin Mejorado': {'ingredientes':[('Botiquin',1),('Antibioticos',1),('Morfina',1)],'xp':35,'desc':'Cura completa.','plano':'Plano: Botiquin Mejorado'},
    'Comida Cocinada':   {'ingredientes':[('Lata de comida',2),('Agua sucia',1)],'xp':12,'desc':'Comida caliente. Requiere campamento.','plano':'Plano: Comida Cocinada','requiere_campamento':True},
}

PIEZAS_BARCO = 4
COMBUSTIBLE_COCHE = 5

DROPS_JEFE = ['Armadura Placas','Casco Militar','Rifle','Morfina','Morfina','Botiquin','Vial de Retencion','Escopeta']
DROPS_BANDIDO = ['Cuchillo','Pistola 9mm','Balas 9mm','Lata de comida','Venda','Chatarra metalica','Balas Rifle']