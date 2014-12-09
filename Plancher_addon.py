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

bl_info = {
    "name": "Plancher",
    "author": "Cédric Brandin",
    "version": (0, 0, 10),
    "blender": (2, 72, 0),
    "location": "",
    "description": "Ajout d'un mesh de type 'plancher'",
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
# CALCUL DE LA LARGEUR DE LA LAME
#############################################################
# Calcul pour conserver la largeur de la lame si offsetx.
def calculangle(gauche, fin, offsetx, debut, largeur, longueurlame):

    oppose = largeur * math.tan(offsetx)
    hyp = math.sqrt(largeur ** 2 + oppose ** 2)
    decalx = longueurlame * math.sin(offsetx)   
    decaly = math.sqrt((longueurlame ** 2) - (decalx ** 2))
    
    return (hyp, decalx, decaly)

#############################################################
# LAME 
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
def transversal(gauche, droite, debut, offsetx, decalx, espacey, esptrans, fin, nbrtrans, verts, faces, locktrans, longtrans, decaltrans):
    
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
    
    verts = (bg, bd, hd, hg)
    
    return verts

#############################################################
# PARQUET
#############################################################
# Création d'une rangée de parquet
def parquet(switch, nbrlame, largeur, randlargoffset, espacex, longueurlame, espacey, offsety, nbrdecal, offsetx, batonrompu, randoffsety, longueurparquet, hauteur, trans, esptrans, longtrans, locktrans, nbrtrans, decaltrans, colseed):

    #------------------------------------------------------------
    # Initialisation des zones
    #------------------------------------------------------------
    seed(colseed)
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
            transversal(listinter[0], droite, fin, offsetx, decalx, espacey, esptrans, debut2, nbrtrans, verts, faces, locktrans, longtrans, decaltrans)
        elif trans and (x == nbrlame) and locktrans:
            if debut2 > longueurparquet: debut2 = longueurparquet
            transversal(listinter[0], droite, fin, offsetx, decalx, espacey, esptrans, debut2, nbrtrans, verts, faces, locktrans, longtrans, decaltrans)

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
                transversal(listinter[0], droite, fin2, offsetx, decalx, espacey, esptrans, debut2, nbrtrans, verts, faces, locktrans, longtrans, decaltrans)

            elif trans and locktrans and (x == nbrlame) and (fin2 < longueurparquet) :
                if debut2 > longueurparquet: debut2 = longueurparquet
                transversal(listinter[0], droite, fin2, offsetx, decalx, espacey, esptrans, debut2, nbrtrans, verts, faces, locktrans, longtrans, decaltrans)

            #------------------------------------------------------------
            # Test si on depasse la longueur du parquet, on sort de la boucle.
            fin2 = debut2
        #------------------------------------------------------------
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
class GeneratorPanel(bpy.types.Panel):
    bl_idname = "mesh.plancher"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_category = "Floor"
    bl_label = "Floor"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        
        box = layout.box()
        
        row = box.row()
        row.operator("mesh.plancher")


#############################################################
# OPERATOR
#############################################################

class AppelPlancher(bpy.types.Operator):
    """Création d'un plancher"""
    bl_label = "Plancher"
    bl_idname = "mesh.plancher"
    bl_options = {'REGISTER', 'UNDO'}
    #------------------------------------------------------------
    # PROPRIETES
    #------------------------------------------------------------
    # Switch entre unités et 
    switch = BoolProperty(
               name="Switch",
               description="Switch entre unités ou mesures",
               default=False,            
               )  
               
    longueurparquet = FloatProperty(
               name="Length",
               description="Longueur du sol",
               min=0.01, max=100.0,
               default=4.0,
               precision=2,
               subtype='DISTANCE',
               unit='LENGTH',
              step=0.001,
               )

    # Nombre de lame
    nbrlame = IntProperty(
            name="Count",
            description="Nombre de rangées",
            min=1, max=100,
            default=2,
            )
              
    # Longueur d'une planche
    longueurlame = FloatProperty(
               name="Length",
               description="Longueur de l'objet",
               min=0.01, max=100.0,
               default=2.0,
               precision=2,
               subtype='DISTANCE',
               unit='LENGTH',
               step=0.001,
               )
               
    # Largeur
    largeur = FloatProperty(
              name="Width",
              description="Largeur de l'objet",
              min=0.01, max=100.0,
              default=0.18,
              precision=3,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.1,
              )

    # Offset Random largeur         
    randlargoffset = FloatProperty(
               name="Random",
               description="Influence du random sur la largeur",
               min=0, max=1,
               default=0,
               precision=2,
               subtype='PERCENTAGE',
               unit='NONE',
               step=0.1
               )

    # Interval entre les rangées sur les X
    espacex = FloatProperty(
              name="Gap X",
              description="Interval entre chaque rangées sur les X",
              min=0.00, max=100.0,
              default=0.01,
              precision=2,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.001,
              )
              
    # Interval entre les rangées sur les Y
    espacey = FloatProperty(
              name="Gap Y",
              description="Interval entre chaque rangées sur les Y",
              min=0.00, max=100.0,
              default=0.01,
              precision=2,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.001,              
              )

    # Remplir l'interval sur X
    trans = BoolProperty(
               name=" ",
               description="Remplir l'interval sur X",
               default=False,           
               )   

    # Utilise les paramètre d'espacement
    locktrans = BoolProperty(
               name="Unlock",
               description="Utilise les paramètres d'espacement",
               default=False,           
               )  
               
    # Longueur de la planche transversale
    longtrans = FloatProperty(
              name="Length",
              description="Longueur de la planche transversale",
              min=0.01, max=100,
              default=2,
              precision=2,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.1,
              )

    # Espace entre les planches transversales
    esptrans = FloatProperty(
              name="Gap",
              description="Espace entre les planches transversale",
              min=0.00, max=100,
              default=0.01,
              precision=2,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.001,
              )

    # Nombre de lames transversales
    nbrtrans = IntProperty(
            name="Count X",
            description="Nombre de rangées",
            min=1, max=100,
            default=1,
            )

    # Décalage des rangées
    decaltrans = FloatProperty(
               name="Shift",
               description="Décalage des rangées",
               min=0, max=1,
               default=0,
               precision=2,
               subtype='PERCENTAGE',
               unit='NONE',
               step=0.1
               )
            
    # Décalage des rangées
    offsety = FloatProperty(
               name="Shift Y",
               description="Décalage des rangées Y",
               min=0, max=1,
               default=0,
               precision=2,
               subtype='PERCENTAGE',
               unit='NONE',
               step=0.1
               )

    # Nombre de lames décalées
    nbrdecal = IntProperty(
            name="Count Y",
            description="Nombre de rangées décalées",
            min=1, max=100,
            default=1,
            )

    # Décalage des planches
    offsetx = FloatProperty(
               name="Shift X",
               description="Décalage des rangées X",
               min= math.radians(0), max= math.radians(70),
               default=0.00,
               precision=2,
               subtype='ANGLE',
               unit='ROTATION',
               step=1
               )

    # Random décalage             
    randoffsety = FloatProperty(
               name="Random",
               description="Ajoute un décalage aléatoire",
               min=0, max=1,
               default=0,
               precision=2,
               subtype='PERCENTAGE',
               unit='NONE',
               step=0.1
               )


    # Hauteur           
    hauteur = FloatProperty(
              name="Height",
              description="Hauteur du parquet",
              min=0.01, max=100,
              default=0.01,
              precision=2,
              subtype='DISTANCE',
              unit='LENGTH',
              step=0.1,
              )

    # Baton rompus
    batonrompu = BoolProperty(
               name="Bâtons rompus",
               description="Parquet batons rompus",
               default=False,            
               )  

    # UV Smart Projection
    uvsmart = BoolProperty(
               name="UV Smart Projection",
               description="UV Smart Projection",
               default=False,            
               )  

    # Nombre de vertex color
    uvcol = IntProperty(
               name="Random Color",
               description="Nombre de vertex color",
               min=0, max=100,
               default=0,
               )  

    # Nombre de vertex color
    colphase = IntProperty(
               name="Phase color",
               description="Distribution de la couleur par phase",
               min=0, max=100,
               default=0,
               )  

    # Nombre de vertex color
    colseed = IntProperty(
               name="Seed",
               description="Redistribution du hasard",
               min=0, max=999999,
               default=0,
               )  

    # Aligner sur la vue
    view_align = BoolProperty(
            name="Align to View",
            default=False,
            )
          
    # Location
    location = FloatVectorProperty(
            name="Location",
            subtype='TRANSLATION',
            )
            
    # Rotation
    rotation = FloatVectorProperty(
            name="Rotation",
            subtype='EULER',
            )


    
    #------------------------------------------------------------
    # PANEL SECONDAIRE
    #------------------------------------------------------------
    def draw(self, context):
        layout = self.layout
        obj = context.object

        col = layout.column()
 
        #------------------------------------------------------------PLANCHER
        col.label(text="Surface")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "switch",  icon='BLANK1')  
        row = col.row(align=True)
        row.prop(self, "nbrlame")
        row.prop(self, "longueurparquet")
        row = col.row(align=True)         
        row.prop(self, "hauteur")   

        col = layout.column()
        col = layout.column()      
        
        #------------------------------------------------------------SOL
        col.label(text="Board")
        col = layout.column(align=True)
        row = col.row(align=True)
        
        row.prop(self, "longueurlame")
        row.prop(self, "largeur")
        row = col.row(align = True)
        row.prop(self, "randlargoffset", text="Random", slider=True)
        row = col.row(align=True) 
        row.prop(self, "colseed")
        
        col = layout.column()
        col = layout.column()   
        
        #------------------------------------------------------------ESPACEMENT        
        col.label(text="Gap")
        col = layout.column(align=True)
        row = col.row(align=True)

        if self.batonrompu == False:
            row.prop(self, "espacex")
        row.prop(self, "espacey")
        if self.espacey > 0:

        #------------------------------------------------------------TRANSVERSAL     
            col = layout.column(align=True)
            row = col.row(align=True)
            row.label(text="Transversal:")
            row.prop(self, "trans")
            if self.trans:
                row.prop(self, "locktrans")
                col = layout.column(align=True)
                row = col.row(align=True)
                if self.locktrans: row.prop(self, "longtrans")
                if not self.locktrans: row.prop(self, "nbrdecal")
                row.prop(self, "nbrtrans")
                row = col.row(align=True)
                row.prop(self, "esptrans")
            else: 
                row = col.row(align=True)
                row.prop(self, "nbrdecal")
            row = col.row(align=True)
            row.prop(self, "offsety")
            row.prop(self, "randoffsety")
            row = col.row(align=True) 
            row.prop(self, "colseed")

        #------------------------------------------------------------CHEVRON / HERRINGBONE
            col = layout.column()
            col = layout.column()      
            col.label(text="Chevron")    
            col = layout.column(align=True)
                            
        if self.offsety == 0 and self.batonrompu == False:
            row = col.row(align=True)
            #Parquet Hongrie
            row.prop(self, "offsetx")             
                        
        if self.batonrompu == True:
            self.switch = True
        #Parquet Herringbone
        row = col.row(align=True) 
        row.prop(self, "batonrompu", text='Herringbone', icon='BLANK1')

        #------------------------------------------------------------UV / VERTEX
        col = layout.column()
        col = layout.column()      
        col.label(text="Vertex / UV")    
        col = layout.column(align=True)
        #UV Smart Projection
        row = col.row(align=True) 
        if not self.uvsmart:
            row.prop(self, "uvsmart", text='Smart Projection', icon='BLANK1')
        else:         
            row.prop(self, "uvsmart", text='UV DONE !', icon='BLANK1')
            #Vertex Color
            if self.colphase == 0:
                row = col.row(align=True)
                row.prop(self, "uvcol")
            #Phase Color
            if self.uvcol == 0:
                row = col.row(align=True) 
                row.prop(self, "colphase")
            #Seed color
            row = col.row(align=True) 
            row.prop(self, "colseed")


                        
    #-----------------------------------------------------
    # Execute
    #-----------------------------------------------------
    def execute(self, context):
        create_plancher(self,context)
        return {'FINISHED'}

#############################################################
# FONCTION PLANCHER
#############################################################
def create_plancher(self,context):
    
    bpy.context.scene.unit_settings.system = 'METRIC'

    verts_loc, faces = parquet(self.switch,
                               self.nbrlame,
                               self.largeur,
                               self.randlargoffset,
                               self.espacex,
                               self.longueurlame,
                               self.espacey,
                               self.offsety,
                               self.nbrdecal,
                               self.offsetx,
                               self.batonrompu,
                               self.randoffsety,
                               self.longueurparquet,
                               self.hauteur,
                               self.trans,
                               self.esptrans,
                               self.longtrans,
                               self.locktrans,
                               self.nbrtrans,
                               self.decaltrans,
                               self.colseed,
                              )

    # Création d'un bmesh vide
    mesh = bpy.data.meshes.new("Plancher")
    bm = bmesh.new()
    
    # Création des points
    for v_co in verts_loc:
        bm.verts.new(v_co)

    # Indexation
    bm.verts.ensure_lookup_table()
        
    # Création des faces à partir des points.
    for f_idx in faces:
        bm.faces.new([bm.verts[i] for i in f_idx])
  
    # Mise à jour du bmesh
    bm.to_mesh(mesh)
    mesh.update()

    # Ajout du mesh en tant qu'objet dans la scène
    from bpy_extras import object_utils
    object_utils.object_data_add(context, mesh, operator=self)

    obj = bpy.ops.object
    obj_act =  bpy.context.scene.objects.active
    ob = bpy.data.objects[obj_act.name]
    
    #----------------------------------------------------------------COULEUR / UV 
    if self.uvsmart:
        seed(self.colseed)
        # Ajout des UV et d'une couleur pour chaque planche
        mesh.uv_textures.new()
        vertex_colors = mesh.vertex_colors.new().data
        rgb = []

        # Générer autant de couleurs que d'uvcol
        if self.uvcol > 0: 
            for i in range(self.uvcol):
                color = [round(rand()), round(rand()), round(rand())]
                rgb.append(color)

        elif self.colphase > 0: 
            for n in range(self.colphase):
                color = [round(rand()), round(rand()), round(rand())]
                rgb.append(color)      
    #----------------------------------------------------------------VERTEX GROUP
        # Création d'un vertex group
        if self.uvcol == 0 and self.colphase == 0: 
            bpy.context.object.vertex_groups.new()
        elif self.uvcol > 0:        
            # Création de plusieurs vertex group
            for v in range(self.uvcol): 
                bpy.context.object.vertex_groups.new()
        elif self.colphase > 0: 
            # Création de plusieurs vertex group
            for v in range(self.colphase): 
                bpy.context.object.vertex_groups.new()

    #----------------------------------------------------------------LOOPS + COULEUR        
        phase = self.colphase
        for poly in mesh.polygons:

            if self.uvcol == 0 and self.colphase == 0: 
                color = [rand(), rand(), rand()]

            elif self.uvcol > 0: 
                color = rgb[randint(0,self.uvcol-1)]
                
                for loop_index in poly.loop_indices:
                    vertex_colors[loop_index].color = color
                    vg = bpy.context.object.vertex_groups[rgb.index(color)]

                    # Assigne chaque vertex/couleur a un vertex group
                    vg.add([loop_index], 1, "ADD") # index, weight, operation

            elif self.colphase > 0: 
                color = rgb[phase-1]
                phase -= 1
                if phase == 0: phase = self.colphase
                
                for loop_index in poly.loop_indices:
                    vertex_colors[loop_index].color = color
                    vg = bpy.context.object.vertex_groups[rgb.index(color)]

                    # Assigne chaque vertex/couleur a un vertex group
                    vg.add([loop_index], 1, "ADD") # index, weight, operation

        # Ajoute les Uv aux nouvelles faces
        uv_layer = bm.loops.layers.uv.verify()
        bm.faces.layers.tex.verify()

        # Parcours les Vertex Group et génère les UV.
        bpy.ops.object.editmode_toggle() 
        bpy.ops.mesh.select_all() #Selectionne toutes les faces
        bpy.ops.uv.unwrap(method='ANGLE_BASED', correct_aspect=True)
        bpy.ops.object.vertex_group_deselect()
        obj = context.active_object

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        uv_lay = bm.loops.layers.uv.active

        h = 0        
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

            v = 0

            tpuvx.clear() 
            tpuvy.clear()
            
        bpy.ops.object.editmode_toggle() 
        #-----------    

    # Récupération du contexte de l'objet
    co = context.object
    mods = co.modifiers

    # Ajout du modifier SOLIDIFY
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.ops.object.modifier_add(type='BEVEL')
    mods[0].show_expanded = False
    mods[0].thickness = self.hauteur
    mods[1].width = 0.001
    bm.free()
    

    return


def register():
    bpy.utils.register_class(GeneratorPanel)
    bpy.utils.register_class(AppelPlancher)
    
def unregister():
    bpy.utils.unregister_class(GeneratorPanel)
    bpy.utils.unregister_class(AppelPlancher)
            
if __name__ == "__main__":
    register()

