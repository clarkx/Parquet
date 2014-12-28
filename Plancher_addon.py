# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

# Some of the code is from Michel Anders's script "Floor Generator"
# I couldn't figure by myself how to update the mesh :( Thanks to him !
 
bl_info = {
    "name": "Plancher",
    "author": "Cédric Brandin",
    "version": (0, 0, 15),
    "blender": (2, 72, 0),
	  "location": "",
    "description": "Create a floor board",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}


import math 
import bpy
import bmesh
from bpy.props import IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty
from mathutils import Vector, Euler, Matrix
from random import random as rand, seed, uniform as randuni, randint, expovariate

#############################################################
# COMPUTE THE LENGTH OF THE BOARD
#############################################################
# Calcul pour conserver la largeur de la lame si offsetx.
def calculangle(gauche, fin, offsetx, debut, largeur, longueurlame):

    oppose = largeur * math.tan(offsetx)
    hyp = math.sqrt(largeur ** 2 + oppose ** 2)
    decalx = longueurlame * math.sin(offsetx)   
    decaly = math.sqrt((longueurlame ** 2) - (decalx ** 2))
    
    return (hyp, decalx, decaly)

#############################################################
# BOARD 
#############################################################
# Création des lames basées sur la première.
def lame(debut, gauche, droite, fin, offsetx, decalx, hyp, batonrompu, espacey):
    
    espacex = 0
    if not batonrompu: espacey = 0
    
    if offsetx > 0:
        decalbas = decalx
        decalhaut = 0
        if batonrompu:
            espacey = espacey / 2
            espacex = 0
            
    else:
        decalbas = 0
        decalhaut = -decalx
        if batonrompu:
            espacey = espacey / 2
            espacex = espacey * 2

        
    # bas gauche [0,0,0]
    bg = Vector((gauche + decalbas + espacex, debut - espacey, 0))
    # bas droite [1,0,0]
    bd = Vector((droite + decalbas + espacex, debut - espacey, 0))
    # haut droite [1,1,0]
    hd = Vector((droite - decalhaut + espacex, fin - espacey, 0))
    # haut gauche [0,1,0]
    hg = Vector((gauche - decalhaut + espacex, fin - espacey, 0))

    if batonrompu:
        if offsetx > 0:
            hd[0] = hd[0] - (hyp / 2) 
            hd[1] = hd[1] + (hyp / 2) 
            bd[0] = bd[0] - (hyp / 2)
            bd[1] = bd[1] + (hyp / 2)
        else:
            bg[0] = bg[0] + (hyp / 2)
            bg[1] = bg[1] + (hyp / 2) 
            hg[0] = hg[0] + (hyp / 2) 
            hg[1] = hg[1] + (hyp / 2) 

    verts = (bg, hg, hd, bd)
   
    return (verts)

#############################################################
# TRANSVERSAL
#############################################################
# Création des transversales.
def transversal(gauche, droite, debut, offsetx, decalx, espacey, esptrans, fin, nbrtrans, verts, faces, locktrans, longtrans):
    
    if esptrans > espacey/(nbrtrans+1): esptrans = espacey/(nbrtrans+1)   #L'espace ne peut pas excéder la largeur de la transversale
    x = 0
    longint = 0
    bool_decal = True
    if offsetx > 0: decalx = 0
    lrg = ((fin - debut)-(esptrans*(nbrtrans+1))) * (1 / nbrtrans)  #Largeur de la lame / nbr de transversales
    debint = debut + esptrans
    while droite > longint:
        if locktrans: 
            longint += longtrans

        if not locktrans or (longint > droite): longint = droite

        while x < nbrtrans: # Nombre de planches dans l'interval
            x += 1
            # Incrémentation fin de chaque planche
            fintrans = debint + lrg

            # Récupération du nombre total de points
            nbvert = len(verts)

            # Création de la planche dans l'interval
            verts.extend(interval(gauche, longint, debint, decalx, espacey, fintrans))

            # Création des faces à partir des points
            faces.append((nbvert, nbvert+1, nbvert+2, nbvert+3))
            debint = fintrans + esptrans
        #------------------------------------------------------------------------------------
        # Initialisation
        if locktrans:
            gauche = longint + esptrans
            longint += esptrans
            x = 0
            fintrans = debut + lrg
            debint = debut + esptrans
        # Test si on depasse la longueur du parquet, on sort de la boucle.
        if gauche > droite:
            longint = gauche


#############################################################
# INTERVAL
#############################################################
# Création d'une nouvelle lame dans l'intervalle Y.
def interval(gauche, droite, debut, offsetx, espacey, fin):

    # bas droite
    bd = Vector((droite + offsetx, debut, 0))
    # bas gauche
    bg = Vector((gauche + offsetx, debut, 0))
    # haut gauche
    hg = Vector((gauche + offsetx, fin, 0))
    # haut droite
    hd = Vector((droite + offsetx, fin, 0))
    
    verts = (bg, hg, hd, bd)
    
    return verts

#############################################################
# FLOOR BOARD
#############################################################
# Création d'une rangée de parquet
def parquet(switch, nbrlame, largeur, randlargoffset, espacex, longueurlame, espacey, offsety, nbrdecal, offsetx, batonrompu, randoffsety, longueurparquet, hauteur, trans, esptrans, longtrans, locktrans, nbrtrans):

    #------------------------------------------------------------
    # Initialisation des zones
    #------------------------------------------------------------
    x = 0
    y = 0
    verts = []
    faces = []
    listinter = []
    debut = 0
    gauche = 0
    bool_decaly = True #offsety = 0  
    fin = longueurlame 
    intergauche = 0
    interdroite = 0
    if offsety: locktrans = False
    if batonrompu : switch = True
    if randoffsety > 0:
        randecaley = offsety * (1-randoffsety)
    else:
        randecaley = offsety
        
    if offsety > 0: 
        offsetx = 0
        batonrompu = False

    if espacey == 0: #Si il n'y pas d'écart entre les lames, désactivation de la planche transversale.
        trans = False

    if batonrompu:
        offsety = 0
        offsetx = math.radians(45)
        randlargoffset = 0
        trans = False
    #------------------------------------------------------------
    hyp, decalx, decaly = calculangle(gauche, fin, offsetx, debut, largeur, fin)
    randespace = hyp + (randlargoffset * randuni(0, hyp)) # Ajout de hasard dans la largeur des rangées
    droite = randespace # Droite = largeur    
    fin = decaly - (decaly * randuni(randecaley, offsety))

    if batonrompu or switch: # Force la longueur du parquet au nombre de planches
        longueurparquet = round(longueurparquet / decaly) * decaly + (round(longueurparquet / decaly)-1) * espacey
        
    #------------------------------------------------------------
    # Boucle de création des lames sur X
    #------------------------------------------------------------
    while x < nbrlame:
        x += 1   

        if (x % nbrdecal != 0): bool_decaly = not bool_decaly # Décalage de plusieurs rangées

        # Si la dernière planche dépasse, on la coupe !
        if fin > longueurparquet :
            fin = longueurparquet
            fin2 = fin

        # Récupération du nombre total de points
        nbvert = len(verts)
            
        # Création premier objet de chaque rangée 
        verts.extend(lame(debut, gauche, droite, fin, offsetx, decalx, hyp, batonrompu, espacey))

        # Création des faces à partir des points
        faces.append((nbvert,nbvert+1, nbvert+2, nbvert+3))
        
        # Début d'une nouvelle rangée (Y)
        debut2 = fin + espacey
        fin2 = debut2 
        #------------------------------------------------------------
        # TRANSVERSALE
        #------------------------------------------------------------
        listinter.append(gauche)
        if trans and ((x % nbrdecal == 0) or ((x % nbrdecal != 0) and (x == nbrlame))) and (fin < longueurparquet) and not locktrans:
            if debut2 > longueurparquet: debut2 = longueurparquet
            transversal(listinter[0], droite, fin, offsetx, decalx, espacey, esptrans, debut2, nbrtrans, verts, faces, locktrans, longtrans)
        elif trans and (x == nbrlame) and locktrans:
            if debut2 > longueurparquet: debut2 = longueurparquet
            transversal(listinter[0], droite, fin, offsetx, decalx, espacey, esptrans, debut2, nbrtrans, verts, faces, locktrans, longtrans)

        #------------------------------------------------------------
        # Boucle de création des lames sur Y
        #------------------------------------------------------------
        while longueurparquet > fin2 :

            # Début d'une nouvelle rangée
            fin2 = debut2 + decaly

            # Si la dernière planche dépasse, on la coupe !
            if fin2 > longueurparquet :
                fin2 = longueurparquet

            # Récupération du nombre total de points
            nbvert = len(verts)

            # Invertion de l'offset pour décalage X
            if offsetx < 0:
                offsetx = offsetx * (-1)
            else:
                offsetx = -offsetx

            # Création des objets 
            verts.extend(lame(debut2, gauche, droite, fin2, offsetx, decalx, hyp, batonrompu, espacey))

            # Création des faces à partir des points
            faces.append((nbvert,nbvert+1, nbvert+2, nbvert+3))

            # Début d'une nouvelle rangée 
            debut2 += decaly + espacey
            
            #------------------------------------------------------------
            # TRANSVERSALE
            #------------------------------------------------------------
            if trans and ((x % nbrdecal == 0) or ((x % nbrdecal != 0) and (x == nbrlame))) and (fin2 < longueurparquet) and not locktrans:
                if debut2 > longueurparquet: debut2 = longueurparquet
                transversal(listinter[0], droite, fin2, offsetx, decalx, espacey, esptrans, debut2, nbrtrans, verts, faces, locktrans, longtrans)

            elif trans and locktrans and (x == nbrlame) and (fin2 < longueurparquet) :
                if debut2 > longueurparquet: debut2 = longueurparquet
                transversal(listinter[0], droite, fin2, offsetx, decalx, espacey, esptrans, debut2, nbrtrans, verts, faces, locktrans, longtrans)

            # Test si on depasse la longueur du parquet, on sort de la boucle.
            fin2 = debut2
        # Incrémentation
        if not batonrompu:
            gauche += espacex
            droite += espacex
        else:
            droite += espacey * 2
            gauche += espacey * 2
        gauche += randespace
        if (x % nbrdecal == 0) and not locktrans: listinter = []
        randespace = hyp + (randlargoffset * randuni(0, hyp))
        droite += randespace            
        #------------------------------------------------------------
        # Décalage des rangées sur Y
        #------------------------------------------------------------

        if (bool_decaly and offsety > 0):
            if (x % nbrdecal == 0 ):
                fin = decaly * randuni(randecaley, offsety)
            bool_decaly = False  
        else:
            if (x % nbrdecal == 0 ):
                fin = decaly - (decaly * randuni(randecaley, offsety))
            bool_decaly = True


        #------------------------------------------------------------#

        #------------------------------------------------------------
        # Décalage sur X (parquet Hongrie) : Initialisation de l'offsetx
        #------------------------------------------------------------                
        if offsetx < 0:
           offsetx = offsetx * (-1)   
        #------------------------------------------------------------#

    #------------------------------------------------------------ FIN BOUCLE X         
    return verts, faces

#############################################################
# PANEL PRINCIPAL
#############################################################
class PlancherPanel(bpy.types.Panel):
    bl_idname = "mesh.plancher"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Plancher"
    bl_label = "Plancher"

    #------------------------------------------------------------
    # PANEL 
    #------------------------------------------------------------
    def draw(self, context):
        layout = self.layout
        myObj = bpy.context.active_object
        col = layout.column()
        cobj = context.object
        if not myObj or myObj.name != 'Plancher' :
            layout.operator('mesh.ajout_primitive') 
        
        if bpy.context.mode == 'EDIT_MESH':
            col = layout.column()
            col = layout.column()      
            col.label(text="Vertex / UV")    
            col = layout.column(align=True)
            #Vertex Color
            if cobj.colphase == 0:
                row = col.row(align=True)
                row.prop(cobj, "uvcol")
            #Phase Color
            if cobj.uvcol == 0:
                row = col.row(align=True) 
                row.prop(cobj, "colphase")
            #Seed color
            row = col.row(align=True) 
            row.prop(cobj, "colseed")            
            #layout.label('Plancher only works in Object Mode.')
        elif myObj and myObj.name == 'Plancher'  :
            #------------------------------------------------------------PLANCHER
            col.label(text="Surface")
            
            col = layout.column(align=True)
            row = col.row(align=True)
            row.prop(cobj, "switch", icon='BLANK1')
            row = col.row(align=True)
            row.prop(cobj, "nbrlame")
            row.prop(cobj, "longueurparquet")
            row = col.row(align=True)         
            row.prop(cobj, "hauteur")   

            col = layout.column()
            col = layout.column()      

            #------------------------------------------------------------SOL
            col.label(text="Board")
            col = layout.column(align=True)
            row = col.row(align=True)
            
            row.prop(cobj, "longueurlame")
            row.prop(cobj, "largeur")
            row = col.row(align = True)
            row.prop(cobj, "randlargoffset", text="Random", slider=True)
            row = col.row(align=True) 
            row.prop(cobj, "colseed")
            
            col = layout.column()
            col = layout.column()   
            
            #------------------------------------------------------------ESPACEMENT        
            col.label(text="Gap")
            col = layout.column(align=True)
            row = col.row(align=True)

            if cobj.batonrompu == False:
                row.prop(cobj, "espacex")
            row.prop(cobj, "espacey")
            if cobj.espacey > 0:

            #------------------------------------------------------------TRANSVERSAL     
                col = layout.column(align=True)
                row = col.row(align=True)
                row.label(text="Transversal:")
                row.prop(cobj, "trans")
                if cobj.trans:
                    row.prop(cobj, "locktrans")
                    col = layout.column(align=True)
                    row = col.row(align=True)
                    if cobj.locktrans: row.prop(cobj, "longtrans")
                    if not cobj.locktrans: row.prop(cobj, "nbrdecal")
                    row.prop(cobj, "nbrtrans")
                    row = col.row(align=True)
                    row.prop(cobj, "esptrans")
                else: 
                    row = col.row(align=True)
                    row.prop(cobj, "nbrdecal")
                row = col.row(align=True)
                row.prop(cobj, "offsety")
                row.prop(cobj, "randoffsety")
                row = col.row(align=True) 
                row.prop(cobj, "colseed")            

            #------------------------------------------------------------CHEVRON / HERRINGBONE
                col = layout.column()
                col = layout.column()      
                col.label(text="Chevron")    
                col = layout.column(align=True)
                                
            if cobj.offsety == 0 and cobj.batonrompu == False:
                row = col.row(align=True)
                #Parquet Hongrie
                row.prop(cobj, "offsetx")             
            
            if cobj.batonrompu == True:
                self.switch = True                            
            #Parquet Herringbone
            row = col.row(align=True) 
            row.prop(cobj, "batonrompu", text='Herringbone', icon='BLANK1')
            
            #------------------------------------------------------------UV / VERTEX
            col = layout.column()
            col = layout.column() 
            col = layout.column(align=True)     
            col.label(text="Go in edit mode for UV !")    
            col.label(text="Warning ! Any change here will reset the uv/color !")    

#############################################################
# FUNCTION PLANCHER
#############################################################
def create_plancher(self,context):
    bpy.context.user_preferences.edit.use_global_undo = False
    obj_mode = bpy.context.active_object.mode
    bpy.ops.object.mode_set(mode='OBJECT')  
    bpy.context.scene.unit_settings.system = 'METRIC'
    cobj = context.object
    verts, faces = parquet(cobj.switch,
                               cobj.nbrlame,
                               cobj.largeur,
                               cobj.randlargoffset,
                               cobj.espacex,
                               cobj.longueurlame,
                               cobj.espacey,
                               cobj.offsety,
                               cobj.nbrdecal,
                               cobj.offsetx,
                               cobj.batonrompu,
                               cobj.randoffsety,
                               cobj.longueurparquet,
                               cobj.hauteur,
                               cobj.trans,
                               cobj.esptrans,
                               cobj.longtrans,
                               cobj.locktrans,
                               cobj.nbrtrans,)
    
    # Code from Michel Anders script Floor Generator
    # Create mesh & link object to scene
    emesh = cobj.data

    mesh = bpy.data.meshes.new("Plancher_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)

    for i in bpy.data.objects:
        if i.data == emesh:
            i.data = mesh
    
    name = emesh.name
    emesh.user_clear()
    bpy.data.meshes.remove(emesh)
    mesh.name = name
    # ---------------------------------------------------------------

    #----------------------------------------------------------------COLOR & UV 
    if obj_mode =='EDIT':
        seed(cobj.colseed)
        # Ajout des UV et d'une couleur pour chaque planche
        mesh.uv_textures.new("Txt_Plancher")
        vertex_colors = mesh.vertex_colors.new().data
        rgb = []

        # Générer autant de couleurs que d'uvcol
        if cobj.uvcol > 0: 
            for i in range(cobj.uvcol):
                color = [round(rand()), round(rand()), round(rand())]
                rgb.append(color)

        elif cobj.colphase > 0: 
            for n in range(cobj.colphase):
                color = [round(rand()), round(rand()), round(rand())]
                rgb.append(color)      
    #----------------------------------------------------------------VERTEX GROUP
        # Création d'un vertex group
        bpy.context.object.vertex_groups.clear()
        if cobj.uvcol == 0 and cobj.colphase == 0: 
            bpy.context.object.vertex_groups.new()
        elif cobj.uvcol > 0:        
            # Création de plusieurs vertex group
            for v in range(cobj.uvcol): 
                bpy.context.object.vertex_groups.new()
        elif cobj.colphase > 0: 
            # Création de plusieurs vertex group
            for v in range(cobj.colphase): 
                bpy.context.object.vertex_groups.new()

    #----------------------------------------------------------------VERTEX COLOR        
        phase = cobj.colphase
        color = {}
        for poly in mesh.polygons:

            if cobj.uvcol == 0 and cobj.colphase == 0: 
                color = [rand(), rand(), rand()]

            elif cobj.uvcol > 0: 
                color = rgb[randint(0,cobj.uvcol-1)]
                
                for loop_index in poly.loop_indices:
                    vertex_colors[loop_index].color = color
                    vg = bpy.context.object.vertex_groups[rgb.index(color)]

                    # Assigne chaque vertex/couleur a un vertex group
                    vg.add([loop_index], 1, "ADD") # index, weight, operation

            elif cobj.colphase > 0: 
                color = rgb[phase-1]
                phase -= 1
                if phase == 0: phase = cobj.colphase
                
                for loop_index in poly.loop_indices:
                    vertex_colors[loop_index].color = color
                    vg = bpy.context.object.vertex_groups[rgb.index(color)]

                    # Assigne chaque vertex/couleur a un vertex group
                    vg.add([loop_index], 1, "ADD") 
        color.clear() 

        # UV Unwrap
        ob = bpy.context.object
        ob.select = True
        bpy.ops.object.mode_set(mode='EDIT') 
        bpy.ops.uv.unwrap(method='ANGLE_BASED', correct_aspect=True)
        
        # UV Layer
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        uv_lay = bm.loops.layers.uv.verify()
        
        # Group the UV at the origin point
        v = 0
        tpuvx = {}
        tpuvy = {}
        for face in bm.faces:
            for loop in face.loops:
                luv = loop[uv_lay]
                v += 1
                uv = loop[uv_lay].uv
                tpuvx[uv.x] = loop.index
                tpuvy[uv.y] = loop.index
 
                if v > 3:
                    minx = min(tpuvx.keys())
                    miny = min(tpuvy.keys())
                    idxminx = tpuvx[minx]
                    idxminy = tpuvy[miny]

                    for loop in face.loops:
                        loop[uv_lay].uv[0] -= minx
                        loop[uv_lay].uv[1] -= miny
            tpuvx.clear() 
            tpuvy.clear()
            
        bmesh.update_edit_mesh(me)
    else:
        bpy.ops.object.mode_set(mode='OBJECT')       
        #-----------    
    
    # Ajout du modifier SOLIDIFY
    nbop = len(cobj.modifiers)
    obj = context.active_object
    if nbop == 0:
        obj.modifiers.new('Solidify', 'SOLIDIFY')
        obj.modifiers.new('Bevel', 'BEVEL')
    cobj.modifiers['Solidify'].show_expanded = False
    cobj.modifiers['Solidify'].thickness = self.hauteur
    cobj.modifiers['Bevel'].show_expanded = False
    cobj.modifiers['Bevel'].width = 0.001
    bpy.context.user_preferences.edit.use_global_undo = True

#############################################################
# PROPERTIES
#############################################################

    # Switch entre unités et mesures 
bpy.types.Object.switch = BoolProperty(
               name="Switch",
               description="Switch between length of plank and meters",
               default=False,            
               update=create_plancher)  

    # Longueur du plancher 
bpy.types.Object.longueurparquet = FloatProperty(
               name="Length",
               description="Length of the floor",
               min=0.01, max=100.0,
               default=4.0,
               precision=2,
               subtype='DISTANCE',
               unit='LENGTH',
               step=0.001,
               update=create_plancher)

    # Nombre de lame
bpy.types.Object.nbrlame = IntProperty(
            name="Count",
            description="Number of row",
            min=1, max=100,
            default=2,
            update=create_plancher)
              
    # Longueur d'une planche
bpy.types.Object.longueurlame = FloatProperty(
               name="Length",
               description="Length of a board",
               min=0.01, max=100.0,
               default=2.0,
               precision=2,
               subtype='DISTANCE',
               unit='LENGTH',
               step=0.001,
               update=create_plancher)
               
    # Largeur d'une planche
bpy.types.Object.largeur = FloatProperty(
              name="Width",
              description="Width of a board",
              min=0.01, max=100.0,
              default=0.18,
              precision=3,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.1,
              update=create_plancher)

    # Offset Random largeur         
bpy.types.Object.randlargoffset = FloatProperty(
               name="Random",
               description="Add random to the width",
               min=0, max=1,
               default=0,
               precision=2,
               subtype='PERCENTAGE',
               unit='NONE',
               step=0.1,
               update=create_plancher)

    # Interval entre les rangées sur les X
bpy.types.Object.espacex = FloatProperty(
              name="Gap X",
              description="Add a gap between the columns (X)",  
              min=0.00, max=100.0,
              default=0.01,
              precision=2,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.001,
              update=create_plancher)
              
    # Interval entre les rangées sur les Y
bpy.types.Object.espacey = FloatProperty(
              name="Gap Y",
              description="Add a gap between the row (Y)",
              min=0.00, max=100.0,
              default=0.01,
              precision=2,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.001,              
              update=create_plancher)

    # Remplir l'interval sur X
bpy.types.Object.trans = BoolProperty(
               name=" ",
               description="Fill in the gap between the row",
               default=False,           
               update=create_plancher) 

    # Utilise les paramètre d'espacement
bpy.types.Object.locktrans = BoolProperty(
               name="Unlock",
               description="Unlock the length of the transversal",
               default=False,           
               update=create_plancher)
               
    # Longueur de la planche transversale
bpy.types.Object.longtrans = FloatProperty(
              name="Length",
              description="Length of the transversal",
              min=0.01, max=100,
              default=2,
              precision=2,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.1,
              update=create_plancher)

    # Espace entre les planches transversales
bpy.types.Object.esptrans = FloatProperty(
              name="Gap",
              description="Gap between the interval",
              min=0.00, max=100,
              default=0.01,
              precision=2,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.001,
              update=create_plancher)

    # Nombre de lames transversales
bpy.types.Object.nbrtrans = IntProperty(
            name="Count X",
            description="Number of board in the interval",
            min=1, max=100,
            default=1,
            update=create_plancher)
           
    # Décalage des rangées
bpy.types.Object.offsety = FloatProperty(
               name="Shift",
               description="Shift the columns",
               min=0, max=1,
               default=0,
               precision=2,
               subtype='PERCENTAGE',
               unit='NONE',
               step=0.1,
               update=create_plancher)

    # Random décalage             
bpy.types.Object.randoffsety = FloatProperty(
               name="Random",
               description="Add random to the shift",
               min=0, max=1,
               default=0,
               precision=2,
               subtype='PERCENTAGE',
               unit='NONE',
               step=0.1,
               update=create_plancher)
               
    # Nombre de lames décalées
bpy.types.Object.nbrdecal = IntProperty(
            name="Nbr Shift",
            description="Number of column to shift",
            min=1, max=100,
            default=1,
            update=create_plancher)
            
    # Décalage des planches
bpy.types.Object.offsetx = FloatProperty(
               name="Tilt",
               description="Tilt the columns",
               min= math.radians(0), max= math.radians(70),
               default=0.00,
               precision=2,
               subtype='ANGLE',
               unit='ROTATION',
               step=1,
               update=create_plancher)

    # Hauteur           
bpy.types.Object.hauteur = FloatProperty(
              name="Height",
              description="Height of the floor",
              min=0.01, max=100,
              default=0.01,
              precision=2,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.1,
              update=create_plancher)

    # Parquet Herringbone
bpy.types.Object.batonrompu = BoolProperty(
               name="Herringbone",
               description="Floor type Herringbone",
               default=False,            
               update=create_plancher)

    # Nombre de vertex color
bpy.types.Object.uvcol = IntProperty(
               name="Random Color",
               description="Random color to the vertex group",
               min=0, max=100,
               default=0,
               update=create_plancher)

    # Nombre de vertex color
bpy.types.Object.colphase = IntProperty(
               name="Phase color",
               description="Orderly color to the vertex group",
               min=0, max=100,
               default=0,
               update=create_plancher)

    # Nombre de vertex color
bpy.types.Object.colseed = IntProperty(
               name="Seed",
               description="New distribution for the random",
               min=0, max=999999,
               default=0,
               update=create_plancher) 

                              
class AjoutPrimitive(bpy.types.Operator):
	bl_idname = "mesh.ajout_primitive"
	bl_label = "Add a new floor"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		bpy.ops.mesh.primitive_cube_add()
		context.active_object.name = "Plancher"
		cobj = context.object
		cobj.nbrlame = 2
		return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)
    
def unregister():
    bpy.utils.unregister_module(__name__)
            
if __name__ == "__main__":
    register()

